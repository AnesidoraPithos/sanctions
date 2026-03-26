"""
Results Routes

Endpoints for retrieving saved search results and search history.
"""

from fastapi import APIRouter, HTTPException, Path
from typing import Optional
import logging
import os
import sys

# Add backend to path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import backend modules
from models.responses import ResultsResponse, HistoryResponse, HistoryEntry
from db_operations.db import get_search_results, get_search_history

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
    limit: int = 50
):
    """
    Get search history

    Returns list of recent searches with basic information.
    Use GET /results/{search_id} to retrieve full details for a specific search.

    Args:
        limit: Maximum number of entries to return (default: 50, max: 100)

    Returns:
        HistoryResponse with list of search entries
    """
    # Enforce maximum limit
    if limit > 100:
        limit = 100

    logger.info(f"Retrieving search history (limit: {limit})")

    try:
        history = get_search_history(limit=limit)

        entries = [
            HistoryEntry(
                search_id=entry['search_id'],
                entity_name=entry['entity_name'],
                tier=entry['tier'],
                risk_level=entry['risk_level'],
                sanctions_hits=entry['sanctions_hits'],
                timestamp=entry['timestamp']
            )
            for entry in history
        ]

        logger.info(f"Retrieved {len(entries)} history entries")

        return HistoryResponse(
            entries=entries,
            total=len(entries)
        )

    except Exception as e:
        logger.error(f"Error retrieving search history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "DatabaseError",
                "message": "Failed to retrieve search history"
            }
        )
