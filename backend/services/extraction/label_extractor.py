"""Upgraded label extraction and normalization service for Phase 4."""

import re
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


def normalize_ocr_text(text: str) -> str:
    """Normalize common OCR formatting artifacts without altering uncertain text."""
    if not text:
        return ""
    text = re.sub(r'\b(\d+)\s*(kg|g|gm|gms|mg|ml|l|ltr|pcs)\b', r'\1 \2', text, flags=re.IGNORECASE)
    text = re.sub(r'(mrp|rs\.?|₹|inr)\s*([₹\d])', r'\1 \2', text, flags=re.IGNORECASE)
    text = re.sub(r'([₹\d])\s*(/-)', r'\1 \2', text, flags=re.IGNORECASE)
    text = re.sub(r'\bnet\s*qty\s*[:\-]?\s*', 'Net Qty: ', text, flags=re.IGNORECASE)
    text = re.sub(r'\bmrp\s*[:\-]?\s*', 'MRP: ', text, flags=re.IGNORECASE)
    text = re.sub(r'\bmfg\s*(?:date|by)?\s*[:\-]?\s*', 'Mfg: ', text, flags=re.IGNORECASE)
    text = re.sub(r'\bpkd?\s*(?:date|by)?\s*[:\-]?\s*', 'Pkd: ', text, flags=re.IGNORECASE)
    return text.strip()


def extract_field_detail(raw_text: str, value: Optional[str], confidence: float = 90.0, status: str = "CONFIDENT", candidates: Optional[List[Any]] = None) -> Dict[str, Any]:
    """Build detailed field representation with confidence and status."""
    return {
        "value": value,
        "raw_text": raw_text,
        "confidence": confidence,
        "source": "OCR_TEXT",
        "status": status if value else "MISSING",
        "candidates": candidates or ([value] if value else []),
    }


