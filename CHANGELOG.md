# BEAR² Changelog

> Structured history extracted from `dev-logs.md` and git history.
> Dates are in YYYY-MM-DD format.

---

## [Unreleased] — version3 branch

### Added
- Phase 4 deep-tier features: director pivot (interlocking directorates), digital infrastructure correlation (WHOIS/IP/ASN), beneficial ownership tracing, advanced OSINT via LittleSis
- `director_pivot_service.py`, `infrastructure_service.py`, `beneficial_ownership_service.py`, `osint_advanced_service.py`
- USAspending.gov federal procurement data in deep tier
- WebSocket progress tracking (`backend/websocket/progress_handler.py`)
- Frontend tabs: ManagementNetworkTab, InfrastructureTab, BeneficialOwnershipTab
- `TierBadge.tsx` for displaying research tier on results

### Changed
- Frontend redesigned with "Classified Intelligence Dossier" aesthetic (amber/gold on deep black)

---

## [2.1.0] — 2026-03-09

### Added
- **FastAPI backend decoupled from Streamlit** — REST API at `backend/` with three-tier endpoints (`/api/search/base`, `/api/search/network`, `/api/search/deep`)
- **Next.js frontend** at `frontend/` — replaces Streamlit (`archive/legacy_streamlit/`)
- Three-tier research system: Base (30-60s), Network (2-5min), Deep (5-15min)
- Network graph visualization (`NetworkGraph.tsx`) replacing PyVis
- Export controls (`ExportControls.tsx`)
- `TierSelector.tsx` slider UI for research depth selection
- Parallel cross-entity sanctions screening using `ThreadPoolExecutor`
- Auto-save all searches to SQLite database
- Save/Restore functionality (< 2 second restore times, 15-300x speedup)
- Search history page (`app/saved/page.tsx`)
- Pydantic request/response models (`backend/models/`)
- Risk assessment service with AI + sanctions combined scoring (`risk_assessment_service.py`)
- Network service for graph data generation (`network_service.py`)

---

## [2.0.0] — 2026-03-08

### Added (Legacy Streamlit era — now in `archive/legacy_streamlit/`)
- **Entity relationship diagram** with interactive Neo4j-style network visualization (PyVis)
- **Geographic visualization** (Folium world map with entity markers)
- **Graph path finder** — discover connection paths between any two entities
- `graph_builder.py` — NetworkX MultiDiGraph with parent/subsidiary/director/shareholder/transaction nodes
- `visualizations.py` — PyVis physics-based graph + Folium geographic map

---

## [1.9.0] — 2026-03-07

### Added
- **Financial intelligence extraction** from SEC EDGAR (10-K, 20-F, DEF 14A)
  - Directors & officers (name, title, nationality)
  - Major shareholders (ownership %, voting rights, jurisdiction)
  - Related party transactions (counterparty, amount, type)
- Database tables: `directors_officers`, `major_shareholders`, `related_party_transactions`
- Auto cross-check directors/shareholders against sanctions lists
- SEC filing type support: 10-K (US), 20-F (foreign), DEF 14A (proxy)

---

## [1.8.0] — 2026-03-05

### Added
- **Reverse search**: find parent company and sister companies when starting from a subsidiary
- **Wikipedia integration** as data source for conglomerate subsidiary discovery
- **Ownership threshold filter**: filter subsidiaries by ownership % (100%, >50%, custom)
- **Source reference URLs** for DuckDuckGo search results (clickable "View Source" links)
- Multi-level conglomerate search: depth 1-3 with configurable level-2/level-3 limits

### Fixed
- LLM extracting example company names (Riot Games, Epic Games) as actual search results — replaced with generic placeholders
- LLM extracting descriptive text ("subsidiary for Assassin's Creed") instead of legal entity names — added `_validate_company_name()` filter and strengthened prompts
- Entity name extraction sometimes returned news headlines instead of legal names

### Changed
- Conglomerate data source priority: SEC EDGAR → OpenCorporates API → Wikipedia → DuckDuckGo

---

## [1.5.0] — 2026-02-24 to 2026-03-05

### Changed (UI renames for clarity)
- "Signals Intel" → "News Report"
- "Tactical Summary" → "Info Summary"
- "Federal Reg" → "Entity List"
- "Sentinels" → "Entity Background Check Bot"
- "Subject Identifier" → "Entity Name"
- "Target Params" → "Search Params"
- "Jurisdictions" → "Country of Origin"
- "Operations Archive" → "Search History"
- "Process Logs" → "Thinking Process Logs"
- "Intel Doss" → "Search Results"

### Added
- Hover tooltip explaining risk classification rationale
- Disclaimer banners on Info Summary and News Report tabs
- DOD 1260H / FCC Covered List local database (PDF + URL ingested manually)
- Exact match detection — system no longer requires "Pte. Ltd." suffix to match

### Fixed
- Info summary now longer and includes reference links
- Score system updated to account for fuzzy matching algorithms
- Threat level now considers AI-generated report risk level (e.g., Vadim Makarov not in DB but should be flagged)

---

## [1.2.0] — 2026-02-03

### Added
- Ollama local LLM support (runs on-device, no data leaves the machine)
- DuckDuckGo as free web search backend (replacing Google/Gemini)
- Risk level classification: SAFE / LOW / MID / HIGH / VERY HIGH

### Changed
- Threat level calculation now uses combined scoring of database match count, match score, and media hit count
- Free tier limits on Gemini reached — migrated to Ollama

---

## [1.0.0] — 2026-01-08

### Added
- Initial USA sanctions screening via Trade.gov Consolidated Screening List API
- Pagination loop to retrieve full results (not just first page)
- Chinese → English name translation (via LLM)
- DuckDuckGo OSINT media search for entity news coverage
- Basic risk classification based on database match score
- Search history logging

---

## Pending / Outstanding Items

As of 2026-04-09 audit, these are known gaps vs. the specification in `key documents/requirements.md`:

- Geographic map visualization (was Folium/PyVis in legacy Streamlit, not ported to Next.js)
- Companies House UK PSC integration
- Open Ownership Register (BODS) integration
- OCCRP Aleph (Panama Papers / leak databases)
- WhaleWisdom 13F institutional investor data
- Crunchbase VC/funding integration
- JWT authentication and rate limiting
- PWA offline access
- Webhook support for automation workflows

See `docs/implementation-status.md` for full audit.
