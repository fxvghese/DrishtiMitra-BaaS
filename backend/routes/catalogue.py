"""Reference Product Catalogue API routes."""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database.client import get_db_session
from backend.services.catalogue import search_reference_catalogue
from backend.schemas.common import ApiResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/catalogue", tags=["Reference Catalogue"])


@router.get(
    "/search",
    response_model=ApiResponse[List[Dict[str, Any]]],
    summary="Search reference product catalogue",
    description="Search reference products by query string (product name, brand, or category).",
)
async def search_catalogue(
    q: str = Query(..., description="Search query string"),
    limit: int = Query(5, description="Max results limit"),
    db: Session = Depends(get_db_session),
) -> ApiResponse[List[Dict[str, Any]]]:
    """Search reference catalogue."""
    matches = search_reference_catalogue(db, q, limit)
    return ApiResponse(
        success=True,
        message=f"Found {len(matches)} reference product matches",
        data=matches,
    )
