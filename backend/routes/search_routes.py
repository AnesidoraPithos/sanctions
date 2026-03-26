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
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add backend to path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import backend modules
from models.requests import SearchRequest
from models.responses import SearchResponse
from services.sanctions_service import get_sanctions_service
from services.research_service import get_research_service
from services.conglomerate_service import get_conglomerate_service
from services.network_service import get_network_service
from services.risk_assessment_service import get_risk_assessment_service
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

        logger.info(
            f"[{search_id}] Sanctions screening complete: {len(sanctions_hits)} hits"
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

        # Step 4: Extract AI risk assessment and calculate combined risk
        logger.info(f"[{search_id}] Step 4: Calculating combined risk level...")
        risk_service = get_risk_assessment_service()
        ai_assessment = risk_service.extract_ai_risk_assessment(intelligence_report)
        risk_level, risk_explanation = risk_service.calculate_combined_risk_level(
            sanctions_hits=sanctions_hits,
            ai_assessment=ai_assessment,
            media_intelligence=media_intelligence
        )

        logger.info(
            f"[{search_id}] Risk calculation complete: {risk_level} "
            f"(Sanctions: {len(sanctions_hits)}, AI: {ai_assessment.get('level', 'N/A')})"
        )

        # Step 5: Format data for response
        sanctions_data = sanctions_service.format_sanctions_data(sanctions_hits)
        media_data = research_service.format_media_data(media_intelligence)

        # Step 6: Save to database
        logger.info(f"[{search_id}] Saving results to database...")
        metadata = {
            "entity_name": request.entity_name,
            "country": request.country,
            "fuzzy_threshold": request.fuzzy_threshold,
            "tier": "base",
            "search_duration_estimate": "30-60s",
            "risk_explanation": risk_explanation  # Include risk explanation in metadata
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
            risk_explanation=risk_explanation,  # Include in response
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


@router.post("/network", response_model=SearchResponse)
async def search_network_tier(request: SearchRequest):
    """
    Perform network tier entity background search (Phase 2)

    Network tier includes:
    - Base tier (sanctions + OSINT + report)
    - Conglomerate search (SEC EDGAR + OpenCorporates + Wikipedia)
    - Director/shareholder extraction
    - Cross-entity sanctions screening
    - Network graph generation

    Expected duration: 2-10 minutes (varies by depth)

    Args:
        request: SearchRequest with entity_name, network_depth, ownership_threshold

    Returns:
        SearchResponse with network_data, financial_intelligence, subsidiaries
    """
    # Generate unique search ID
    search_id = str(uuid.uuid4())
    timestamp = datetime.utcnow()
    search_start_time = time.time()

    logger.info(
        f"Starting network tier search: {search_id} for entity: {request.entity_name} "
        f"(depth={request.network_depth}, ownership_threshold={request.ownership_threshold}%)"
    )

    try:
        # STEP 1: Run base tier research (sanctions + media intelligence)
        logger.info(f"[{search_id}] Step 1: Base tier research...")
        sanctions_service = get_sanctions_service()
        research_service = get_research_service()

        # Sanctions screening
        sanctions_hits = sanctions_service.search_sanctions(
            entity_name=request.entity_name,
            country=request.country,
            fuzzy_threshold=request.fuzzy_threshold
        )

        # Media intelligence
        media_intelligence = research_service.get_media_intelligence(request.entity_name)

        logger.info(
            f"[{search_id}] Base tier complete: "
            f"{len(sanctions_hits)} sanctions hits, {media_intelligence['total_hits']} media hits"
        )

        # STEP 2: Conglomerate discovery
        logger.info(f"[{search_id}] Step 2: Conglomerate discovery...")
        conglomerate_service = get_conglomerate_service()

        conglomerate_data = conglomerate_service.discover_subsidiaries(
            parent_company=request.entity_name,
            depth=request.network_depth,
            ownership_threshold=request.ownership_threshold,
            include_sisters=request.include_sisters,
            max_level_2_searches=request.max_level_2_searches,
            max_level_3_searches=request.max_level_3_searches
        )

        subsidiaries = conglomerate_data.get('subsidiaries', [])
        sisters = conglomerate_data.get('sisters', [])
        parent_info = conglomerate_data.get('parent', None)
        warnings = conglomerate_data.get('warnings', [])
        data_sources_used = conglomerate_data.get('data_sources_used', [])

        logger.info(
            f"[{search_id}] Conglomerate discovery complete: "
            f"{len(subsidiaries)} subsidiaries, {len(sisters)} sisters found "
            f"(method: {conglomerate_data.get('method', 'unknown')})"
        )

        # STEP 3: Extract financial intelligence
        logger.info(f"[{search_id}] Step 3: Extracting financial intelligence...")

        # Try to get CIK for more accurate results
        cik = conglomerate_service.search_sec_edgar_for_cik(request.entity_name)

        financial_intelligence = conglomerate_service.extract_financial_intelligence(
            company_name=request.entity_name,
            cik=cik
        )

        directors = financial_intelligence.get('directors', [])
        shareholders = financial_intelligence.get('shareholders', [])
        transactions = financial_intelligence.get('transactions', [])
        warnings.extend(financial_intelligence.get('warnings', []))

        logger.info(
            f"[{search_id}] Financial intelligence extracted: "
            f"{len(directors)} directors, {len(shareholders)} shareholders, "
            f"{len(transactions)} transactions"
        )

        # Calculate level statistics for subsidiaries
        level_stats = {
            "level_1": len([s for s in subsidiaries if s.get('level') == 1]),
            "level_2": len([s for s in subsidiaries if s.get('level') == 2]),
            "level_3": len([s for s in subsidiaries if s.get('level') == 3]),
        }

        logger.info(
            f"[{search_id}] Subsidiary level breakdown: "
            f"L1={level_stats['level_1']}, L2={level_stats['level_2']}, L3={level_stats['level_3']}"
        )

        # STEP 4: Cross-entity sanctions screening
        logger.info(f"[{search_id}] Step 4: Cross-entity sanctions screening...")

        # Define wrapper functions for parallel screening
        def screen_subsidiary(subsidiary):
            """Wrapper for parallel subsidiary sanctions screening"""
            try:
                sub_hits = sanctions_service.search_sanctions(
                    entity_name=subsidiary['name'],
                    country=None,
                    fuzzy_threshold=request.fuzzy_threshold
                )
                subsidiary['sanctions_hits'] = len(sub_hits)
                subsidiary['sanctions_data'] = sub_hits[:5]
                return (subsidiary, len(sub_hits), None)
            except Exception as e:
                logger.error(f"Error screening subsidiary {subsidiary['name']}: {str(e)}")
                subsidiary['sanctions_hits'] = 0
                subsidiary['sanctions_data'] = []
                return (subsidiary, 0, str(e))

        def screen_person(person):
            """Wrapper for parallel person sanctions screening"""
            try:
                person_hits = sanctions_service.search_sanctions(
                    entity_name=person['name'],
                    country=None,
                    fuzzy_threshold=request.fuzzy_threshold
                )
                person['sanctions_hits'] = len(person_hits)
                person['sanctions_data'] = person_hits[:5]
                return (person, len(person_hits), None)
            except Exception as e:
                logger.error(f"Error screening person {person['name']}: {str(e)}")
                person['sanctions_hits'] = 0
                person['sanctions_data'] = []
                return (person, 0, str(e))

        # Screen subsidiaries in parallel
        subsidiary_sanctions_count = 0
        if subsidiaries:
            # Get max workers from settings
            try:
                from config import settings
                max_workers = min(len(subsidiaries), settings.MAX_PARALLEL_SANCTIONS_SCREENING)
            except (ImportError, AttributeError):
                max_workers = min(len(subsidiaries), 20)  # Fallback

            logger.info(f"Screening {len(subsidiaries)} subsidiaries with {max_workers} workers")

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(screen_subsidiary, sub) for sub in subsidiaries]
                for future in as_completed(futures):
                    _, hit_count, error = future.result()
                    if not error:
                        subsidiary_sanctions_count += hit_count

        # Screen directors and shareholders in parallel
        person_sanctions_count = 0
        all_persons = directors + shareholders
        if all_persons:
            # Get max workers from settings
            try:
                from config import settings
                max_workers = min(len(all_persons), settings.MAX_PARALLEL_SANCTIONS_SCREENING)
            except (ImportError, AttributeError):
                max_workers = min(len(all_persons), 20)  # Fallback

            logger.info(f"Screening {len(all_persons)} persons with {max_workers} workers")

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(screen_person, person) for person in all_persons]
                for future in as_completed(futures):
                    _, hit_count, error = future.result()
                    if not error:
                        person_sanctions_count += hit_count

        logger.info(
            f"[{search_id}] Cross-entity screening complete: "
            f"{subsidiary_sanctions_count} subsidiary hits, {person_sanctions_count} person hits"
        )

        # STEP 5: Build network graph
        logger.info(f"[{search_id}] Step 5: Building network graph...")
        network_service = get_network_service()

        network_graph = network_service.build_network_graph(
            company_name=request.entity_name,
            subsidiaries=subsidiaries,
            sisters=sisters,
            directors=directors,
            shareholders=shareholders,
            transactions=transactions,
            parent_info=parent_info
        )

        logger.info(
            f"[{search_id}] Network graph built: "
            f"{len(network_graph['nodes'])} nodes, {len(network_graph['edges'])} edges"
        )

        # STEP 6: Generate intelligence report
        logger.info(f"[{search_id}] Step 6: Generating intelligence report...")
        intelligence_report = research_service.generate_intelligence_report(
            request.entity_name
        )

        logger.info(f"[{search_id}] Intelligence report generated")

        # STEP 6.1: Fallback parent extraction from intelligence report
        if not parent_info and intelligence_report:
            logger.info(f"[{search_id}] No parent found via network search — attempting extraction from intelligence report...")
            parent_info = research_service.extract_parent_from_report(request.entity_name, intelligence_report)
            if parent_info:
                logger.info(f"[{search_id}] Parent extracted from report: {parent_info['name']}")

        # STEP 6.5: Extract AI risk assessment and calculate combined risk
        logger.info(f"[{search_id}] Step 6.5: Calculating combined risk level...")
        risk_service = get_risk_assessment_service()
        ai_assessment = risk_service.extract_ai_risk_assessment(intelligence_report)
        risk_level, risk_explanation = risk_service.calculate_combined_risk_level(
            sanctions_hits=sanctions_hits,
            ai_assessment=ai_assessment,
            media_intelligence=media_intelligence
        )

        logger.info(
            f"[{search_id}] Risk calculation complete: {risk_level} "
            f"(Sanctions: {len(sanctions_hits)}, AI: {ai_assessment.get('level', 'N/A')})"
        )

        # STEP 7: Format data for response and database
        sanctions_data = sanctions_service.format_sanctions_data(sanctions_hits)
        media_data = research_service.format_media_data(media_intelligence)

        # Calculate search duration
        total_duration = time.time() - search_start_time
        logger.info(f"[{search_id}] ⏱️  TOTAL NETWORK TIER SEARCH TIME: {total_duration:.2f} seconds")

        # Prepare metadata
        metadata = {
            "entity_name": request.entity_name,
            "country": request.country,
            "fuzzy_threshold": request.fuzzy_threshold,
            "tier": "network",
            "network_depth": request.network_depth,
            "ownership_threshold": request.ownership_threshold,
            "include_sisters": request.include_sisters,
            "max_level_2_searches": request.max_level_2_searches,
            "max_level_3_searches": request.max_level_3_searches,
            "search_duration_seconds": round(total_duration, 2),
            "parallelization_enabled": True,
            "conglomerate_method": conglomerate_data.get('method', 'unknown'),
            "data_sources_used": data_sources_used,
            "risk_explanation": risk_explanation  # Include risk explanation in metadata
        }

        # Prepare network data for database
        network_data_db = {
            "graph": network_graph,
            "subsidiaries": subsidiaries,
            "sisters": sisters,
            "parent_info": parent_info,
            "financial_intelligence": {
                "directors": directors,
                "shareholders": shareholders,
                "transactions": transactions
            },
            "warnings": warnings,
            "data_sources_used": data_sources_used,
            "statistics": {
                "total_subsidiaries": len(subsidiaries),
                "total_sisters": len(sisters),
                "total_directors": len(directors),
                "total_shareholders": len(shareholders),
                "total_transactions": len(transactions),
                "subsidiary_sanctions_hits": subsidiary_sanctions_count,
                "person_sanctions_hits": person_sanctions_count,
                # Level breakdown for subsidiaries
                "level_1_count": level_stats["level_1"],
                "level_2_count": level_stats["level_2"],
                "level_3_count": level_stats["level_3"]
            }
        }

        # STEP 8: Save to database
        logger.info(f"[{search_id}] Saving results to database...")
        save_success = save_search_results(
            search_id=search_id,
            entity_name=request.entity_name,
            tier="network",
            risk_level=risk_level,
            sanctions_data=sanctions_data,
            research_data={
                "media_intelligence": media_intelligence,
                "media_data": media_data
            },
            network_data=network_data_db,
            intelligence_report=intelligence_report,
            metadata=metadata
        )

        if not save_success:
            logger.warning(f"[{search_id}] Failed to save to database, but continuing...")

        logger.info(f"[{search_id}] Network tier search complete")

        # Return response
        return SearchResponse(
            search_id=search_id,
            status="completed",
            tier="network",
            entity_name=request.entity_name,
            risk_level=risk_level,
            risk_explanation=risk_explanation,  # Include risk explanation
            sanctions_hits=len(sanctions_hits),
            media_hits=media_intelligence['total_hits'],
            intelligence_report=intelligence_report,
            timestamp=timestamp,
            # Include limited data in response (full data available via GET /results/{id})
            sanctions_data=sanctions_data[:10],
            media_data=media_data[:10],
            network_data=network_graph,
            financial_intelligence={
                "directors": directors[:20],
                "shareholders": shareholders[:20],
                "transactions": transactions[:20]
            },
            subsidiaries=subsidiaries[:50],  # Limit subsidiaries in response
            warnings=warnings,
            data_sources_used=data_sources_used,
            metadata=metadata
        )

    except Exception as e:
        logger.error(f"[{search_id}] Network tier search failed: {str(e)}", exc_info=True)

        # Save failed search to database
        try:
            save_search_results(
                search_id=search_id,
                entity_name=request.entity_name,
                tier="network",
                risk_level="UNKNOWN",
                sanctions_data=[],
                research_data={"error": str(e)},
                intelligence_report=f"Network tier search failed: {str(e)}",
                metadata={"status": "failed", "error": str(e)}
            )
        except:
            pass  # Don't fail on save error

        raise HTTPException(
            status_code=500,
            detail={
                "error": "NetworkSearchError",
                "message": f"Failed to complete network tier search: {str(e)}",
                "search_id": search_id
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
