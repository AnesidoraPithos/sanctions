"""
Search Routes

Endpoints for entity background searches (base/network/deep tiers).
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
import uuid
from datetime import datetime
import logging
import os
import sys

# Add backend to path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import backend modules
from models.requests import SearchRequest
from models.responses import SearchResponse
from services.sanctions_service import get_sanctions_service
from services.research_service import get_research_service
from db_operations.db import save_search_results

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/base", response_model=SearchResponse)
async def search_base_tier(request: SearchRequest):
    """
    Perform base tier entity background search

    Base tier includes:
    - Sanctions screening (USA Trade API + local databases)
    - OSINT media intelligence (official + general sources)
    - Risk scoring
    - LLM-generated intelligence report

    Expected duration: 30-60 seconds

    Args:
        request: SearchRequest with entity_name, country, fuzzy_threshold

    Returns:
        SearchResponse with search_id, risk_level, hit counts, and intelligence report
    """
    # Generate unique search ID
    search_id = str(uuid.uuid4())
    timestamp = datetime.utcnow()

    logger.info(f"Starting base tier search: {search_id} for entity: {request.entity_name}")

    try:
        # Step 1: Sanctions Screening
        logger.info(f"[{search_id}] Step 1: Sanctions screening...")
        sanctions_service = get_sanctions_service()
        sanctions_hits = sanctions_service.search_sanctions(
            entity_name=request.entity_name,
            country=request.country,
            fuzzy_threshold=request.fuzzy_threshold
        )

        # Calculate risk level
        risk_level = sanctions_service.calculate_risk_level(sanctions_hits)

        logger.info(
            f"[{search_id}] Sanctions screening complete: "
            f"{len(sanctions_hits)} hits, risk level: {risk_level}"
        )

        # Step 2: Media Intelligence (OSINT)
        logger.info(f"[{search_id}] Step 2: OSINT media intelligence...")
        research_service = get_research_service()
        media_intelligence = research_service.get_media_intelligence(request.entity_name)

        logger.info(
            f"[{search_id}] Media intelligence complete: "
            f"{media_intelligence['total_hits']} hits found"
        )

        # Step 3: Generate Intelligence Report
        logger.info(f"[{search_id}] Step 3: Generating LLM intelligence report...")
        intelligence_report = research_service.generate_intelligence_report(
            request.entity_name
        )

        logger.info(f"[{search_id}] Intelligence report generated")

        # Step 4: Format data for response
        sanctions_data = sanctions_service.format_sanctions_data(sanctions_hits)
        media_data = research_service.format_media_data(media_intelligence)

        # Step 5: Save to database
        logger.info(f"[{search_id}] Saving results to database...")
        metadata = {
            "entity_name": request.entity_name,
            "country": request.country,
            "fuzzy_threshold": request.fuzzy_threshold,
            "tier": "base",
            "search_duration_estimate": "30-60s"
        }

        save_success = save_search_results(
            search_id=search_id,
            entity_name=request.entity_name,
            tier="base",
            risk_level=risk_level,
            sanctions_data=sanctions_data,
            research_data={
                "media_intelligence": media_intelligence,
                "media_data": media_data
            },
            intelligence_report=intelligence_report,
            metadata=metadata
        )

        if not save_success:
            logger.warning(f"[{search_id}] Failed to save to database, but continuing...")

        logger.info(f"[{search_id}] Base tier search complete")

        # Return response
        return SearchResponse(
            search_id=search_id,
            status="completed",
            tier="base",
            entity_name=request.entity_name,
            risk_level=risk_level,
            sanctions_hits=len(sanctions_hits),
            media_hits=media_intelligence['total_hits'],
            intelligence_report=intelligence_report,
            timestamp=timestamp,
            # Include full data in response (for immediate display)
            sanctions_data=sanctions_data[:10],  # Limit to first 10 for response size
            media_data=media_data[:10],          # Limit to first 10 for response size
            metadata=metadata
        )

    except Exception as e:
        logger.error(f"[{search_id}] Search failed: {str(e)}", exc_info=True)

        # Save failed search to database
        try:
            save_search_results(
                search_id=search_id,
                entity_name=request.entity_name,
                tier="base",
                risk_level="UNKNOWN",
                sanctions_data=[],
                research_data={"error": str(e)},
                intelligence_report=f"Search failed: {str(e)}",
                metadata={"status": "failed", "error": str(e)}
            )
        except:
            pass  # Don't fail on save error

        raise HTTPException(
            status_code=500,
            detail={
                "error": "SearchError",
                "message": f"Failed to complete base tier search: {str(e)}",
                "search_id": search_id
            }
        )


@router.post("/network")
async def search_network_tier(request: SearchRequest):
    """
    Perform network tier entity background search (Phase 2)

    Network tier includes:
    - Base tier (sanctions + OSINT + report)
    - Conglomerate search (SEC EDGAR + OpenCorporates + Wikipedia)
    - Director/shareholder extraction
    - Cross-entity sanctions screening
    - Network graph generation

    Expected duration: 2-5 minutes

    Returns:
        Feature not yet implemented (Phase 2)
    """
    raise HTTPException(
        status_code=501,
        detail={
            "error": "NotImplemented",
            "message": "Network tier is not yet implemented (Phase 2 feature)"
        }
    )


@router.post("/deep")
async def search_deep_tier(request: SearchRequest):
    """
    Perform deep tier entity background search (Phase 3)

    Deep tier includes:
    - Network tier (all network features)
    - Financial flow analysis
    - Trade data analysis
    - Criminal record checks
    - Advanced risk scoring

    Expected duration: 5-15 minutes

    Returns:
        Feature not yet implemented (Phase 3)
    """
    raise HTTPException(
        status_code=501,
        detail={
            "error": "NotImplemented",
            "message": "Deep tier is not yet implemented (Phase 3 feature)"
        }
    )