def extract_label_fields(raw_text: str, client_fields: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Extract structured label fields with normalization, confidence, and ambiguity handling."""
    client_fields = client_fields or {}
    normalized_raw = normalize_ocr_text(raw_text)

    extracted = {
        "product_name": client_fields.get("product_name"),
        "manufacturer": client_fields.get("manufacturer"),
        "net_quantity": client_fields.get("net_quantity"),
        "mrp": client_fields.get("mrp"),
        "date": client_fields.get("date"),
        "consumer_care": client_fields.get("consumer_care"),
        "field_details": {},
    }

    if not normalized_raw and not client_fields:
        return extracted

    lines = [line.strip() for line in normalized_raw.splitlines() if line.strip()]

    mrp_candidates = []
    qty_candidates = []

    for i, line in enumerate(lines):
        line_lower = line.lower()

        if not extracted["product_name"] and i == 0 and len(line) > 3:
            if not any(kw in line_lower for kw in ["mrp", "net", "mfg", "pkd", "consumer", "manufacturer"]):
                extracted["product_name"] = line

        if not extracted["manufacturer"]:
            if any(kw in line_lower for kw in ["mfg", "mfg by", "manufactured by", "manufacturer", "mfd by", "packer", "importer"]):
                parts = [line]
                if i + 1 < len(lines) and not any(kw in lines[i+1].lower() for kw in ["mrp", "net", "qty", "date", "consumer"]):
                    parts.append(lines[i+1])
                extracted["manufacturer"] = ", ".join(parts)

        if any(kw in line_lower for kw in ["net qty", "net quantity", "net weight", "net wt", "contents"]) or re.search(r'\b\d+\s*(?:g|kg|ml|l)\b', line_lower):
            qty_candidates.append(line)

        if any(kw in line_lower for kw in ["mrp", "max. retail price", "retail price", "price"]) or re.search(r'(?:₹|rs\.?|inr)', line_lower):
            mrp_candidates.append(line)

        if not extracted["date"]:
            if any(kw in line_lower for kw in ["pkd", "packed", "batch", "date", "mfg date", "pkd date"]) and not any(ex in line_lower for ex in ["mfg by", "manufactured by", "mfd by"]):
                extracted["date"] = line
            else:
                match = re.search(r'\b(?:0[1-9]|1[0-2])\s*[/.-]\s*(?:20\d{2})\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*(?:20\d{2})\b', line, re.IGNORECASE)
                if match:
                    extracted["date"] = match.group(0)

        if not extracted["consumer_care"]:
            if any(kw in line_lower for kw in ["consumer care", "customer care", "helpline", "complaints", "email"]):
                extracted["consumer_care"] = line
            else:
                if "@" in line or re.search(r'\b(?:\+91[\-\s]?)?[0]?[6-9]\d{9}\b|\b1800[\-\s]?\d{3}[\-\s]?\d{4}\b', line):
                    extracted["consumer_care"] = line

    if not extracted["net_quantity"] and qty_candidates:
        if "?" in qty_candidates[0]:
            extracted["net_quantity"] = None
        else:
            extracted["net_quantity"] = qty_candidates[0]

    if not extracted["mrp"] and mrp_candidates:
        extracted["mrp"] = mrp_candidates[0]

    extracted["field_details"] = {
        "product_name": extract_field_detail(extracted["product_name"] or "", extracted["product_name"], status="CONFIDENT" if extracted["product_name"] else "MISSING"),
        "manufacturer": extract_field_detail(extracted["manufacturer"] or "", extracted["manufacturer"], status="CONFIDENT" if extracted["manufacturer"] else "MISSING"),
        "net_quantity": extract_field_detail(extracted["net_quantity"] or "", extracted["net_quantity"], status="AMBIGUOUS" if len(qty_candidates) > 1 else ("CONFIDENT" if extracted["net_quantity"] else "MISSING"), candidates=qty_candidates),
        "mrp": extract_field_detail(extracted["mrp"] or "", extracted["mrp"], status="AMBIGUOUS" if len(mrp_candidates) > 1 else ("CONFIDENT" if extracted["mrp"] else "MISSING"), candidates=mrp_candidates),
        "date": extract_field_detail(extracted["date"] or "", extracted["date"], status="CONFIDENT" if extracted["date"] else "MISSING"),
        "consumer_care": extract_field_detail(extracted["consumer_care"] or "", extracted["consumer_care"], status="CONFIDENT" if extracted["consumer_care"] else "MISSING"),
    }

    return extracted


def combine_label_extractions(extractions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Combine extracted fields from multiple images belonging to the same inspection.

    Handles merging and conflict detection (e.g., conflicting MRPs become AMBIGUOUS).
    """
    if not extractions:
        return {
            "product_name": None,
            "manufacturer": None,
            "net_quantity": None,
            "mrp": None,
            "date": None,
            "consumer_care": None,
            "field_details": {},
        }

    if len(extractions) == 1:
        return extractions[0]

    combined = {
        "product_name": None,
        "manufacturer": None,
        "net_quantity": None,
        "mrp": None,
        "date": None,
        "consumer_care": None,
        "field_details": {},
    }

    fields_to_check = ["product_name", "manufacturer", "net_quantity", "mrp", "date", "consumer_care"]

    for field in fields_to_check:
        values = []
        confidences = []
        for ext in extractions:
            val = ext.get(field)
            if val:
                values.append(val)
                details = ext.get("field_details", {}).get(field, {})
                confidences.append(details.get("confidence", 90.0))

        if not values:
            combined[field] = None
            combined["field_details"][field] = {
                "value": None,
                "raw_text": "",
                "confidence": 0.0,
                "source": "OCR_TEXT",
                "status": "MISSING",
                "candidates": [],
            }
        elif len(set(values)) == 1:
            combined[field] = values[0]
            avg_conf = sum(confidences) / len(confidences) if confidences else 90.0
            combined["field_details"][field] = {
                "value": values[0],
                "raw_text": values[0],
                "confidence": avg_conf,
                "source": "OCR_TEXT",
                "status": "CONFIDENT",
                "candidates": values,
            }
        else:
            # Conflict detected across images -> set value to None and status to AMBIGUOUS
            combined[field] = None
            combined["field_details"][field] = {
                "value": None,
                "raw_text": " | ".join(values),
                "confidence": 50.0,
                "source": "OCR_TEXT",
                "status": "AMBIGUOUS",
                "candidates": values,
            }

    return combined
