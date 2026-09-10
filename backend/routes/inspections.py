"""Inspections and Scan API routes."""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.database.client import get_db_session
from backend.models.entities import Product, Inspection, InspectionImage, ExtractedData
from backend.models.enums import InspectionStatus
from backend.services.storage import upload_inspection_image, delete_inspection_image, get_signed_url
from backend.services.ocr import get_ocr_service, OCRResult, OCRBlock
from backend.services.extraction import extract_label_fields, combine_label_extractions
from backend.services.preprocessing import preprocess_image
from backend.schemas.common import ApiResponse
from backend.schemas.inspection import InspectionDetailResponse
from backend.rules import evaluate_inspection, ComplianceEvaluationSummary
from backend.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inspections", tags=["Inspections"])


@router.post(
    "/scan",
    response_model=ApiResponse[InspectionDetailResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit product-label scan with one or multiple images for OCR extraction and review",
    description="Accepts one or multiple product-label images and optional OCR text/hints, stores images in Supabase Storage, creates InspectionImage records, processes OCR and combines/resolves extractions, creates product and inspection records with status REVIEW, and returns structured inspection data.",
)
async def scan_label(
    image: Optional[UploadFile] = File(None, description="Single product label image file"),
    images: List[UploadFile] = File(default=[], description="Multiple product label image files"),
    ocr_text: Optional[str] = Form(None, description="Optional client-provided raw OCR text (Scenario A)"),
    product_name: Optional[str] = Form(None, description="Optional product name hint"),
    manufacturer: Optional[str] = Form(None, description="Optional manufacturer hint"),
    net_quantity: Optional[str] = Form(None, description="Optional net quantity hint"),
    mrp: Optional[str] = Form(None, description="Optional MRP hint"),
    db: Session = Depends(get_db_session),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[InspectionDetailResponse]:
    """Process single or multi-image label scan request."""
    image_list: List[UploadFile] = []
    if image and image.filename:
        image_list.append(image)
    if images:
        for img in images:
            if img and img.filename:
                image_list.append(img)

    if not image_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No image files provided or filenames are missing.",
        )

    uploaded_storage_paths = []
    extractions_list = []
    avg_confidences = []

    try:
        for idx, img in enumerate(image_list):
            try:
                img_bytes = await img.read()
                if not img_bytes:
                    continue
            except Exception as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to read image '{img.filename}': {str(exc)}",
                )

            try:
                storage_info = upload_inspection_image(
                    file_bytes=img_bytes,
                    original_filename=img.filename,
                )
                storage_path = storage_info["storage_path"]
                uploaded_storage_paths.append(storage_path)
            except Exception as se:
                logger.error(f"Storage upload error for '{img.filename}': {se}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Image storage failed for '{img.filename}': {str(se)}",
                )

            if ocr_text and ocr_text.strip() and idx == 0:
                ocr_result = OCRResult(
                    raw_text=ocr_text.strip(),
                    confidence=100.0,
                    blocks=[OCRBlock(text=ocr_text.strip(), confidence=100.0)],
                    provider="client-supplied",
                    model="external",
                )
            else:
                try:
                    processed_bytes = preprocess_image(img_bytes)
                    ocr_svc = get_ocr_service()
                    ocr_result = ocr_svc.extract_text(processed_bytes)
                except Exception as oe:
                    logger.error(f"OCR processing error for '{img.filename}': {oe}")
                    ocr_result = OCRResult(
                        raw_text="",
                        confidence=0.0,
                        blocks=[],
                        provider="paddleocr",
                        model="failed",
                    )

            client_hints = {
                "product_name": product_name,
                "manufacturer": manufacturer,
                "net_quantity": net_quantity,
                "mrp": mrp,
            }
            extracted_fields = extract_label_fields(ocr_result.raw_text, client_hints)
            extractions_list.append(extracted_fields)
            avg_confidences.append(ocr_result.confidence)

        combined_extraction = combine_label_extractions(extractions_list)
        overall_confidence = float(sum(avg_confidences) / len(avg_confidences)) if avg_confidences else 0.0

        try:
            product = Product(
                product_name=combined_extraction.get("product_name"),
                manufacturer=combined_extraction.get("manufacturer"),
            )
            db.add(product)
            db.flush()

            primary_image_path = uploaded_storage_paths[0] if uploaded_storage_paths else ""
            inspection = Inspection(
                product_id=product.id,
                user_id=current_user["user_id"],
                image_url=primary_image_path,
                status=InspectionStatus.REVIEW.value,
            )
            db.add(inspection)
            db.flush()

            for seq, path in enumerate(uploaded_storage_paths):
                insp_image = InspectionImage(
                    inspection_id=inspection.id,
                    image_url=path,
                    sequence=seq,
                )
                db.add(insp_image)

            extracted_data = ExtractedData(
                inspection_id=inspection.id,
                product_name=combined_extraction.get("product_name"),
                manufacturer=combined_extraction.get("manufacturer"),
                net_quantity=combined_extraction.get("net_quantity"),
                mrp=combined_extraction.get("mrp"),
                date=combined_extraction.get("date"),
                consumer_care=combined_extraction.get("consumer_care"),
                extraction_confidence=overall_confidence,
            )
            db.add(extracted_data)
            db.commit()
            db.refresh(inspection)

        except Exception as dbe:
            db.rollback()
            logger.error(f"Database persistence failed: {dbe}")
            for path in uploaded_storage_paths:
                try:
                    delete_inspection_image(path)
                except Exception:
                    pass
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database transaction failed: {str(dbe)}",
            )

        resp_image_url = primary_image_path
        try:
            resp_image_url = get_signed_url(primary_image_path)
        except Exception:
            pass

        inspection_detail = InspectionDetailResponse.model_validate(inspection)
        inspection_detail.image_url = resp_image_url

        return ApiResponse(
            success=True,
            message=f"Scan processed successfully with {len(uploaded_storage_paths)} image(s) and inspection set to REVIEW",
            data=inspection_detail,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected scan processing error: {exc}")
        for path in uploaded_storage_paths:
            try:
                delete_inspection_image(path)
            except Exception:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected internal error: {str(exc)}",
        )


@router.post(
    "/{inspection_id}/evaluate",
    response_model=ApiResponse[ComplianceEvaluationSummary],
    summary="Evaluate Legal Metrology compliance rules for an inspection",
    description="Runs the deterministic compliance engine (Rules 6, 10, 11, 12, 13, 14, 16, 17, 24, 26) against extracted inspection data, persists findings as violations, updates inspection status, and returns the evaluation summary.",
)
async def evaluate_inspection_endpoint(
    inspection_id: str,
    db: Session = Depends(get_db_session),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[ComplianceEvaluationSummary]:
    """Execute compliance evaluation on an inspection with ownership verification."""
    try:
        inspection = db.query(Inspection).filter_by(id=inspection_id).first()
        if not inspection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inspection with id '{inspection_id}' not found.",
            )
        if inspection.user_id and inspection.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: you do not own this inspection.",
            )

        summary = evaluate_inspection(db, inspection_id)
        return ApiResponse(
            success=True,
            message="Compliance evaluation completed successfully",
            data=summary,
        )
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve),
        )
    except Exception as exc:
        logger.error(f"Compliance evaluation error for inspection {inspection_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Compliance evaluation failed: {str(exc)}",
        )
