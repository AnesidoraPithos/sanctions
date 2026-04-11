"""
Search Routes

Endpoints for entity background searches (base/network/deep tiers).
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Path
from functools import partial
from typing import Dict, Any
import uuid
from datetime import datetime
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import backend modules
from models.requests import SearchRequest
from models.responses import SearchResponse
from services.sanctions_service import get_sanctions_service
from services.research_service import get_research_service
from services.conglomerate_service import get_conglomerate_service
from services.network_service import get_network_service
from services.risk_assessment_service import get_risk_assessment_service
from db_operations.db import save_search_results
from websocket.progress_handler import update_progress, complete_progress, fail_progress
from core.cancel_store import mark_cancelled, is_cancelled, clear_cancelled

logger = logging.getLogger(__name__)

router = APIRouter()


def _check_cancel(search_id: str) -> None:
    """Raise HTTPException(499) if the search has been cancelled by the user."""
    if is_cancelled(search_id):
        clear_cancelled(search_id)
        fail_progress(search_id, "Search cancelled by user")
        raise HTTPException(
            status_code=499,
            detail={"error": "Cancelled", "message": "Search was cancelled by the user"},
        )


@router.post("/{search_id}/cancel")
def cancel_search(search_id: str = Path(..., description="Search ID to cancel")):
    """Signal a running search to stop at its next checkpoint."""
    mark_cancelled(search_id)
    return {"cancelled": True, "search_id": search_id}


@router.post("/base", response_model=SearchResponse)
def search_base_tier(request: SearchRequest):
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
    search_id = request.client_search_id or str(uuid.uuid4())
    timestamp = datetime.utcnow()
    _progress = partial(update_progress, search_id)

    logger.info(f"Starting base tier search: {search_id} for entity: {request.entity_name}")

    try:
        # Step 1: Sanctions Screening
        _progress("Sanctions screening", 5)
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
        _check_cancel(search_id)
        _progress("OSINT media intelligence", 40)
        logger.info(f"[{search_id}] Step 2: OSINT media intelligence...")
        research_service = get_research_service()
        media_intelligence = research_service.get_media_intelligence(request.entity_name)

        logger.info(
            f"[{search_id}] Media intelligence complete: "
            f"{media_intelligence['total_hits']} hits found"
        )

        # Step 3: Generate Intelligence Report
        _check_cancel(search_id)
        _progress("Generating intelligence report", 65)
        logger.info(f"[{search_id}] Step 3: Generating LLM intelligence report...")
        intelligence_report = research_service.generate_intelligence_report(
            request.entity_name,
            sanctions_hits=sanctions_hits
        )

        logger.info(f"[{search_id}] Intelligence report generated")

        # Step 4: Extract AI risk assessment and calculate combined risk
        _check_cancel(search_id)
        _progress("Calculating risk level", 80)
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
        _progress("Saving results", 92)
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

        complete_progress(search_id)
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
        fail_progress(search_id, str(e))

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
def search_network_tier(request: SearchRequest):
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
    search_id = request.client_search_id or str(uuid.uuid4())
    timestamp = datetime.utcnow()
    search_start_time = time.time()
    _progress = partial(update_progress, search_id)

    logger.info(
        f"Starting network tier search: {search_id} for entity: {request.entity_name} "
        f"(depth={request.network_depth}, ownership_threshold={request.ownership_threshold}%)"
    )

    try:
        # STEP 1: Run base tier research (sanctions + media intelligence)
        _progress("Sanctions screening", 5)
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
        _check_cancel(search_id)
        _progress("Conglomerate discovery", 20)
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
        _check_cancel(search_id)
        _progress("Extracting financial intelligence", 38)
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
        _check_cancel(search_id)
        _progress("Cross-entity sanctions screening", 55)
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
        _check_cancel(search_id)
        _progress("Building network graph", 72)
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
        _check_cancel(search_id)
        _progress("Generating intelligence report", 82)
        logger.info(f"[{search_id}] Step 6: Generating intelligence report...")
        intelligence_report = research_service.generate_intelligence_report(
            request.entity_name,
            sanctions_hits=sanctions_hits
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
        _progress("Saving results", 93)
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

        complete_progress(search_id)
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
        fail_progress(search_id, str(e))

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
def search_deep_tier(request: SearchRequest):
    """
    Perform deep tier entity background search (Phase 3)

    Deep tier includes:
    - All network tier features
    - USAspending.gov federal procurement data (graceful skip if unavailable)
    - Financial flow extraction from related-party transactions
    - Enhanced intelligence report
    """
    search_id = request.client_search_id or str(uuid.uuid4())
    timestamp = datetime.utcnow()
    search_start_time = time.time()
    _progress = partial(update_progress, search_id)

    logger.info(f"Starting deep tier search: {search_id} for entity: {request.entity_name}")

    try:
        # --- STEP 1: Base tier ---
        _progress("Sanctions screening", 5)
        logger.info(f"[{search_id}] Step 1: Base tier research...")
        sanctions_service = get_sanctions_service()
        research_service = get_research_service()

        sanctions_hits = sanctions_service.search_sanctions(
            entity_name=request.entity_name,
            country=request.country,
            fuzzy_threshold=request.fuzzy_threshold,
        )
        media_intelligence = research_service.get_media_intelligence(request.entity_name)

        logger.info(
            f"[{search_id}] Base tier: {len(sanctions_hits)} sanctions hits, "
            f"{media_intelligence['total_hits']} media hits"
        )

        # --- STEP 2: Conglomerate discovery ---
        _check_cancel(search_id)
        _progress("Conglomerate discovery", 20)
        logger.info(f"[{search_id}] Step 2: Conglomerate discovery...")
        conglomerate_service = get_conglomerate_service()

        conglomerate_data = conglomerate_service.discover_subsidiaries(
            parent_company=request.entity_name,
            depth=request.network_depth,
            ownership_threshold=request.ownership_threshold,
            include_sisters=request.include_sisters,
            max_level_2_searches=request.max_level_2_searches,
            max_level_3_searches=request.max_level_3_searches,
        )

        subsidiaries = conglomerate_data.get("subsidiaries", [])
        sisters = conglomerate_data.get("sisters", [])
        parent_info = conglomerate_data.get("parent", None)
        warnings = conglomerate_data.get("warnings", [])
        data_sources_used = conglomerate_data.get("data_sources_used", [])

        logger.info(
            f"[{search_id}] Conglomerate: {len(subsidiaries)} subsidiaries, "
            f"{len(sisters)} sisters"
        )

        # --- STEP 3: Financial intelligence ---
        _check_cancel(search_id)
        _progress("Extracting financial intelligence", 40)
        logger.info(f"[{search_id}] Step 3: Extracting financial intelligence...")
        cik = conglomerate_service.search_sec_edgar_for_cik(request.entity_name)
        financial_intelligence = conglomerate_service.extract_financial_intelligence(
            company_name=request.entity_name,
            cik=cik,
        )

        directors = financial_intelligence.get("directors", [])
        shareholders = financial_intelligence.get("shareholders", [])
        transactions = financial_intelligence.get("transactions", [])
        warnings.extend(financial_intelligence.get("warnings", []))

        # --- STEP 4: Cross-entity sanctions screening ---
        _check_cancel(search_id)
        _progress("Cross-entity sanctions screening", 55)
        logger.info(f"[{search_id}] Step 4: Cross-entity sanctions screening...")

        def _screen_entity(entity: dict) -> dict:
            try:
                hits = sanctions_service.search_sanctions(
                    entity_name=entity["name"],
                    country=None,
                    fuzzy_threshold=request.fuzzy_threshold,
                )
                entity["sanctions_hits"] = len(hits)
                entity["sanctions_data"] = hits[:5]
            except Exception as exc:
                logger.error(f"Error screening {entity['name']}: {exc}")
                entity.setdefault("sanctions_hits", 0)
                entity.setdefault("sanctions_data", [])
            return entity

        subsidiary_sanctions_count = 0
        person_sanctions_count = 0

        all_entities = list(subsidiaries) + list(directors) + list(shareholders)
        if all_entities:
            try:
                from config import settings as cfg
                max_workers = min(len(all_entities), cfg.MAX_PARALLEL_SANCTIONS_SCREENING)
            except (ImportError, AttributeError):
                max_workers = min(len(all_entities), 20)

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(_screen_entity, e) for e in all_entities]
                for future in as_completed(futures):
                    e = future.result()
                    hits = e.get("sanctions_hits", 0)
                    if e in subsidiaries:
                        subsidiary_sanctions_count += hits
                    else:
                        person_sanctions_count += hits

        # --- STEP 5: Build network graph ---
        _check_cancel(search_id)
        _progress("Building network graph", 65)
        logger.info(f"[{search_id}] Step 5: Building network graph...")
        network_service = get_network_service()
        network_graph = network_service.build_network_graph(
            company_name=request.entity_name,
            subsidiaries=subsidiaries,
            sisters=sisters,
            directors=directors,
            shareholders=shareholders,
            transactions=transactions,
            parent_info=parent_info,
        )

        # --- STEP 6: USAspending.gov procurement records (graceful skip) ---
        _check_cancel(search_id)
        _progress("Querying federal procurement records", 72)
        logger.info(f"[{search_id}] Step 6: Federal procurement data (USAspending)...")
        usaspending_flows: list = []
        try:
            import requests as _req
            payload = {
                "filters": {
                    "recipient_search_text": [request.entity_name],
                    "award_type_codes": ["A", "B", "C", "D"],
                },
                "fields": ["Recipient Name", "Award Amount", "Awarding Agency Name", "Action Date", "Award Type"],
                "limit": 20,
                "page": 1,
            }
            resp = _req.post(
                "https://api.usaspending.gov/api/v2/search/spending_by_award/",
                json=payload,
                timeout=10,
            )
            if resp.status_code == 200:
                awards = resp.json().get("results", [])
                for award in awards:
                    usaspending_flows.append({
                        "source": award.get("Awarding Agency Name", "US Federal Government"),
                        "target": award.get("Recipient Name", request.entity_name),
                        "amount": award.get("Award Amount"),
                        "currency": "USD",
                        "type": award.get("Award Type", "procurement"),
                        "date": award.get("Action Date"),
                    })
                logger.info(f"[{search_id}] USAspending: {len(usaspending_flows)} awards found")
            else:
                logger.warning(f"[{search_id}] USAspending returned {resp.status_code}")
        except Exception as exc:
            logger.warning(f"[{search_id}] USAspending unavailable: {exc}")
            warnings.append({
                "source": "usaspending",
                "message": "Federal procurement data unavailable (USAspending.gov unreachable)",
                "severity": "info",
            })

        # --- STEP 7: Build financial flows from transactions + USAspending ---
        _progress("Extracting financial flows", 80)
        financial_flows: list = list(usaspending_flows)
        for tx in transactions:
            if tx.get("counterparty"):
                financial_flows.append({
                    "source": request.entity_name,
                    "target": tx.get("counterparty", ""),
                    "amount": tx.get("amount"),
                    "currency": tx.get("currency", "USD"),
                    "type": tx.get("transaction_type", "related_party"),
                    "date": tx.get("transaction_date"),
                })

        # --- STEP 8: Generate intelligence report ---
        _check_cancel(search_id)
        _progress("Generating intelligence report", 85)
        logger.info(f"[{search_id}] Step 8: Generating intelligence report...")
        intelligence_report = research_service.generate_intelligence_report(
            request.entity_name,
            sanctions_hits=sanctions_hits
        )

        # Fallback parent extraction
        if not parent_info and intelligence_report:
            parent_info = research_service.extract_parent_from_report(
                request.entity_name, intelligence_report
            )

        # --- STEP 9: Risk assessment ---
        _progress("Calculating risk level", 92)
        risk_service = get_risk_assessment_service()
        ai_assessment = risk_service.extract_ai_risk_assessment(intelligence_report)
        risk_level, risk_explanation = risk_service.calculate_combined_risk_level(
            sanctions_hits=sanctions_hits,
            ai_assessment=ai_assessment,
            media_intelligence=media_intelligence,
        )

        # --- STEP 11: Director pivot (Phase 4) ---
        director_pivots: list = []
        if request.include_director_pivot:
            _progress("Pivoting directors (interlocking directorates)...", 93)
            try:
                from services.director_pivot_service import DirectorPivotService
                director_pivots = DirectorPivotService().pivot_directors(directors[:10])
                logger.info(f"[{search_id}] Director pivot: {len(director_pivots)} pivots")
            except Exception as _exc:
                logger.warning(f"[{search_id}] Director pivot failed: {_exc}")
                warnings.append({
                    "source": "director_pivot",
                    "message": f"Director pivot unavailable: {_exc}",
                    "severity": "info",
                })

        # --- STEP 12: Infrastructure correlation (Phase 4) ---
        infrastructure: list = []
        if request.include_infrastructure:
            _progress("Correlating digital infrastructure...", 94)
            try:
                from services.infrastructure_service import InfrastructureService
                _all_sources = (
                    media_intelligence.get("official_sources", [])
                    + media_intelligence.get("general_media", [])
                )
                all_urls = [h.get("url", "") for h in _all_sources if h.get("url")]
                infrastructure = InfrastructureService().correlate_infrastructure(
                    request.entity_name, all_urls
                )
                logger.info(f"[{search_id}] Infrastructure: {len(infrastructure)} domains analysed")
            except Exception as _exc:
                logger.warning(f"[{search_id}] Infrastructure correlation failed: {_exc}")
                warnings.append({
                    "source": "infrastructure",
                    "message": f"Infrastructure correlation unavailable: {_exc}",
                    "severity": "info",
                })

        # --- STEP 13: Beneficial ownership (Phase 4) ---
        beneficial_owners: list = []
        if request.include_beneficial_ownership:
            _progress("Tracing beneficial ownership...", 95)
            try:
                from services.beneficial_ownership_service import BeneficialOwnershipService
                beneficial_owners = BeneficialOwnershipService().get_beneficial_owners(
                    request.entity_name
                )
                logger.info(f"[{search_id}] Beneficial owners: {len(beneficial_owners)} found")
            except Exception as _exc:
                logger.warning(f"[{search_id}] Beneficial ownership tracing failed: {_exc}")
                warnings.append({
                    "source": "beneficial_ownership",
                    "message": f"Beneficial ownership data unavailable: {_exc}",
                    "severity": "info",
                })

        # --- STEP 14: Advanced OSINT (Phase 4) ---
        advanced_osint_data: dict = {"littlesis_results": [], "dork_results": []}
        _progress("Advanced OSINT reconnaissance...", 96)
        try:
            from services.osint_advanced_service import AdvancedOsintService
            advanced_osint_data = AdvancedOsintService().get_advanced_osint(request.entity_name)
            logger.info(
                f"[{search_id}] Advanced OSINT: "
                f"{len(advanced_osint_data.get('littlesis_results', []))} LittleSis, "
                f"{len(advanced_osint_data.get('dork_results', []))} dork results"
            )
        except Exception as _exc:
            logger.warning(f"[{search_id}] Advanced OSINT failed: {_exc}")
            warnings.append({
                "source": "advanced_osint",
                "message": f"Advanced OSINT unavailable: {_exc}",
                "severity": "info",
            })

        # --- STEP 10: Format & save ---
        _progress("Saving results", 97)
        sanctions_data = sanctions_service.format_sanctions_data(sanctions_hits)
        media_data = research_service.format_media_data(media_intelligence)

        total_duration = time.time() - search_start_time
        logger.info(f"[{search_id}] TOTAL DEEP TIER SEARCH TIME: {total_duration:.2f}s")

        level_stats = {
            "level_1": len([s for s in subsidiaries if s.get("level") == 1]),
            "level_2": len([s for s in subsidiaries if s.get("level") == 2]),
            "level_3": len([s for s in subsidiaries if s.get("level") == 3]),
        }

        metadata = {
            "entity_name": request.entity_name,
            "country": request.country,
            "fuzzy_threshold": request.fuzzy_threshold,
            "tier": "deep",
            "network_depth": request.network_depth,
            "ownership_threshold": request.ownership_threshold,
            "include_sisters": request.include_sisters,
            "max_level_2_searches": request.max_level_2_searches,
            "max_level_3_searches": request.max_level_3_searches,
            "search_duration_seconds": round(total_duration, 2),
            "parallelization_enabled": True,
            "conglomerate_method": conglomerate_data.get("method", "unknown"),
            "data_sources_used": data_sources_used,
            "risk_explanation": risk_explanation,
            "financial_flows_count": len(financial_flows),
            # Phase 4 counts
            "director_pivots_count": len(director_pivots),
            "infrastructure_domains_count": len(infrastructure),
            "beneficial_owners_count": len(beneficial_owners),
        }

        network_data_db = {
            "graph": network_graph,
            "subsidiaries": subsidiaries,
            "sisters": sisters,
            "parent_info": parent_info,
            "financial_intelligence": {
                "directors": directors,
                "shareholders": shareholders,
                "transactions": transactions,
            },
            "financial_flows": financial_flows,
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
                "level_1_count": level_stats["level_1"],
                "level_2_count": level_stats["level_2"],
                "level_3_count": level_stats["level_3"],
            },
            # Phase 4
            "director_pivots": director_pivots,
            "infrastructure": infrastructure,
            "beneficial_owners": beneficial_owners,
            "advanced_osint": advanced_osint_data,
        }

        save_search_results(
            search_id=search_id,
            entity_name=request.entity_name,
            tier="deep",
            risk_level=risk_level,
            sanctions_data=sanctions_data,
            research_data={"media_intelligence": media_intelligence, "media_data": media_data},
            network_data=network_data_db,
            intelligence_report=intelligence_report,
            metadata=metadata,
        )

        complete_progress(search_id)

        logger.info(f"[{search_id}] Deep tier search complete")

        return SearchResponse(
            search_id=search_id,
            status="completed",
            tier="deep",
            entity_name=request.entity_name,
            risk_level=risk_level,
            risk_explanation=risk_explanation,
            sanctions_hits=len(sanctions_hits),
            media_hits=media_intelligence["total_hits"],
            intelligence_report=intelligence_report,
            timestamp=timestamp,
            sanctions_data=sanctions_data[:10],
            media_data=media_data[:10],
            network_data=network_graph,
            financial_intelligence={
                "directors": directors[:20],
                "shareholders": shareholders[:20],
                "transactions": transactions[:20],
            },
            subsidiaries=subsidiaries[:50],
            financial_flows=financial_flows[:50],
            # Phase 4
            director_pivots=director_pivots,
            infrastructure=infrastructure,
            beneficial_owners=beneficial_owners,
            advanced_osint=advanced_osint_data,
            warnings=warnings,
            data_sources_used=data_sources_used,
            metadata=metadata,
        )

    except Exception as e:
        logger.error(f"[{search_id}] Deep tier search failed: {str(e)}", exc_info=True)

        fail_progress(search_id, str(e))

        try:
            save_search_results(
                search_id=search_id,
                entity_name=request.entity_name,
                tier="deep",
                risk_level="UNKNOWN",
                sanctions_data=[],
                research_data={"error": str(e)},
                intelligence_report=f"Deep tier search failed: {str(e)}",
                metadata={"status": "failed", "error": str(e)},
            )
        except Exception:
            pass

        raise HTTPException(
            status_code=500,
            detail={
                "error": "DeepSearchError",
                "message": f"Failed to complete deep tier search: {str(e)}",
                "search_id": search_id,
            },
        )
