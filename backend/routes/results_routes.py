"""
Results Routes

Endpoints for retrieving saved search results and search history.
"""

from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel
from typing import Optional
import logging

# Import backend modules
from models.responses import ResultsResponse, HistoryResponse, HistoryEntry, SaveResponse
from db_operations.db import get_search_results, get_search_history, toggle_save_result, get_saved_searches, set_manual_risk

VALID_MANUAL_RISK = {"LOW", "MODERATE", "HIGH", "CRITICAL"}


class SaveRequest(BaseModel):
    label: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[str] = None


class ManualRiskRequest(BaseModel):
    manual_risk: Optional[str] = None

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{search_id}", response_model=ResultsResponse)
async def get_results(
    search_id: str = Path(..., description="Search ID (UUID)")
):
    """
    Retrieve search results by ID

    Returns full search results including:
    - Sanctions data
    - Media intelligence
    - Intelligence report
    - Risk level and metadata

    Args:
        search_id: Unique search identifier (UUID)

    Returns:
        ResultsResponse with full search data

    Raises:
        404: If search_id not found
        500: If database error occurs
    """
    logger.info(f"Retrieving results for search_id: {search_id}")

    try:
        results = get_search_results(search_id)

        if not results:
            logger.warning(f"Search not found: {search_id}")
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "NotFound",
                    "message": f"Search with ID {search_id} not found"
                }
            )

        logger.info(f"Successfully retrieved results for: {search_id}")

        # Extract risk_explanation from metadata
        metadata = results.get('metadata', {})
        risk_explanation = metadata.get('risk_explanation')

        return ResultsResponse(
            search_id=results['search_id'],
            entity_name=results['entity_name'],
            tier=results['tier'],
            risk_level=results['risk_level'],
            risk_explanation=risk_explanation,  # Include risk explanation
            sanctions_hits=results['sanctions_hits'],
            sanctions_data=results['sanctions_data'],
            research_data=results['research_data'],
            intelligence_report=results.get('intelligence_report'),
            timestamp=results['timestamp'],
            metadata=metadata,
            # Network tier fields (Phase 2)
            network_data=results.get('network_data'),
            financial_intelligence=results.get('financial_intelligence'),
            subsidiaries=results.get('subsidiaries', []),
            warnings=results.get('warnings', []),
            data_sources_used=results.get('data_sources_used', []),
            # Deep tier fields (Phase 3)
            financial_flows=results.get('financial_flows', []),
            # Phase 4 fields
            director_pivots=results.get('director_pivots', []) or None,
            infrastructure=results.get('infrastructure', []) or None,
            beneficial_owners=results.get('beneficial_owners', []) or None,
            advanced_osint=results.get('advanced_osint') or None,
            # Bookmark fields
            is_saved=results.get('is_saved', False),
            save_label=results.get('save_label'),
            save_notes=results.get('save_notes'),
            save_tags=results.get('save_tags'),
            manual_risk=results.get('manual_risk'),
        )

    except HTTPException:
        # Re-raise HTTPExceptions (404 from above)
        raise
    except Exception as e:
        logger.error(f"Error retrieving results for {search_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "DatabaseError",
                "message": "Failed to retrieve search results"
            }
        )


@router.get("/")
async def get_history(
    limit: int = 50,
    saved: bool = False,
):
    """
    Get search history (or saved searches when ?saved=true).

    Args:
        limit: Maximum number of entries to return (default: 50, max: 100)
        saved: If true, return only bookmarked entries

    Returns:
        HistoryResponse with list of search entries
    """
    if limit > 100:
        limit = 100

    logger.info(f"Retrieving {'saved' if saved else 'all'} search history (limit: {limit})")

    try:
        history = get_saved_searches(limit=limit) if saved else get_search_history(limit=limit)

        entries = [
            HistoryEntry(
                search_id=entry['search_id'],
                entity_name=entry['entity_name'],
                tier=entry['tier'],
                risk_level=entry['risk_level'],
                sanctions_hits=entry['sanctions_hits'],
                timestamp=entry['timestamp'],
                is_saved=entry.get('is_saved', False),
                save_label=entry.get('save_label'),
                saved_at=entry.get('saved_at'),
                save_notes=entry.get('save_notes'),
                save_tags=entry.get('save_tags'),
            )
            for entry in history
        ]

        logger.info(f"Retrieved {len(entries)} history entries")

        return HistoryResponse(entries=entries, total=len(entries))

    except Exception as e:
        logger.error(f"Error retrieving search history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "DatabaseError", "message": "Failed to retrieve search history"}
        )


@router.post("/{search_id}/save", response_model=SaveResponse)
async def save_result(
    search_id: str = Path(..., description="Search ID (UUID)"),
    body: SaveRequest = SaveRequest(),
):
    """Bookmark a search result."""
    result = get_search_results(search_id)
    if not result:
        raise HTTPException(status_code=404, detail={"error": "NotFound", "message": f"Search {search_id} not found"})

    success = toggle_save_result(search_id, True, body.label, body.notes, body.tags)
    if not success:
        raise HTTPException(status_code=500, detail={"error": "DatabaseError", "message": "Failed to save result"})

    return SaveResponse(saved=True, search_id=search_id, label=body.label, notes=body.notes, tags=body.tags)


@router.delete("/{search_id}/save", response_model=SaveResponse)
async def unsave_result(
    search_id: str = Path(..., description="Search ID (UUID)"),
):
    """Remove a bookmark from a search result."""
    result = get_search_results(search_id)
    if not result:
        raise HTTPException(status_code=404, detail={"error": "NotFound", "message": f"Search {search_id} not found"})

    toggle_save_result(search_id, False)
    return SaveResponse(saved=False, search_id=search_id)


@router.patch("/{search_id}/manual-risk")
async def update_manual_risk(
    search_id: str = Path(..., description="Search ID (UUID)"),
    body: ManualRiskRequest = ManualRiskRequest(),
):
    """Set or clear the staff's manual risk determination for a search result."""
    value = body.manual_risk.upper() if body.manual_risk else None
    if value and value not in VALID_MANUAL_RISK:
        raise HTTPException(
            status_code=422,
            detail={"error": "InvalidValue", "message": f"manual_risk must be one of {VALID_MANUAL_RISK} or null"}
        )

    found = set_manual_risk(search_id, value)
    if not found:
        raise HTTPException(status_code=404, detail={"error": "NotFound", "message": f"Search {search_id} not found"})

    return {"search_id": search_id, "manual_risk": value}
