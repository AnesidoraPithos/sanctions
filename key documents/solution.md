# Entity Background Research Agent — Solution Architecture Document

**Document Version**: 1.0
**System Version**: 3.0.0
**Date**: 2026-03-12
**Project**: Entity Background Research Agent - Intelligence Operations System
**Status**: Design Phase

---

## 1. Purpose and Scope

This document describes the solution architecture for the **Entity Background Research Agent**, an AI-powered intelligence operations system for sanctions screening and corporate structure analysis.

### What This Document Covers

- Architecture design (logical, deployment, and data views)
- Design decisions and trade-offs
- Core components and responsibilities
- System interfaces and integration patterns
- API specifications and data flows
- Third-party dependencies and backing services
- Phased implementation roadmap for development teams

### Out of Scope

- Internal algorithms for specific LLM providers
- Organization-specific security controls not represented in code
- Detailed deployment infrastructure (Kubernetes, Docker configs)
- Database schema migration scripts (covered in separate documentation)

---

## 2. Executive Summary

### Problem Statement

International relations staff currently spend 30 minutes to several hours manually researching entities across 10+ scattered sanctions databases (OFAC, BIS, Treasury, State Department, DOD, FCC), manually reviewing SEC EDGAR filings, and separately querying OpenCorporates and conducting Google searches. This results in decision delays, compliance risk, inefficiency, and inconsistent quality.

### Solution Overview

The Entity Background Research Agent automates multi-source research across 10+ databases, visualizes entity relationships, and generates comprehensive risk assessments in **minutes rather than hours**. The system features a modern **React/Next.js frontend** with **REST API backend** and a **three-tiered research system** that allows users to balance speed, cost, and depth:

**Research Tiers:**
- **Base Research** (~30-60 seconds): Database sanctions screening + AI report generation + media source citations
- **Network Research** (~2-5 minutes): Base + corporate structure discovery (subsidiaries, parents, sisters, directors, shareholders)
- **Deep Research** (~5-15 minutes): Network + financial flow mapping + criminal history checks

**Core Capabilities:**
- **15-300x faster** results on subsequent queries (< 2 seconds vs 30 seconds - 10 minutes) via save/restore functionality
- Automated sanctions screening across OFAC, BIS, Treasury, State, DOD, FCC databases
- Conglomerate search with configurable depth (1-3 levels) and ownership filtering
- Automated SEC EDGAR extraction (directors, shareholders, transactions)
- Fuzzy name matching with configurable thresholds to catch name variations
- Interactive relationship visualizations (Neo4j-style network graphs)
- LLM-generated intelligence reports with multi-format export (JSON, Excel, PDF)
- REST API for frontend integration and future automation workflows

### Target Users

- **Primary**: International Relations Staff, Compliance Officers, Risk Analysts
- **Secondary**: Due Diligence Teams, Legal Departments, Financial Investigators, Government Analysts

### Architecture Principles

1. **Speed & Efficiency**: Minimize API calls through intelligent caching and save/restore mechanisms
2. **Comprehensive Coverage**: Integrate multiple authoritative data sources with fallback strategies
3. **Transparency**: Provide source attribution and confidence scores for all findings
4. **Flexibility**: Support both simple single-entity queries and complex multi-level conglomerate investigations
5. **Defensibility**: Generate audit trails and exportable reports for compliance documentation
6. **User-Controlled Scope**: Empower users to select research depth (base/network/deep) based on decision importance
7. **API-First Design**: Decouple frontend from backend to enable integrations, automation, and future platform expansion

---

## 3. Architecture Design

### 3.1 System Diagram

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                            USER INTERFACE LAYER                              │
│                    (React/Next.js Web Application)                           │
│                                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Research   │  │    Search    │  │   Results    │  │    Saved     │   │
│  │ Tier Slider  │  │  Interface   │  │  Dashboard   │  │  Searches    │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Network Graph│  │ Intelligence │  │    Export    │  │   Settings   │   │
│  │ (D3.js/Cyto) │  │    Report    │  │ (PDF/Excel)  │  │   Panel      │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                              HTTPS/REST API
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           REST API BACKEND LAYER                             │
│                         (Flask/FastAPI Application)                          │
│                                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │    Auth &    │  │   Search     │  │   Results    │  │    Export    │   │
│  │   Routing    │  │  Endpoints   │  │   Endpoints  │  │  Endpoints   │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                                               │
│  API Routes: /api/search/{base|network|deep}, /api/results/{id},            │
│              /api/history, /api/export, /ws/progress/{id}                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         APPLICATION CORE LAYER                               │
│                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    Search Orchestration Engine                         │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │  │
│  │  │   Query      │  │  Conglomerate│  │   Reverse    │               │  │
│  │  │  Processor   │  │   Processor  │  │   Processor  │               │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                     Data Integration Services                          │  │
│  │                                                                         │  │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐            │  │
│  │  │   Sanctions   │  │  Conglomerate │  │   Financial   │            │  │
│  │  │   Service     │  │    Service    │  │    Intel      │            │  │
│  │  │ (10+ sources) │  │  (SEC/OpenCorp)│  │   Service     │            │  │
│  │  └───────────────┘  └───────────────┘  └───────────────┘            │  │
│  │                                                                         │  │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐            │  │
│  │  │     OSINT     │  │     Name      │  │     Risk      │            │  │
│  │  │   Service     │  │   Matching    │  │    Scoring    │            │  │
│  │  │  (DuckDuckGo) │  │   (Fuzzy)     │  │    Engine     │            │  │
│  │  └───────────────┘  └───────────────┘  └───────────────┘            │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    Intelligence Layer (AI/LLM)                         │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │  │
│  │  │    Report    │  │  Translation │  │   Synthesis  │               │  │
│  │  │  Generation  │  │    Service   │  │    Engine    │               │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DATA PERSISTENCE LAYER                                  │
│                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                       SQLite Database                                  │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │  │
│  │  │   Saved      │  │   Search     │  │   Settings   │               │  │
│  │  │  Searches    │  │   Metadata   │  │    Store     │               │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        Cache Layer (Local)                             │  │
│  │           API Response Cache │ Sanctions Data Cache                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL INTEGRATIONS LAYER                             │
│                                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  USA         │  │   SEC        │  │ OpenCorporates│  │  DuckDuckGo  │   │
│  │  Sanctions   │  │   EDGAR      │  │     API       │  │   Search     │   │
│  │  API (10+)   │  │   API        │  │               │  │     API      │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   OpenAI/    │  │  ImportYeti  │  │ USAspending  │  │   Wikipedia  │   │
│  │  Anthropic   │  │     API      │  │     API      │  │     API      │   │
│  │     LLM      │  │  (Planned)   │  │  (Planned)   │  │              │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Design Goals

1. **Speed**: Provide sub-2-second restore times for saved searches (15-300x faster than fresh queries)
2. **Comprehensiveness**: Integrate 10+ sanctions databases and multiple corporate structure sources
3. **Transparency**: Display source attribution, confidence scores, and match percentages for all findings
4. **Flexibility**: Support simple single-entity queries and complex 3-level conglomerate investigations
5. **Usability**: Minimal-click interface for both novice and expert users
6. **Defensibility**: Generate audit-ready reports with timestamps and source citations
7. **Extensibility**: Modular architecture to easily add new data sources and analysis capabilities
8. **Tiered Research**: Allow users to balance speed vs. depth based on their needs (base/network/deep)
9. **API-First**: Expose REST API for frontend and future integrations with automation workflows

### 3.3 Logical Architecture

#### Layer 1: User Interface (Presentation Layer)

**Technology**: React/Next.js (TypeScript web application)

**Components**:
- **Research Tier Slider**: Three-position slider for selecting base/network/deep research depth
- **Search Interface**: Input forms for entity name, country, search parameters with tier selection
- **Results Dashboard**: Comprehensive results display with tab-based navigation
- **Network Graph Visualizer**: D3.js or Cytoscape.js interactive network graphs with drag/zoom
- **Saved Search History**: Filter, sort, restore, and manage previous searches
- **Intelligence Report Viewer**: LLM-generated reports with executive summaries
- **Export Controls**: PDF, Excel, JSON export handlers
- **Settings Panel**: Configure fuzzy matching thresholds, auto-save, data source preferences
- **Real-Time Progress Tracker**: WebSocket-powered progress updates for network/deep tier searches

**State Management**: React Context API or Zustand for global state

**API Client**: Axios or Fetch API for REST backend communication

**Pages** (Next.js App Router):
- `/` - Homepage with research tier selection and search interface
- `/results/[id]` - Results dashboard for completed searches
- `/history` - Saved search history and management
- `/settings` - User preferences and configuration

#### Layer 1.5: REST API Backend (NEW)

**Technology**: Flask or FastAPI (Python web framework)

**Components**:
- **Authentication Middleware**: JWT token validation and user session management
- **Rate Limiting Middleware**: Request throttling (100 req/hr base, 500 req/hr premium)
- **Search Routes**: Tier-specific endpoints for base, network, and deep research
- **Results Routes**: Retrieve and manage search results
- **Export Routes**: Generate PDF/Excel/JSON exports on demand
- **WebSocket Handler**: Real-time progress updates for long-running searches
- **Request Validation**: Pydantic models for request/response validation

**API Endpoints**:
- `POST /api/auth/login` - User authentication
- `POST /api/search/base` - Base tier search (sanctions + report + media)
- `POST /api/search/network` - Network tier search (base + conglomerate)
- `POST /api/search/deep` - Deep tier search (network + financial flows + criminal checks)
- `GET /api/results/{search_id}` - Retrieve search results
- `GET /api/history` - List user's saved searches
- `DELETE /api/history/{search_id}` - Delete saved search
- `POST /api/export/{search_id}` - Export results as PDF/Excel/JSON
- `GET /api/settings` - Get user settings
- `PUT /api/settings` - Update user settings
- `WebSocket /ws/progress/{search_id}` - Real-time progress updates

**API Documentation**: OpenAPI 3.0 specification with Swagger/ReDoc

#### Layer 2: Application Core

**Search Orchestration Engine**:
- **Query Processor**: Handles single-entity sanctions screening and OSINT research
- **Conglomerate Processor**: Manages multi-level subsidiary discovery and recursive analysis
- **Reverse Processor**: Identifies parent companies and sister entities

**Data Integration Services**:
- **Sanctions Service**: Queries 10+ USA sanctions databases (OFAC, BIS, Treasury, State, DOD, FCC)
- **Conglomerate Service**: Extracts corporate structures from SEC EDGAR (10-K, 20-F Exhibit 21.1), OpenCorporates, Wikipedia, web search
- **Financial Intelligence Service**: Parses SEC filings for directors, shareholders, related party transactions
- **OSINT Service**: Conducts DuckDuckGo searches for media coverage and government announcements
- **Name Matching Service**: Fuzzy matching using Levenshtein distance with configurable thresholds
- **Risk Scoring Engine**: 5-level risk assessment (SAFE, LOW, MID, HIGH, VERY HIGH) combining match scores

#### Layer 3: Intelligence Layer (AI/LLM)

- **Report Generation Service**: Synthesizes findings into executive summaries and risk assessments
- **Translation Service**: Handles non-English entity names (planned)
- **Synthesis Engine**: Combines multi-source data into coherent intelligence

#### Layer 4: Data Persistence

- **SQLite Database**: Stores saved searches (50KB - 5MB each), metadata, tags, notes
- **Local Cache**: API responses, sanctions data for performance optimization
- **Settings Store**: User preferences, fuzzy matching thresholds, data source configuration

#### Layer 5: External Integrations

- **USA Sanctions API** (10+ databases)
- **SEC EDGAR API**
- **OpenCorporates API** (optional, requires API key)
- **DuckDuckGo Search API**
- **OpenAI/Anthropic LLM APIs**
- **ImportYeti API** (planned - trade data)
- **USAspending.gov API** (planned - government procurement)
- **Wikipedia API**

### 3.4 Deployment Architecture

**Deployment Mode**: Desktop application (Streamlit local server)

**Runtime Environment**:
- **Language**: Python 3.10+
- **Web Framework**: Streamlit
- **Database**: SQLite (embedded, single-file database)
- **Dependencies**: See `requirements.txt` for complete list

**Data Storage**:
- **Search Database**: `~/.entity_research/searches.db` (SQLite)
- **Cache Directory**: `~/.entity_research/cache/`
- **Export Directory**: `~/Downloads/entity_research_exports/`

**API Access Requirements**:
- Internet connectivity for external APIs
- API keys: OpenCorporates (optional), OpenAI/Anthropic (required for LLM features)
- No authentication required for USA Sanctions API, SEC EDGAR, DuckDuckGo

### 3.5 Data and Control Flows

#### Flow 1A — Base Research Tier (Fast Compliance Check)

1. User opens React web application
2. User selects **Base Research** tier via slider (left position)
3. UI displays: "~30-60 seconds | Sanctions screening + AI report + media sources"
4. User enters entity name and country
5. User clicks "EXECUTE SEARCH"
6. Frontend sends `POST /api/search/base` with request payload
7. **REST API Backend** validates request and creates search task
8. **Sanctions Service** queries 10+ sanctions databases in parallel
9. **OSINT Service** conducts DuckDuckGo searches (official + media sources)
10. **Risk Scoring Engine** calculates risk level (SAFE → VERY HIGH)
11. **Intelligence Layer** generates LLM report with executive summary
12. **Database** auto-saves search results
13. Backend returns search results to frontend
14. UI displays results with "BASE RESEARCH" badge
15. User exports PDF report

**Performance**: 30-60 seconds
**Cost**: Low (minimal API calls)
**Use Case**: Quick compliance check for routine engagements

#### Flow 1B — Network Research Tier (Corporate Structure Analysis)

1. User selects **Network Research** tier via slider (center position)
2. UI displays: "~2-5 minutes | Base + corporate structure + personnel discovery"
3. User enters entity name and country
4. User clicks "EXECUTE SEARCH"
5. Frontend sends `POST /api/search/network` with request payload
6. Backend establishes WebSocket connection for real-time progress
7. **Step 1**: System executes all Base tier operations (Flow 1A steps 8-11)
8. WebSocket sends: "Searching corporate structure... 30% complete"
9. **Conglomerate Service** discovers subsidiaries (SEC EDGAR, OpenCorporates, Wikipedia)
10. WebSocket sends: "Found 12 subsidiaries... 50% complete"
11. **Financial Intelligence Service** extracts directors and shareholders from SEC filings
12. WebSocket sends: "Screening personnel... 70% complete"
13. **Sanctions Service** screens discovered directors/shareholders
14. **Visualization Engine** builds interactive network graph
15. WebSocket sends: "Generating report... 90% complete"
16. **Intelligence Layer** synthesizes network-level findings
17. **Database** saves search with network data
18. Backend returns results with relationship graph
19. UI displays results with "NETWORK RESEARCH" badge and network visualizer
20. User exports multi-sheet Excel workbook

**Performance**: 2-5 minutes
**Cost**: Medium (conglomerate + personnel queries)
**Use Case**: Due diligence for partnerships, M&A target screening

#### Flow 1C — Deep Research Tier (Comprehensive Investigation)

1. User selects **Deep Research** tier via slider (right position)
2. UI displays: "~5-15 minutes | Network + financial flows + criminal history"
3. User enters entity name and country
4. User clicks "EXECUTE SEARCH"
5. Frontend sends `POST /api/search/deep` with request payload
6. Backend establishes WebSocket connection for real-time progress
7. **Step 1**: System executes all Network tier operations (Flow 1B steps 7-16)
8. WebSocket sends: "Analyzing financial flows... 60% complete"
9. **Financial Intelligence Service** extracts trade data (ImportYeti, planned)
10. **Financial Intelligence Service** queries government procurement (USAspending.gov, planned)
11. WebSocket sends: "Performing criminal history checks... 75% complete"
12. **Criminal History Service** (planned) checks directors/officers across jurisdictions
13. **Beneficial Ownership Service** (planned) traces offshore structures
14. WebSocket sends: "Mapping beneficial ownership... 85% complete"
15. **Visualization Engine** adds financial flow layers to network graph
16. WebSocket sends: "Generating comprehensive report... 95% complete"
17. **Intelligence Layer** synthesizes deep-level findings with financial context
18. **Database** saves search with all layers
19. Backend returns comprehensive results with multi-layer graph
20. UI displays results with "DEEP RESEARCH" badge, full network + financial flows
21. User exports comprehensive multi-sheet Excel with all data layers

**Performance**: 5-15 minutes
**Cost**: High (full network + financial + criminal checks)
**Use Case**: High-stakes engagements, regulatory compliance, litigation support

#### Flow 2 — Single Entity Sanctions Screening (Legacy)

1. User enters entity name and country in search interface
2. User enables fuzzy logic toggle
3. User clicks "EXECUTE QUERY"
4. **Query Processor** validates input
5. **Name Matching Service** prepares entity name variations
6. **Sanctions Service** queries 10+ sanctions databases in parallel
7. **OSINT Service** conducts DuckDuckGo searches
8. **Risk Scoring Engine** calculates combined risk level (SAFE → VERY HIGH)
9. **Intelligence Layer** generates LLM report
10. **Database** auto-saves complete search results
11. **UI** displays results across tabs: sanctions matches, media coverage, intelligence report
12. User exports report as PDF

**Performance**: ~30-60 seconds for fresh search

#### Flow 2 — Conglomerate Search (Multi-Level)

1. User enters parent company name
2. User enables "CONGLOMERATE SEARCH" toggle
3. User configures depth (1-3 levels) and ownership filter (100%, >50%, custom%)
4. User clicks "EXECUTE QUERY"
5. **Conglomerate Processor** initiates search
6. **Conglomerate Service** queries sources in waterfall priority:
   - SEC EDGAR (10-K, 20-F Exhibit 21.1) → OpenCorporates API → Wikipedia → DuckDuckGo
7. For Level 1: System discovers subsidiaries and displays with checkboxes
8. User selects subsidiaries to process
9. **Sanctions Service** screens selected subsidiaries
10. **Financial Intelligence Service** extracts SEC data (if available)
11. For Level 2: System discovers sub-subsidiaries of selected L1 entities, repeat steps 8-10
12. For Level 3: System discovers sub-sub-subsidiaries, repeat steps 8-10
13. **Visualization Engine** builds interactive relationship graph
14. **Intelligence Layer** synthesizes findings across full corporate network
15. **Database** saves search with all levels
16. User exports multi-sheet Excel workbook

**Performance**: ~2-10 minutes depending on depth and entity count

#### Flow 3 — Reverse Search (Parent & Sister Discovery)

1. User enters subsidiary name
2. User **disables** "CONGLOMERATE SEARCH" toggle
3. User **enables** "SEARCH FOR PARENT & SISTERS" toggle
4. User clicks "EXECUTE QUERY"
5. **Reverse Processor** queries multiple sources to identify parent company:
   - OpenCorporates control statements → SEC EDGAR mentions → Companies House UK PSC
6. System displays parent company with confidence score
7. **Reverse Processor** queries parent's subsidiaries to find sisters
8. System displays sister companies with checkboxes
9. User selects parent and/or sisters to add to analysis
10. **Sanctions Service** screens selected entities
11. **Visualization Engine** builds relationship graph: subsidiary → parent → sisters
12. **Intelligence Layer** generates report with ownership context
13. **Database** saves search
14. User exports findings

**Performance**: ~30-90 seconds

#### Flow 4 — SEC Financial Intelligence Extraction

1. During any entity search, **Conglomerate Service** checks if entity has SEC registration
2. If registered, **Financial Intelligence Service** retrieves SEC filings:
   - 10-K (US annual reports)
   - 20-F (foreign issuer annual reports)
   - DEF 14A (proxy statements)
3. Service extracts structured data:
   - Directors & Officers (names, titles, nationalities, biographies)
   - Major Shareholders (names, ownership %, voting rights, jurisdictions)
   - Related Party Transactions (counterparty names, amounts, types)
4. **Sanctions Service** automatically cross-checks all extracted personnel against sanctions lists
5. **UI** displays financial intelligence in dedicated tabs with sanctions status columns
6. **Visualization Engine** adds personnel and transaction counterparties as nodes in relationship graph
7. Data included in Excel export on separate sheets

**Performance**: Adds ~10-30 seconds to overall query time

#### Flow 5 — Search Restore (15-300x Speedup)

1. User opens "📜 SAVED SEARCH HISTORY" expander
2. User filters by entity name, tags, or date range
3. User finds relevant saved search (e.g., "Xiaomi - 2026-03-04")
4. User clicks "📂 Restore" button
5. **Database** loads complete search results from SQLite
6. **UI** populates all tabs with restored data (< 2 seconds, **no API calls made**)
7. Banner displays: "📂 Displaying Restored Search - No API calls were made. Data as of [timestamp]"
8. User reviews all findings: sanctions, subsidiaries, financial intelligence, visualizations
9. User can add notes or tags to saved search
10. User exports restored search

**Performance**: < 2 seconds (15-300x faster than fresh search)

---

## 4. Key Design Decisions and Trade-offs

### 4.1 SQLite Database for Save/Restore

**Decision**: Use embedded SQLite database to store complete search results in JSON format.

**Rationale**:
- **Speed**: Sub-2-second restore times enable 15-300x speedup vs. re-running APIs
- **Simplicity**: No separate database server, minimal configuration
- **Portability**: Single-file database easy to backup and transfer
- **Sufficient Performance**: SQLite handles 50KB-5MB search objects efficiently

**Trade-offs**:
- **Single-user**: Not suitable for concurrent multi-user access (acceptable for desktop use case)
- **Storage Growth**: Database grows over time (~5MB per complex search)
- **Mitigation**: Provide search deletion and database maintenance tools

### 4.2 Fuzzy Name Matching with Levenshtein Distance

**Decision**: Use Levenshtein distance algorithm with configurable threshold (default 80%) for entity name matching.

**Rationale**:
- **Handles Variations**: Catches spelling differences, transliterations (Huawei vs 华为), abbreviations (Corp vs Corporation)
- **Transparency**: Displays match scores (0-100%) for user validation
- **Flexibility**: Users adjust threshold based on risk tolerance
- **Simple**: Deterministic algorithm, no ML training required

**Trade-offs**:
- **False Positives**: Lower thresholds (< 75%) may match unrelated entities
- **False Negatives**: Higher thresholds (> 90%) may miss legitimate matches
- **Mitigation**: Display match scores prominently, allow threshold adjustment per search

### 4.3 Waterfall Data Source Priority for Conglomerate Search

**Decision**: Query data sources in priority order: SEC EDGAR → OpenCorporates → Wikipedia → DuckDuckGo.

**Rationale**:
- **Reliability**: Prioritize authoritative sources (SEC regulatory filings) over public sources (Wikipedia)
- **Performance**: Stop searching once sufficient subsidiaries found
- **Cost**: SEC EDGAR and Wikipedia are free; OpenCorporates API is paid (optional)
- **Coverage**: Fallback ensures results even for non-public companies

**Trade-offs**:
- **Completeness**: May miss subsidiaries if higher-priority source has incomplete data
- **Mitigation**: Provide option to force query all sources (disable early stopping)

### 4.4 LLM-Powered Intelligence Reports

**Decision**: Use OpenAI/Anthropic LLM APIs to synthesize findings into human-readable intelligence reports.

**Rationale**:
- **Comprehension**: Stakeholders need actionable insights, not raw data dumps
- **Efficiency**: Automated synthesis saves analyst time
- **Context**: LLM can incorporate geopolitical context and explain sanctions significance
- **Quality**: State-of-the-art language models produce high-quality reports

**Trade-offs**:
- **Cost**: API calls cost $0.01-0.10 per report depending on length
- **Reliability**: LLM output quality varies, requires human review
- **Privacy**: Sensitive entity names sent to third-party API
- **Mitigation**: Make LLM features optional, provide data redaction options, cache reports in database

### 4.5 Streamlit for User Interface

**Decision**: Build web UI using Streamlit Python framework instead of traditional web frameworks (Flask/Django) or desktop GUI (Qt/Tkinter).

**Rationale**:
- **Rapid Development**: Streamlit enables fast UI prototyping with minimal code
- **Python Native**: Seamless integration with Python data processing libraries
- **Interactive**: Built-in support for charts, graphs, tables without JavaScript
- **Deployment**: Runs as local server accessible via browser (localhost:8501)

**Trade-offs**:
- **Performance**: Streamlit re-runs entire script on user interaction (can be slow for large datasets)
- **Customization**: Less control over UI/UX compared to React/Vue.js
- **Scalability**: Not ideal for high-traffic multi-user deployment
- **Mitigation**: Use Streamlit caching extensively, optimize script reruns

### 4.6 Selective Subsidiary Processing

**Decision**: Allow users to manually select which subsidiaries to analyze at each level instead of auto-processing all discovered entities.

**Rationale**:
- **Time Control**: Users balance thoroughness vs. speed based on risk assessment needs
- **Cost Control**: Avoid expensive API calls for irrelevant subsidiaries
- **Relevance**: User domain expertise determines which subsidiaries matter for their decision
- **Scalability**: Large conglomerates (100+ subsidiaries) become manageable

**Trade-offs**:
- **Manual Effort**: Requires user clicks and decision-making during search
- **Completeness Risk**: User may miss critical subsidiaries if selection is rushed
- **Mitigation**: Provide "Select All" option, show ownership % to guide selection

### 4.7 Combined Risk Scoring (5-Level System)

**Decision**: Assign 5-level risk classification (SAFE, LOW, MID, HIGH, VERY HIGH) based on name similarity, entity type match, and address match.

**Rationale**:
- **Simplicity**: Stakeholders need actionable risk levels, not raw match scores
- **Consistency**: Standardized scoring ensures uniform risk communication
- **Transparency**: Score components (name match %, type match, address match) displayed alongside level
- **Flexibility**: Users can adjust fuzzy threshold to shift risk levels

**Trade-offs**:
- **Oversimplification**: Nuanced risks may be lost in 5-level bucketing
- **Subjectivity**: Threshold boundaries (e.g., 85% = HIGH vs MID) are somewhat arbitrary
- **Mitigation**: Always display raw match scores alongside risk levels, explain scoring methodology in documentation

### 4.8 React/Next.js Frontend Architecture

**Decision**: Use Next.js (App Router) with TypeScript for the frontend instead of Streamlit.

**Rationale**:
- **Modern User Experience**: React provides component-based architecture with instant client-side interactions, smooth transitions, and real-time updates via WebSockets
- **Server-Side Rendering (SSR)**: Next.js App Router enables SSR/SSG for faster initial page loads and better SEO
- **Developer Experience**: TypeScript provides type safety, Next.js offers file-based routing, built-in API routes, and excellent tooling
- **Scalability**: Decoupling frontend from backend enables horizontal scaling, CDN deployment for static assets, and independent deployment cycles
- **Progressive Web App (PWA)**: React ecosystem supports offline-capable PWAs for accessing saved searches without connectivity
- **Real-Time Progress**: WebSocket integration for live progress updates during network/deep tier searches
- **Mobile Responsive**: React component libraries (shadcn/ui, Material-UI) provide mobile-first responsive design

**Trade-offs**:
- **Larger Bundle Size**: React/Next.js has larger initial bundle (~200-500KB gzipped) vs Streamlit's server-rendered pages
- **Separate Backend Requirement**: Must maintain separate REST API backend vs Streamlit's integrated approach
- **Increased Complexity**: Requires managing state, API client, error boundaries, loading states
- **Deployment Overhead**: Two deployment targets (frontend + backend) vs single Streamlit app

**Mitigation**:
- Use Next.js code splitting and lazy loading to minimize bundle size
- Implement service workers for offline caching of saved searches
- Use TypeScript and ESLint to catch errors early
- Document deployment process for both frontend and backend

### 4.9 Three-Tiered Research System

**Decision**: Users select research depth (base/network/deep) via slider interface before search execution.

**Rationale**:
- **User Control**: Gives users explicit control over time/cost vs. thoroughness trade-off based on decision importance
- **Expectation Management**: Clear upfront indication of search duration (30-60s / 2-5min / 5-15min) prevents user frustration
- **Cost Efficiency**: Users pay/wait only for depth needed - base tier sufficient for routine checks, deep tier for critical decisions
- **Transparency**: Each tier explicitly lists included features, eliminating confusion about what was analyzed
- **Upgrade Path**: Users can start with base tier, review results, then upgrade to network/deep if warranted
- **API Efficiency**: Tier selection prevents over-fetching - base tier doesn't trigger expensive conglomerate or financial flow queries

**Implementation**:
- **UI**: Horizontal slider with three discrete positions (left=base, center=network, right=deep)
- **Tier Indicators**: Each position shows tier name, estimated time, and expandable feature list
- **Search Execution**: Backend routes to `/api/search/{tier}` endpoints that execute only tier-appropriate features
- **Results Badge**: Results display tier badge (BASE/NETWORK/DEEP) so users know scope of analysis
- **Upgrade Button**: "Upgrade to Network/Deep Research" button on results page for post-search depth increase
- **Persistence**: User's last tier selection saved in preferences for session continuity

**Trade-offs**:
- **No Mid-Search Upgrade**: Users cannot upgrade tier during search execution (must abort and restart)
- **Tier Selection Burden**: Users must assess appropriate tier upfront without seeing preliminary results
- **Fixed Tier Boundaries**: Some users may want hybrid tiers (e.g., base + personnel without full conglomerate)

**Mitigation**:
- Provide clear tier comparison table with examples of use cases for each tier
- Allow post-search upgrade with one-click re-execution at higher tier
- Display estimated costs (API call counts) alongside time estimates for cost-conscious users
- Consider "auto-recommend tier" feature based on entity type (e.g., public companies → network tier)

---

## 5. Components and Responsibilities

### 5.1 Repository Structure

```
entity-background-research-agent/
├── README.md                       # System documentation
├── CLAUDE.md                       # Project guidelines
│
├── frontend/                       # React/Next.js application (NEW)
│   ├── app/                        # Next.js app router
│   │   ├── page.tsx                # Homepage with search interface
│   │   ├── layout.tsx              # Root layout with providers
│   │   ├── results/
│   │   │   └── [id]/
│   │   │       └── page.tsx        # Results dashboard
│   │   ├── history/
│   │   │   └── page.tsx            # Search history page
│   │   ├── settings/
│   │   │   └── page.tsx            # Settings page
│   │   └── api/                    # Optional Next.js API routes (proxy)
│   ├── components/
│   │   ├── ResearchTierSlider.tsx  # Base/Network/Deep selector
│   │   ├── SearchForm.tsx          # Entity name, country inputs
│   │   ├── ResultsDashboard.tsx    # Results display container
│   │   ├── NetworkGraph.tsx        # D3.js/Cytoscape network visualization
│   │   ├── IntelligenceReport.tsx  # LLM report viewer
│   │   ├── SavedSearches.tsx       # Search history manager
│   │   ├── ExportControls.tsx      # PDF/Excel export
│   │   ├── ProgressTracker.tsx     # Real-time progress via WebSocket
│   │   └── ui/                     # Reusable UI components (buttons, cards, etc.)
│   ├── lib/
│   │   ├── api-client.ts           # Backend API client (Axios)
│   │   ├── websocket.ts            # WebSocket connection manager
│   │   ├── types.ts                # TypeScript types/interfaces
│   │   └── utils.ts                # Utility functions
│   ├── hooks/
│   │   ├── useSearch.ts            # Search execution hook
│   │   ├── useProgress.ts          # Progress tracking hook
│   │   └── useHistory.ts           # Search history hook
│   ├── styles/
│   │   └── globals.css             # Global styles (dark cyber theme)
│   ├── public/                     # Static assets
│   ├── package.json                # Node dependencies
│   ├── tsconfig.json               # TypeScript configuration
│   ├── next.config.js              # Next.js configuration
│   └── .env.local                  # Environment variables (API base URL)
│
├── backend/                        # REST API server (NEW)
│   ├── app.py                      # Flask/FastAPI application entry point
│   ├── requirements.txt            # Python dependencies
│   ├── routes/
│   │   ├── auth_routes.py          # /api/auth/* endpoints
│   │   ├── search_routes.py        # /api/search/{tier} endpoints
│   │   ├── results_routes.py       # /api/results/{id} endpoints
│   │   ├── history_routes.py       # /api/history endpoints
│   │   ├── export_routes.py        # /api/export endpoints
│   │   └── settings_routes.py      # /api/settings endpoints
│   ├── middleware/
│   │   ├── auth.py                 # JWT authentication
│   │   ├── rate_limit.py           # Rate limiting
│   │   ├── cors.py                 # CORS configuration
│   │   └── error_handler.py        # Global error handling
│   ├── websocket/
│   │   └── progress_handler.py     # WebSocket progress updates
│   ├── models/
│   │   ├── request_models.py       # Pydantic request validation
│   │   └── response_models.py      # Pydantic response schemas
│   └── config.py                   # Backend configuration
│
├── core/                           # Application core layer (shared by backend)
│   ├── orchestrator.py             # Search orchestration engine
│   ├── query_processor.py          # Single entity query handler
│   ├── conglomerate_processor.py   # Multi-level conglomerate search
│   ├── reverse_processor.py        # Parent/sister discovery
│   ├── tier_processor.py           # Tier-specific search routing (NEW)
│   └── config.py                   # Configuration management
│
├── services/                       # Data integration services
│   ├── sanctions_service.py        # 10+ USA sanctions databases
│   ├── conglomerate_service.py     # SEC EDGAR, OpenCorporates, Wikipedia
│   ├── financial_intel_service.py  # SEC filing extraction (directors, shareholders)
│   ├── osint_service.py            # DuckDuckGo media intelligence
│   ├── name_matching_service.py    # Fuzzy matching with Levenshtein
│   └── risk_scoring_service.py     # 5-level risk assessment
│
├── intelligence/                   # AI/LLM layer
│   ├── report_generator.py         # LLM-powered report synthesis
│   ├── translation_service.py      # Non-English name translation (planned)
│   └── synthesis_engine.py         # Multi-source data combination
│
├── persistence/                    # Data persistence layer
│   ├── database.py                 # SQLite database operations
│   ├── search_repository.py        # Saved search CRUD operations
│   ├── cache_manager.py            # API response caching
│   └── settings_store.py           # User preferences persistence
│
├── integrations/                   # External API clients
│   ├── usa_sanctions_api.py        # OFAC, BIS, Treasury, etc.
│   ├── sec_edgar_api.py            # SEC EDGAR filing retrieval
│   ├── opencorporates_api.py       # OpenCorporates API client
│   ├── duckduckgo_api.py           # DuckDuckGo search client
│   ├── openai_api.py               # OpenAI LLM client
│   ├── anthropic_api.py            # Anthropic Claude LLM client
│   └── wikipedia_api.py            # Wikipedia API client
│
├── utils/                          # Shared utilities
│   ├── levenshtein.py              # Distance calculation
│   ├── text_processing.py          # Text normalization, cleaning
│   ├── date_utils.py               # Timestamp formatting
│   ├── error_handling.py           # Exception handling utilities
│   └── logging_config.py           # Logging configuration
│
├── tests/                          # Test suite
│   ├── frontend/                   # Frontend tests (Jest, React Testing Library)
│   ├── backend/                    # Backend API tests (pytest)
│   ├── unit/                       # Unit tests
│   ├── integration/                # Integration tests
│   ├── fixtures/                   # Test data
│   └── test_config.py              # Test configuration
│
└── docs/                           # Documentation
    ├── architecture.md             # Architecture documentation
    ├── api_reference.md            # REST API documentation (OpenAPI)
    ├── user_guide.md               # End-user documentation
    └── deployment.md               # Deployment guide (frontend + backend)
    └── deployment_guide.md         # Deployment instructions
```

### 5.2 Component Responsibilities

#### User Interface Components (`ui/`)

- **search_interface.py**: Renders entity name, country inputs; validates user input; triggers search execution
- **conglomerate_controls.py**: Manages depth selector (1-3 levels), ownership filters (100%, >50%, custom %), selective subsidiary processing UI
- **saved_searches.py**: Displays search history table; provides filter/sort controls; handles restore button clicks
- **visualization_tabs.py**: Renders Neo4j-style network graphs, geographic maps, hierarchical trees using Plotly/Streamlit
- **intelligence_report.py**: Displays LLM-generated reports with markdown formatting, executive summaries, risk assessments
- **export_controls.py**: Provides PDF, Excel, JSON export buttons; handles file downloads
- **settings_panel.py**: Manages fuzzy matching threshold slider, auto-save toggle, data source enable/disable checkboxes

#### Application Core (`core/`)

- **orchestrator.py**: Entry point for all search types; routes requests to appropriate processor; handles exceptions and logging
- **query_processor.py**: Handles single-entity sanctions screening; coordinates sanctions service, OSINT service, risk scoring; returns results object
- **conglomerate_processor.py**: Manages multi-level subsidiary discovery; implements recursive search with depth control; handles selective processing logic
- **reverse_processor.py**: Identifies parent company from subsidiary; discovers sister companies; coordinates data services
- **config.py**: Loads environment variables (API keys); provides configuration getters; validates settings

#### Data Integration Services (`services/`)

- **sanctions_service.py**: Queries 10+ USA sanctions databases in parallel; implements fallback logic for API failures; caches responses locally
- **conglomerate_service.py**: Queries SEC EDGAR (10-K, 20-F Exhibit 21.1), OpenCorporates, Wikipedia, DuckDuckGo in waterfall priority; de-duplicates subsidiaries
- **financial_intel_service.py**: Retrieves SEC filings (10-K, 20-F, DEF 14A); extracts directors, officers, shareholders, related party transactions using regex/LLM parsing
- **osint_service.py**: Conducts DuckDuckGo searches; distinguishes official sources (gov domains) from general media; returns top 10-20 results
- **name_matching_service.py**: Implements fuzzy matching with Levenshtein distance; applies configurable threshold; returns match score (0-100%)
- **risk_scoring_service.py**: Calculates combined risk level (SAFE, LOW, MID, HIGH, VERY HIGH) based on name match %, entity type match, address match

#### Intelligence Layer (`intelligence/`)

- **report_generator.py**: Calls OpenAI/Anthropic LLM APIs with structured prompts; synthesizes findings into executive summaries, sanctions analysis, recommendations; returns markdown report
- **translation_service.py** (planned): Translates non-English entity names to English using LLM; handles transliteration for Chinese, Russian, Arabic
- **synthesis_engine.py**: Combines data from multiple services (sanctions, financial, OSINT) into coherent intelligence object

#### Data Persistence (`persistence/`)

- **database.py**: Manages SQLite connection; creates tables (searches, metadata, settings); provides query helpers
- **search_repository.py**: CRUD operations for saved searches; stores complete search results as JSON; implements filter/sort queries for search history
- **cache_manager.py**: Caches API responses locally (file-based cache with TTL); reduces redundant API calls; implements cache invalidation
- **settings_store.py**: Persists user preferences (fuzzy threshold, auto-save, data source config) to SQLite settings table

#### Visualization Components (`visualization/`)

- **network_graph.py**: Generates Neo4j-style network graphs using Plotly; nodes = entities (parent, subsidiaries, directors, shareholders); edges = relationships (ownership, directorship, transactions)
- **geographic_map.py**: Plots entity locations on interactive map using Plotly/Mapbox; color-codes by risk level; shows jurisdiction exposure
- **tree_view.py**: Renders hierarchical subsidiary trees with expand/collapse; shows ownership % at each level; color-codes by sanctions status
- **chart_generator.py**: Creates bar charts (sanctions by database), pie charts (risk distribution), histograms (ownership %)

#### Export Modules (`export/`)

- **pdf_exporter.py**: Generates PDF reports using ReportLab; includes intelligence report, sanctions matches, visualizations; adds timestamp and source citations
- **excel_exporter.py**: Creates multi-sheet Excel workbooks using openpyxl; sheets: Summary, Sanctions, Subsidiaries, Directors, Shareholders, Transactions, Financial Intelligence
- **json_exporter.py**: Exports complete search results as JSON for API integration; includes metadata (timestamp, user, search parameters)

#### External Integrations (`integrations/`)

- **usa_sanctions_api.py**: HTTP clients for OFAC SDN, BIS Entity List, Treasury, State Department, DOD 1260H, FCC Covered List; implements retries, timeouts, error handling
- **sec_edgar_api.py**: Queries SEC EDGAR API for company filings by CIK; downloads filing text; implements rate limiting (10 requests/second per SEC guidelines)
- **opencorporates_api.py**: Queries OpenCorporates API for company data, control statements, officers; handles API key authentication; implements pagination
- **duckduckgo_api.py**: Performs web searches using DuckDuckGo API or scraping; extracts titles, URLs, snippets; filters by domain for official sources
- **openai_api.py / anthropic_api.py**: Calls LLM APIs with structured prompts; handles streaming responses; implements token limits and cost tracking

---

## 6. Interfaces and Integration

### 6.1 Interface Categories

1. **User ↔ React Frontend** (Browser → Next.js)
2. **React Frontend ↔ REST API Backend** (HTTPS/WebSocket)
3. **REST API Backend ↔ Application Core** (Python function calls)
4. **Application Core ↔ Data Services** (Python function calls)
5. **Data Services ↔ External APIs** (HTTP REST)
6. **Intelligence Layer ↔ LLM APIs** (HTTP REST)
7. **Application ↔ SQLite Database** (Python DB-API)
8. **Application ↔ File System** (Cache, exports)

### 6.1.1 Frontend ↔ Backend API (REST)

**Protocol**: HTTPS REST API with WebSocket for real-time updates

**Authentication**: JWT tokens via Authorization header
```
Authorization: Bearer <jwt_token>
```

**API Endpoints**:

#### Authentication
- `POST /api/auth/login`
  - Request: `{ "username": "string", "password": "string" }`
  - Response: `{ "token": "jwt_token", "expires_in": 3600 }`

#### Tier-Specific Search
- `POST /api/search/base` - Base tier search
  - Request:
    ```json
    {
      "entity_name": "Huawei Technologies",
      "country": "China",
      "fuzzy_matching": true,
      "fuzzy_threshold": 80
    }
    ```
  - Response:
    ```json
    {
      "search_id": "abc123",
      "tier": "base",
      "status": "completed",
      "risk_level": "VERY HIGH",
      "results": {
        "sanctions_matches": [...],
        "media_sources": [...],
        "intelligence_report": "...",
        "risk_score": 95
      },
      "timestamp": "2026-03-12T15:30:00Z",
      "duration_seconds": 45
    }
    ```

- `POST /api/search/network` - Network tier search
  - Request: Same as base + optional conglomerate parameters
    ```json
    {
      "entity_name": "Alibaba Group",
      "country": "China",
      "fuzzy_matching": true,
      "fuzzy_threshold": 80,
      "conglomerate_depth": 2,
      "ownership_threshold": 50
    }
    ```
  - Response: Includes `subsidiaries`, `directors`, `shareholders`, `relationship_graph`

- `POST /api/search/deep` - Deep tier search
  - Request: Same as network
  - Response: Includes `financial_flows`, `criminal_history`, `beneficial_ownership`

#### Results Management
- `GET /api/results/{search_id}` - Retrieve search results
  - Response: Full search result object

- `GET /api/history` - List user's saved searches
  - Query params: `?limit=50&offset=0&risk_level=HIGH&sort=timestamp_desc`
  - Response:
    ```json
    {
      "searches": [
        {
          "search_id": "abc123",
          "entity_name": "Huawei Technologies",
          "tier": "network",
          "risk_level": "VERY HIGH",
          "timestamp": "2026-03-12T15:30:00Z"
        }
      ],
      "total": 150,
      "limit": 50,
      "offset": 0
    }
    ```

- `DELETE /api/history/{search_id}` - Delete saved search
  - Response: `{ "success": true }`

#### Export
- `POST /api/export/{search_id}` - Export results
  - Request: `{ "format": "pdf|excel|json" }`
  - Response: Binary file download or `{ "download_url": "..." }`

#### Settings
- `GET /api/settings` - Get user settings
  - Response: `{ "fuzzy_threshold": 80, "auto_save": true, ... }`

- `PUT /api/settings` - Update user settings
  - Request: `{ "fuzzy_threshold": 85, "auto_save": false }`
  - Response: Updated settings object

#### Real-Time Progress (WebSocket)
- `WebSocket /ws/progress/{search_id}` - Real-time progress updates
  - Messages:
    ```json
    {
      "search_id": "abc123",
      "status": "in_progress",
      "current_step": "Searching corporate structure...",
      "progress_percent": 45,
      "estimated_remaining_seconds": 120
    }
    ```

**Error Handling**:
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Missing or invalid JWT token
- `404 Not Found` - Search ID not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server-side error

**Rate Limiting**:
- Base tier: 100 requests/hour per user
- Premium tier: 500 requests/hour per user
- Headers: `X-RateLimit-Remaining`, `X-RateLimit-Reset`

**CORS Configuration**:
- Allowed origins: Frontend domain (e.g., `https://app.entity-research.com`)
- Allowed methods: GET, POST, PUT, DELETE, OPTIONS
- Allowed headers: Authorization, Content-Type
- Credentials: true (for cookies/JWT)

### 6.2 Integration Details

#### USA Sanctions API Integration

**Databases**:
- OFAC SDN List (Office of Foreign Assets Control)
- BIS Entity List (Bureau of Industry and Security)
- Treasury Consolidated Sanctions List
- State Department Nonproliferation Sanctions
- Commerce Unverified List
- DOD Section 1260H List (Chinese Military Companies)
- FCC Covered List (National Security Telecom)

**Integration Pattern**:
- Parallel HTTP requests to all databases
- Response format: JSON (standardized across sources)
- Error handling: Fallback to local cached sanctions data if API unavailable
- Rate limiting: No limits for public APIs

#### SEC EDGAR API Integration

**Data Retrieved**:
- Company filings (10-K, 20-F, DEF 14A)
- Exhibit 21.1 (subsidiary lists)
- Proxy statements (directors, officers, compensation)

**Integration Pattern**:
- Query by CIK (Central Index Key) or company name
- Response format: HTML/SGML (requires parsing)
- Rate limiting: 10 requests/second (per SEC guidelines)
- User-Agent header: Required (system identification)

#### OpenCorporates API Integration

**Data Retrieved**:
- Company profile (jurisdiction, status, officers)
- Control statements (parent companies)
- Officer data (names, roles, appointment dates)

**Integration Pattern**:
- Requires API key (optional for system, falls back to Wikipedia if unavailable)
- Response format: JSON
- Rate limiting: 500 requests/day (free tier), higher for paid tiers
- Pagination: Handle large result sets

#### DuckDuckGo Search Integration

**Data Retrieved**:
- Media coverage (news articles, press releases)
- Official government announcements
- Public information about entities

**Integration Pattern**:
- Web scraping (DuckDuckGo does not provide official API)
- Distinguish official sources (.gov, .treasury.gov) from general media
- Extract: title, URL, snippet for top 10-20 results
- Rate limiting: Implement delays to avoid blocking

#### LLM API Integration (OpenAI/Anthropic)

**Data Sent**:
- Structured prompt with search findings (sanctions matches, subsidiary data, financial intelligence)
- System instructions for report format (executive summary, risk assessment, recommendations)

**Data Received**:
- Markdown-formatted intelligence report
- Risk-level recommendation with justification

**Integration Pattern**:
- HTTP POST to LLM API with JSON payload
- Streaming response for real-time display (optional)
- Token limits: Cap input at 8K tokens, output at 2K tokens
- Cost tracking: Log tokens used per API call

#### SQLite Database Integration

**Schema**:

```sql
-- Saved searches table
CREATE TABLE searches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_name TEXT NOT NULL,
    country TEXT,
    search_type TEXT NOT NULL,  -- 'single', 'conglomerate', 'reverse'
    results_json TEXT NOT NULL, -- Complete search results as JSON
    risk_level TEXT,            -- 'SAFE', 'LOW', 'MID', 'HIGH', 'VERY HIGH'
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    tags TEXT                   -- Comma-separated tags
);

-- Settings table
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Metadata index for fast searches
CREATE INDEX idx_entity_name ON searches(entity_name);
CREATE INDEX idx_timestamp ON searches(timestamp DESC);
CREATE INDEX idx_tags ON searches(tags);
```

**Integration Pattern**:
- Use Python `sqlite3` module (built-in)
- Store complete search results as JSON BLOB
- Restore by deserializing JSON from database
- Implement connection pooling for performance

---

## 7. API Specifications (Internal)

> Note: This system is a desktop application without external HTTP APIs. The specifications below describe internal Python function signatures for inter-component communication.

### 7.1 Query Processor API

```python
class QueryProcessor:
    def execute_single_entity_query(
        self,
        entity_name: str,
        country: str,
        enable_fuzzy: bool = True,
        fuzzy_threshold: int = 80
    ) -> SearchResults:
        """
        Execute single-entity sanctions screening.

        Args:
            entity_name: Name of entity to search
            country: Country of entity
            enable_fuzzy: Enable fuzzy name matching
            fuzzy_threshold: Match threshold (0-100)

        Returns:
            SearchResults object with sanctions matches, risk level, OSINT data

        Raises:
            QueryError: If search fails
        """
```

### 7.2 Conglomerate Processor API

```python
class ConglomerateProcessor:
    def execute_conglomerate_search(
        self,
        parent_company: str,
        depth: int = 2,
        ownership_filter: str = ">50%",  # "100%", ">50%", or "custom:XX%"
        selected_subsidiaries: Dict[int, List[str]] = None
    ) -> ConglomerateSearchResults:
        """
        Execute multi-level conglomerate search.

        Args:
            parent_company: Parent company name
            depth: Search depth (1, 2, or 3 levels)
            ownership_filter: Ownership threshold filter
            selected_subsidiaries: User-selected subsidiaries to process at each level

        Returns:
            ConglomerateSearchResults with subsidiaries, sanctions, financial intelligence

        Raises:
            ConglomerateError: If search fails
        """
```

### 7.3 Reverse Processor API

```python
class ReverseProcessor:
    def execute_reverse_search(
        self,
        subsidiary_name: str,
        include_parent: bool = True,
        include_sisters: bool = True
    ) -> ReverseSearchResults:
        """
        Discover parent company and sister entities.

        Args:
            subsidiary_name: Subsidiary name to reverse search
            include_parent: Include parent company in analysis
            include_sisters: Include sister companies in analysis

        Returns:
            ReverseSearchResults with parent, sisters, sanctions, relationships

        Raises:
            ReverseSearchError: If search fails or parent not found
        """
```

### 7.4 Sanctions Service API

```python
class SanctionsService:
    def screen_entity(
        self,
        entity_name: str,
        enable_fuzzy: bool = True,
        fuzzy_threshold: int = 80
    ) -> List[SanctionsMatch]:
        """
        Screen entity against 10+ USA sanctions databases.

        Args:
            entity_name: Entity name to screen
            enable_fuzzy: Enable fuzzy matching
            fuzzy_threshold: Match threshold (0-100)

        Returns:
            List of SanctionsMatch objects with source, match score, details
        """
```

### 7.5 Search Repository API

```python
class SearchRepository:
    def save_search(
        self,
        entity_name: str,
        search_type: str,
        results: Dict,
        risk_level: str,
        notes: str = "",
        tags: List[str] = None
    ) -> int:
        """
        Save complete search results to database.

        Args:
            entity_name: Entity name searched
            search_type: 'single', 'conglomerate', or 'reverse'
            results: Complete search results as dictionary
            risk_level: 'SAFE', 'LOW', 'MID', 'HIGH', 'VERY HIGH'
            notes: User notes
            tags: User tags

        Returns:
            Search ID
        """

    def restore_search(self, search_id: int) -> Dict:
        """
        Restore saved search results from database.

        Args:
            search_id: ID of saved search

        Returns:
            Complete search results dictionary

        Raises:
            SearchNotFoundError: If search ID does not exist
        """
```

---

## 8. Third-Party and Backing Services

### 8.1 External Data Sources

| Service | Purpose | Auth Required | Cost | Rate Limits |
|---------|---------|---------------|------|-------------|
| **USA Sanctions API** | OFAC, BIS, Treasury, State, DOD, FCC sanctions lists | No | Free | None |
| **SEC EDGAR** | Company filings (10-K, 20-F, DEF 14A) | No | Free | 10 req/sec |
| **OpenCorporates** | Global corporate registry data | API Key (optional) | Freemium (500 req/day free, paid tiers available) | 500/day (free), higher (paid) |
| **DuckDuckGo** | Media intelligence and OSINT | No | Free | Self-imposed delays to avoid blocking |
| **Wikipedia API** | Corporate structure data | No | Free | Reasonable use policy |
| **OpenAI GPT-4** | Intelligence report generation | API Key | $0.03-0.10 per report | Tier-based (5K req/day for Tier 1) |
| **Anthropic Claude** | Intelligence report generation (alternative) | API Key | $0.02-0.08 per report | Tier-based |

### 8.2 Planned Integrations (Future Phases)

| Service | Purpose | Phase | Estimated Cost |
|---------|---------|-------|----------------|
| **ImportYeti** | US import/export trade data (Bills of Lading) | Phase 3 | Free tier available, paid for bulk |
| **USAspending.gov** | Federal procurement and subcontractor data | Phase 3 | Free |
| **Companies House UK** | UK PSC (Persons with Significant Control) | Phase 4 | Free |
| **Open Ownership Register** | Beneficial ownership data (BODS standard) | Phase 4 | Free |
| **OCCRP Aleph** | Offshore leaks (Panama Papers, Pandora Papers) | Phase 4 | Free (public data) |
| **LittleSis** | Director interlocks, political connections | Phase 4 | Free (public data) |

### 8.3 Tooling and Runtime Dependencies

- **Python 3.10+**: Programming language
- **Streamlit**: Web UI framework
- **SQLite**: Embedded database
- **Plotly**: Interactive visualizations
- **ReportLab**: PDF generation
- **openpyxl**: Excel file generation
- **requests**: HTTP client for API calls
- **beautifulsoup4**: HTML parsing for SEC filings
- **python-Levenshtein**: Fast Levenshtein distance calculation
- **openai / anthropic**: LLM API clients

---

## 9. Security Architecture Considerations

### 9.1 Security Controls Present

1. **API Key Management**: Store API keys in environment variables (`.env` file), never hardcoded
2. **Input Validation**: Sanitize user inputs (entity names, countries) to prevent injection attacks
3. **Rate Limiting**: Respect external API rate limits to avoid service blocking
4. **Data Privacy**: LLM API calls can be disabled; provide option to redact sensitive data before sending to LLM
5. **Local Storage**: All data stored locally in SQLite database (no cloud storage by default)
6. **Audit Trail**: All searches timestamped and logged for compliance review

### 9.2 Security Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| **API Key Exposure** | Use `.env` file excluded from git; provide `.env.example` template; encrypt API keys at rest (future) |
| **Sensitive Data in LLM Calls** | Make LLM features optional; provide entity name redaction option; document data-sharing policies |
| **SQL Injection** | Use parameterized queries for all database operations; validate user inputs |
| **Dependency Vulnerabilities** | Regularly update dependencies; use `pip-audit` to scan for known vulnerabilities |
| **Unencrypted Database** | Database stored locally with file system permissions; implement encryption at rest (future) |
| **Man-in-the-Middle (API Calls)** | Use HTTPS for all external API calls; verify SSL certificates |

### 9.3 Compliance Considerations

- **GDPR**: System processes entity names (may include individuals); provide data deletion functionality
- **Export Control**: Sanctions screening supports compliance with US export control regulations
- **Audit Requirements**: Timestamp all searches; log all data sources queried; include source citations in reports

---

## 10. Reliability, Scalability, and Operations

### 10.1 Reliability Patterns

- **Graceful Degradation**: If OpenCorporates API unavailable, fallback to Wikipedia/web search for conglomerate data
- **Local Caching**: Cache sanctions lists locally; use cached data if API calls fail
- **Error Handling**: Catch and log all exceptions; display user-friendly error messages
- **Retry Logic**: Retry failed API calls with exponential backoff (max 3 retries)
- **Progress Indicators**: Display real-time progress for long-running conglomerate searches
- **Auto-Save**: Automatically save search results to database upon completion to prevent data loss

### 10.2 Scalability Considerations

**Frontend Scalability**:
- **Static Asset Hosting**: Deploy Next.js static assets to CDN (CloudFront, Vercel Edge Network) for global low-latency access
- **Code Splitting**: Next.js automatic code splitting ensures users only download code for pages they visit
- **Image Optimization**: Next.js Image component provides automatic optimization, lazy loading, and responsive images
- **Client-Side Caching**: React Query or SWR for client-side API response caching, reducing backend load
- **Bundle Size**: Monitor bundle size; keep below 500KB gzipped; use dynamic imports for heavy components (D3.js, PDF viewer)

**Backend Scalability**:
- **Horizontal Scaling**: Deploy multiple API backend instances behind load balancer (AWS ALB, nginx) to handle concurrent users
- **Async Processing**: Long-running searches (network/deep tier) use task queue (Celery + Redis) for background processing
  - Client receives `search_id` immediately
  - Backend processes search asynchronously
  - Client polls `/api/results/{search_id}` or receives WebSocket updates
- **Database Sharding**: (Future) Partition SQLite databases by user or date range for multi-tenant deployments
- **Database Growth**: SQLite database grows ~5MB per complex search; implement search deletion, database vacuuming, and archival
- **Connection Pooling**: Use connection pools for database and external API connections to handle concurrent requests
- **API Rate Limits**: Respect rate limits (SEC EDGAR: 10 req/sec, OpenCorporates: 500 req/day free); implement queuing and throttling
- **Memory Usage**: Large conglomerate searches (100+ subsidiaries) may consume 500MB-2GB RAM; implement streaming for very large result sets

**WebSocket Scalability**:
- **Redis Pub/Sub**: Use Redis for WebSocket message brokering across multiple backend instances
- **Connection Management**: Limit concurrent WebSocket connections per user; implement heartbeat/ping-pong for connection health
- **Graceful Fallback**: If WebSocket fails, client falls back to HTTP polling for progress updates

**Caching Strategy**:
- **API Gateway Caching**: Cache GET requests (results, history) at API gateway/CDN for 60 seconds
- **Application-Level Caching**: Cache sanctions lists, SEC filings, OpenCorporates results in Redis with 24-hour TTL
- **CDN Caching**: Cache frontend static assets with long TTL (1 year); use cache-busting via file hashes

### 10.3 Observability and Auditability

- **Logging**: Structured logs with levels (DEBUG, INFO, WARNING, ERROR) written to `~/.entity_research/logs/`
- **Metrics**: Track query performance (time per search type), API call counts, database size
- **Audit Trail**: All searches saved with timestamp, user (future), search parameters, results
- **Monitoring**: (Future) Integrate with monitoring tools (Prometheus, Grafana) for production deployments

### 10.4 Operational Runbook

**Installation**:
1. Install Python 3.10+
2. Clone repository: `git clone <repo-url>`
3. Install dependencies: `pip install -r requirements.txt`
4. Configure API keys: Copy `.env.example` to `.env`, add OpenAI/Anthropic API keys
5. Run application: `streamlit run app.py`

**Backup**:
- Database: Copy `~/.entity_research/searches.db` to backup location
- Settings: Included in database
- Exports: Saved to `~/Downloads/entity_research_exports/` by default

**Maintenance**:
- Update dependencies: `pip install --upgrade -r requirements.txt`
- Vacuum database: Run `VACUUM` SQL command periodically to reclaim space
- Clear cache: Delete `~/.entity_research/cache/` directory
- Review logs: Check `~/.entity_research/logs/` for errors

---

## 11. Configuration and Environment Model

### 11.1 Environment Variables (`.env` file)

```bash
# LLM API Keys (required for intelligence reports)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# OpenCorporates API (optional, falls back to Wikipedia if not provided)
OPENCORPORATES_API_KEY=...

# Database Configuration
DATABASE_PATH=~/.entity_research/searches.db
CACHE_DIR=~/.entity_research/cache/
LOG_DIR=~/.entity_research/logs/

# Application Settings
AUTO_SAVE_ENABLED=true
DEFAULT_FUZZY_THRESHOLD=80
DEFAULT_OWNERSHIP_FILTER=>50%
DEFAULT_CONGLOMERATE_DEPTH=2

# LLM Configuration
LLM_PROVIDER=openai  # or 'anthropic'
LLM_MODEL=gpt-4-turbo
LLM_MAX_TOKENS=2000
LLM_TEMPERATURE=0.3

# API Rate Limiting
SEC_EDGAR_RATE_LIMIT=10  # requests per second
OPENCORPORATES_RATE_LIMIT=500  # requests per day (free tier)
```

### 11.2 User Settings (Stored in Database)

Settings configurable via UI settings panel:
- **Fuzzy Matching Threshold**: 0-100% (default: 80%)
- **Auto-Save**: Enable/disable automatic search saving (default: enabled)
- **Data Source Preferences**: Enable/disable specific sanctions databases, conglomerate sources
- **LLM Provider**: OpenAI or Anthropic (default: OpenAI)
- **Export Format**: PDF, Excel, or JSON (default: PDF)

---

## 12. Known Constraints and Future Enhancements

### 12.1 Current Constraints (v2.1.0)

1. **USA-Centric Sanctions**: Only queries USA sanctions databases (no EU, UN sanctions)
2. **Limited Trade Data**: No trade intelligence (Bills of Lading) - planned for Phase 3
3. **No Beneficial Ownership**: Limited offshore beneficial ownership discovery - planned for Phase 4
4. **English-Only**: Non-English entity names require manual translation - LLM translation planned
5. **Single-User**: No multi-user collaboration features (shared searches, approval workflows)
6. **No Real-Time Monitoring**: Cannot set alerts for changes in sanctions status - planned for Phase 5
7. **No Batch Processing**: Cannot submit multiple entities in single session - planned for Phase 2
8. **Limited Personnel Screening**: No individual criminal records or professional sanctions - planned for Phase 5

### 12.2 Recommended Enhancements by Phase

#### Phase 2 (Q2 2026) — Enhanced Usability

**Features**:
1. **Batch Entity Processing** (US-2.7)
   - Submit multiple entity names (CSV upload or text area)
   - Process sequentially with progress tracking
   - Generate summary report showing all entities with risk levels
   - Export batch results as single Excel file

2. **Search Comparison** (US-2.8)
   - Select two saved searches to compare side-by-side
   - Highlight differences (new sanctions, changed risk levels)
   - Export comparison report as PDF

3. **Enhanced UI/UX**
   - Dark mode support
   - Keyboard shortcuts for common actions
   - Advanced search history filters (date ranges, risk level, tags)
   - Collapsible/expandable sections for large datasets

**Effort**: 3-4 weeks
**Dependencies**: None
**Value**: Improves analyst productivity for routine screening workflows

---

#### Phase 3 (Q3 2026) — Trade and Financial Intelligence

**Features**:
1. **ImportYeti Integration** (US-3.6)
   - Extract Bills of Lading from US sea shipments
   - Identify foreign suppliers and consignees
   - Calculate estimated capital outflows
   - Screen suppliers against sanctions lists

2. **Trade-Based Money Laundering Detection** (US-3.7)
   - Flag over-invoicing/under-invoicing patterns
   - Detect mismatched HS codes and product descriptions
   - Highlight high-risk jurisdictions in trade flows

3. **USAspending.gov Procurement Integration** (US-3.8, US-3.9)
   - Extract federal contracts where entity is prime contractor
   - Identify subcontractor B2B vendor network
   - Screen subcontractors against sanctions lists

4. **Enhanced Transaction Analysis** (US-3.5)
   - Calculate transaction summary statistics
   - Identify concentrated counterparties (>50% volume)
   - Time series visualization of transaction volumes

**Effort**: 6-8 weeks
**Dependencies**: API keys for ImportYeti (optional, free tier available)
**Value**: Provides 360-degree financial flow mapping for deep investigations

---

#### Phase 4 (Q4 2026) — Advanced Corporate Intelligence

**Features**:
1. **Director/Officer Network Pivoting** (Journey 2, Phase 2)
   - Extract directors/officers from OpenCorporates, Companies House UK
   - Perform Officer Pivot Search to find all companies where individual holds positions
   - Identify sister companies via shared management (≥2 overlapping directors)
   - Display "Management Network" tab with director-company graphs

2. **Digital Infrastructure Correlation** (Journey 2, Phase 3)
   - WHOIS lookup and Reverse WHOIS search (shared registrant details)
   - ASN/IP mapping and Reverse DNS (find domains on same IP)
   - Technology stack analysis (shared Google Analytics, AdSense IDs)
   - Display "Infrastructure Correlation" tab with confidence scores

3. **Offshore Beneficial Ownership** (Journey 2, Phase 4)
   - Query OCCRP Aleph (Panama Papers, Pandora Papers)
   - Query Open Ownership Register (BODS standard)
   - Query Companies House UK PSC (Persons with Significant Control)
   - Trace UBO (Ultimate Beneficial Owner) chains
   - Calculate Opacity Score (0-100, higher = more opaque)
   - Flag high-risk patterns (offshore + nominee directors + bearer shares)

4. **Advanced OSINT Reconnaissance** (Journey 2, Phase 5)
   - Google Dorking for exposed documents (org charts, internal PDFs)
   - SpiderFoot integration for automated OSINT scraping
   - LittleSis integration for political connections and board interlocks

**Effort**: 8-10 weeks
**Dependencies**: API access to OCCRP Aleph, Open Ownership, Companies House UK
**Value**: Uncovers hidden corporate relationships beyond official disclosures; critical for high-stakes due diligence

---

#### Phase 5 (Q1 2027) — Individual Screening and Monitoring

**Features**:
1. **Individual Criminal Background Checks** (Journey 6)
   - Automatic individual discovery from SEC filings (directors, officers, UBOs)
   - Multi-country criminal records screening (US, UK, EU, Singapore, China)
   - Sex offender registry checks (US NSOPW, UK ViSOR equivalents)
   - Role-specific screening (CFO → FinCEN, SEC, FINRA; Medical → OIG)
   - Government debarment lists (SAM.gov, UN, World Bank)
   - Standalone individual search mode

2. **EU and UN Sanctions Integration** (US-1.7)
   - EU Consolidated Sanctions List API
   - UN Security Council Sanctions List API
   - Toggle to enable/disable EU/UN screening
   - Display jurisdiction in match results (USA/EU/UN)

3. **Machine Learning Enhanced Name Matching** (US-1.8)
   - User feedback on match accuracy (Confirm/Reject buttons)
   - Train ML model on validated matches
   - Improve scoring accuracy over time (target >90% precision)

4. **Real-Time Monitoring and Alerts**
   - Set alerts for saved searches (email when sanctions status changes)
   - Periodic re-screening schedules (daily, weekly, monthly)
   - Dashboard view showing all monitored entities with status indicators

**Effort**: 10-12 weeks
**Dependencies**: Access to criminal records databases (may require subscriptions), ML training data
**Value**: Comprehensive personnel risk assessment; proactive monitoring reduces compliance risk

---

## 13. Implementation Roadmap

### Phase 1: Modernized Platform with Tiered Research (v3.0.0 - In Progress)

**Status**: 🚧 Design Phase → Implementation

**Major Architecture Changes**:
- **React/Next.js Frontend**: Modern TypeScript web application with component-based UI
- **REST API Backend**: Flask/FastAPI backend with OpenAPI documentation
- **Three-Tiered Research System**: User-selectable research depth (base/network/deep)
- **Real-Time Progress**: WebSocket integration for live updates during network/deep searches
- **Decoupled Architecture**: Frontend and backend deployed independently for scalability

**Core Platform Features** (from v2.1.0):
- Multi-source sanctions screening (10+ databases)
- Fuzzy name matching with configurable thresholds
- Conglomerate search (1-3 levels deep)
- Ownership filtering (100%, >50%, custom %)
- Reverse search (parent & sister discovery)
- SEC EDGAR financial intelligence extraction
- OSINT media intelligence (DuckDuckGo)
- Combined risk scoring (5-level system)
- Interactive relationship visualizations (now D3.js/Cytoscape in React)
- Save/restore functionality (15-300x speedup)
- LLM-powered intelligence reports
- Multi-format export (PDF, Excel, JSON)

**New Phase 1 Deliverables**:

1. **React/Next.js Frontend Application**
   - Research tier slider component (base/network/deep selection)
   - Search interface with tier-aware feature display
   - Results dashboard with tier badge indicators
   - Network graph visualizer (D3.js or Cytoscape.js)
   - Real-time progress tracker with WebSocket integration
   - Saved search history with filtering/sorting
   - Settings panel with user preferences
   - Responsive design (desktop, tablet, mobile)
   - Dark cyber theme UI matching existing design
   - PWA support for offline saved search access

2. **REST API Backend**
   - Flask or FastAPI application with OpenAPI 3.0 documentation
   - JWT authentication middleware
   - Rate limiting (100 req/hr base, 500 req/hr premium)
   - Tier-specific endpoints: `/api/search/{base|network|deep}`
   - Results management endpoints: `/api/results/{id}`, `/api/history`
   - Export endpoints: `/api/export/{search_id}`
   - Settings endpoints: `/api/settings`
   - WebSocket handler: `/ws/progress/{search_id}`
   - CORS configuration for frontend domain
   - Pydantic request/response validation
   - Error handling and logging

3. **Base Research Tier Implementation**
   - Sanctions screening (10+ databases)
   - OSINT media intelligence (DuckDuckGo)
   - Risk scoring (5-level system)
   - LLM intelligence report generation
   - PDF/Excel/JSON export
   - Performance target: 30-60 seconds

4. **Network Research Tier Implementation**
   - All Base tier features
   - Conglomerate search (SEC EDGAR, OpenCorporates, Wikipedia)
   - Director and shareholder extraction
   - Cross-entity sanctions screening
   - Network relationship graph generation
   - Multi-sheet Excel export
   - Performance target: 2-5 minutes

5. **Deep Research Tier Implementation**
   - All Network tier features
   - Financial flow mapping (SEC related party transactions)
   - Trade data integration (ImportYeti - Phase 3 feature pulled forward)
   - Criminal history checks (planned)
   - Beneficial ownership tracing (planned)
   - Comprehensive multi-layer export
   - Performance target: 5-15 minutes

**User Journeys Supported**:
- Journey 0: Selecting Research Tier (NEW)
- Journey 1: Basic Sanctions Screening (Base tier)
- Journey 2: Conglomerate Investigation (Network tier)
- Journey 3: Reverse Search (Network tier)
- Journey 4: Financial Flow Mapping (Deep tier - partial)
- Journey 5: Search Retrieval and Monitoring (All tiers)

**Success Metrics**:
- Frontend bundle size: < 500KB gzipped
- Base tier search: 30-60 seconds
- Network tier search: 2-5 minutes
- Deep tier search: 5-15 minutes
- API response time: < 200ms for GET endpoints
- WebSocket latency: < 100ms for progress updates
- Mobile responsiveness: Lighthouse score > 90

**Deployment Architecture**:
- Frontend: Deployed to Vercel/Netlify with CDN
- Backend: Deployed to AWS EC2/ECS or similar (Docker container)
- Database: SQLite (backend-local) or PostgreSQL (multi-instance)
- WebSocket: Redis Pub/Sub for multi-instance support

---

### Phase 2: Enhanced Usability (Q2 2026)

**Duration**: 3-4 weeks
**Team Size**: 2 developers, 1 QA

**Features**:
- Batch entity processing (CSV upload, multi-entity screening)
- Search comparison (side-by-side, difference highlighting)
- Enhanced UI/UX (dark mode, keyboard shortcuts, advanced filters)
- Performance optimizations (caching improvements, database indexing)

**Success Metrics**:
- Batch processing: 50 entities in < 30 minutes
- Search comparison: < 5 seconds to compute differences
- UI responsiveness: < 500ms for all user interactions

**Deliverables**:
- Updated Streamlit UI with batch processing interface
- Search comparison module
- Performance test suite
- User documentation updates

---

### Phase 3: Trade and Financial Intelligence (Q3 2026)

**Duration**: 6-8 weeks
**Team Size**: 3 developers, 1 data analyst, 1 QA

**Features**:
- ImportYeti integration (Bills of Lading, supplier identification)
- TBML detection (over/under-invoicing, HS code mismatches)
- USAspending.gov procurement integration (subcontractor networks)
- Enhanced transaction analysis (statistics, time series)

**Success Metrics**:
- Trade data extraction: < 60 seconds per entity
- TBML detection accuracy: > 85% precision on test dataset
- Procurement data coverage: All US federal contracts retrieved

**Deliverables**:
- Trade intelligence service (ImportYeti client)
- TBML detection algorithms
- Procurement intelligence service (USAspending.gov client)
- New UI tabs for trade and procurement data
- Updated Excel export with trade/procurement sheets

---

### Phase 4: Advanced Corporate Intelligence (Q4 2026)

**Duration**: 8-10 weeks
**Team Size**: 4 developers, 1 data scientist, 1 QA

**Features**:
- Director/officer network pivoting (interlocking directorates)
- Digital infrastructure correlation (WHOIS, reverse DNS, shared analytics)
- Offshore beneficial ownership tracing (OCCRP Aleph, Open Ownership)
- Advanced OSINT reconnaissance (Google Dorking, SpiderFoot, LittleSis)

**Success Metrics**:
- Director pivot: Find all companies for 20+ directors in < 90 seconds
- Infrastructure correlation: 95% confidence for shared Google Analytics IDs
- UBO tracing: Identify UBOs for 80% of offshore entities
- OSINT coverage: 100+ data points per entity from advanced reconnaissance

**Deliverables**:
- Management network analysis module
- Infrastructure correlation engine
- Beneficial ownership tracing service
- OSINT reconnaissance module (Google Dorking, SpiderFoot, LittleSis clients)
- New UI tabs: Management Network, Infrastructure Correlation, Beneficial Ownership
- Updated multi-sheet Excel export with new data

---

### Phase 5: Individual Screening and Monitoring (Q1 2027)

**Duration**: 10-12 weeks
**Team Size**: 4 developers, 1 ML engineer, 1 QA

**Features**:
- Individual criminal background checks (multi-country)
- Sex offender registry screening
- Role-specific professional sanctions (FinCEN, SEC, FINRA, OIG)
- Government debarment lists (SAM.gov, UN, World Bank)
- EU and UN sanctions integration
- ML-enhanced name matching
- Real-time monitoring and alerts

**Success Metrics**:
- Individual screening coverage: 5+ countries (US, UK, EU, Singapore, China)
- Criminal records accuracy: > 95% match precision
- ML name matching improvement: +10% precision vs. Levenshtein baseline
- Alert latency: < 24 hours from sanctions list update to user notification

**Deliverables**:
- Individual screening module (criminal records, sex offender registries)
- Role-specific screening services (FinCEN, SEC, FINRA, OIG clients)
- EU/UN sanctions integration
- ML name matching model (training pipeline, inference engine)
- Real-time monitoring service (periodic re-screening, email alerts)
- Standalone individual search interface
- Updated intelligence reports with personnel risk section

---

## 14. Appendix A — Data Models

### SearchResults (Single Entity Query)

```python
@dataclass
class SearchResults:
    entity_name: str
    country: str
    timestamp: datetime
    risk_level: str  # 'SAFE', 'LOW', 'MID', 'HIGH', 'VERY HIGH'
    sanctions_matches: List[SanctionsMatch]
    osint_results: List[OSINTResult]
    intelligence_report: str  # LLM-generated markdown report
    search_parameters: Dict  # fuzzy_threshold, etc.
```

### SanctionsMatch

```python
@dataclass
class SanctionsMatch:
    database: str  # 'OFAC SDN', 'BIS Entity List', etc.
    matched_name: str
    match_score: float  # 0-100%
    entity_type: str  # 'Individual', 'Entity', 'Aircraft', etc.
    address: str
    country: str
    program: str  # Sanctions program (e.g., 'IRAN', 'RUSSIA', 'SDGT')
    source_url: str
```

### ConglomerateSearchResults

```python
@dataclass
class ConglomerateSearchResults:
    parent_company: str
    subsidiaries: Dict[int, List[Subsidiary]]  # Level → List of subsidiaries
    total_subsidiaries: int
    total_sanctions_matches: int
    financial_intelligence: List[FinancialIntelligence]
    relationship_graph: Dict  # Nodes and edges for visualization
    risk_summary: Dict  # Risk distribution across subsidiaries
    intelligence_report: str
```

### Subsidiary

```python
@dataclass
class Subsidiary:
    name: str
    level: int  # 1, 2, or 3
    ownership_percentage: float  # 0-100%
    jurisdiction: str
    source: str  # 'SEC EDGAR', 'OpenCorporates', 'Wikipedia', 'DuckDuckGo'
    sanctions_matches: List[SanctionsMatch]
    risk_level: str
```

### FinancialIntelligence

```python
@dataclass
class FinancialIntelligence:
    entity_name: str
    filing_type: str  # '10-K', '20-F', 'DEF 14A'
    accession_number: str
    directors_officers: List[Person]
    major_shareholders: List[Shareholder]
    related_party_transactions: List[Transaction]
```

---

## 15. Appendix B — Sample Intelligence Report

```markdown
# Intelligence Report: Huawei Technologies Co., Ltd.

**Generated**: 2026-03-12 14:35:21 UTC
**Risk Level**: VERY HIGH
**Search Type**: Conglomerate (3 levels deep)

---

## Executive Summary

Huawei Technologies Co., Ltd. (China) is a telecommunications equipment manufacturer with significant sanctions exposure across multiple USA databases. The entity appears on the BIS Entity List, DOD Section 1260H (Chinese Military Companies), and FCC Covered List. Conglomerate analysis identified 87 subsidiaries across 3 levels, with 12 subsidiaries (14%) having direct or indirect sanctions matches.

**Key Risk Indicators**:
- ✅ Multiple USA sanctions listings (BIS, DOD, FCC)
- ✅ High-risk jurisdiction (China)
- ✅ Subsidiaries with independent sanctions exposure
- ✅ Directors with ties to Chinese military
- ⚠️ Complex corporate structure with offshore entities

**Recommendation**: **VERY HIGH RISK — Do Not Engage**. Association with Huawei poses significant compliance and reputational risks given extensive USA sanctions restrictions.

---

## Sanctions Analysis

### Primary Entity

**Huawei Technologies Co., Ltd.**
- **BIS Entity List**: Listed (Match Score: 98%)
  - Reason: Foreign policy/national security concerns
  - Restrictions: Export controls on US technology
  - Date Added: 2019-05-16

- **DOD Section 1260H**: Listed (Match Score: 100%)
  - Designation: Chinese Military Company
  - Implications: Investment restrictions for US persons

- **FCC Covered List**: Listed (Match Score: 100%)
  - Reason: National security threat to communications networks
  - Implications: Prohibited from receiving USF subsidies

### Subsidiary Sanctions Exposure

- **Huawei Device (Shenzhen) Co., Ltd.** (L1 Subsidiary, 100% owned)
  - BIS Entity List (Match Score: 95%)

- **HiSilicon Technologies Co., Ltd.** (L1 Subsidiary, 100% owned)
  - BIS Entity List (Match Score: 92%)
  - Specialty: Semiconductor design

- **Huawei Marine Networks Co., Ltd.** (L2 Subsidiary, 51% owned)
  - Potential national security concern (submarine cable infrastructure)

---

## Corporate Structure

**Total Subsidiaries Discovered**: 87
- **Level 1**: 23 direct subsidiaries
- **Level 2**: 46 sub-subsidiaries
- **Level 3**: 18 sub-sub-subsidiaries

**Ownership Distribution**:
- 100% owned: 68 subsidiaries (78%)
- >50% owned: 14 subsidiaries (16%)
- <50% owned: 5 subsidiaries (6%)

**Geographic Distribution**:
- China: 72 subsidiaries (83%)
- Hong Kong: 8 subsidiaries (9%)
- Offshore (Cayman Islands, BVI): 4 subsidiaries (5%)
- Other: 3 subsidiaries (3%)

**High-Risk Subsidiaries** (sanctions matches or strategic concerns):
1. Huawei Device (Shenzhen) Co., Ltd. — BIS Entity List
2. HiSilicon Technologies Co., Ltd. — BIS Entity List
3. Huawei Marine Networks Co., Ltd. — Submarine cable infrastructure
4. [Additional 9 subsidiaries...]

---

## Financial Intelligence (SEC EDGAR)

*Note: Huawei is not SEC-registered. Limited public financial data available.*

**Directors & Officers** (from public sources):
- Ren Zhengfei (Founder, CEO) — Former PLA engineer
- Meng Wanzhou (CFO) — Subject of US extradition request
- [Additional personnel...]

**Sanctions Cross-Check**:
- Meng Wanzhou: No direct sanctions listing, but subject to US criminal charges

---

## Media Intelligence

### Official Sources (Government Announcements)

1. **US Department of Commerce** (2019-05-16)
   - "Commerce Department Adds Huawei to Entity List"
   - URL: commerce.gov/news/...

2. **US Department of Defense** (2020-06-24)
   - "DOD Releases List of Chinese Military Companies"
   - URL: defense.gov/...

### General Media Coverage

1. **Reuters** (2024-01-15)
   - "Huawei reports 9% revenue growth despite US sanctions"

2. **Financial Times** (2025-11-22)
   - "Huawei 5G equipment banned in UK, citing security risks"

---

## Risk Assessment

| Factor | Level | Justification |
|--------|-------|---------------|
| **Sanctions Exposure** | VERY HIGH | Multiple USA sanctions listings (BIS, DOD, FCC) |
| **Subsidiary Risk** | HIGH | 14% of subsidiaries have sanctions exposure |
| **Geographic Risk** | HIGH | 83% of operations in China, high-risk jurisdiction |
| **Ownership Opacity** | MEDIUM | Some offshore entities (Cayman Islands, BVI) |
| **Personnel Risk** | MEDIUM | Key executives with military ties, CFO under US indictment |
| **Reputational Risk** | VERY HIGH | Extensive negative media coverage, government warnings |

**Overall Risk Level**: **VERY HIGH**

---

## Recommendations

1. **Do Not Engage**: Given extensive USA sanctions listings, engagement with Huawei poses significant compliance and legal risks for US persons and entities.

2. **Avoid Subsidiaries**: Recommend avoiding engagement with all Huawei subsidiaries, particularly those with direct sanctions listings (Huawei Device, HiSilicon).

3. **Monitor Updates**: USA export controls and sanctions lists are subject to change. Recommend periodic re-screening if engagement becomes necessary in future.

4. **Consult Legal Counsel**: If engagement is unavoidable for specific use cases, consult specialized export control attorneys before proceeding.

---

## Sources

- USA Sanctions Databases: OFAC, BIS, DOD, FCC (accessed 2026-03-12)
- Corporate Structure: OpenCorporates, Wikipedia (accessed 2026-03-12)
- Media Intelligence: DuckDuckGo search (accessed 2026-03-12)
- Analysis: AI synthesis using GPT-4 (OpenAI)

---

**Report Generated by**: Entity Background Research Agent v2.1.0
**Search Duration**: 4 minutes 32 seconds
**API Calls Made**: 47 (sanctions: 10, conglomerate: 24, OSINT: 13)

---

*This report is for informational purposes only and does not constitute legal advice. Consult qualified legal counsel for compliance decisions.*
```

---

## 16. Appendix C — Primary Repository Artifacts

**Core Application**:
- `app.py` — Streamlit application entry point
- `requirements.txt` — Python dependencies
- `README.md` — User documentation
- `CLAUDE.md` — Development guidelines
- `.env.example` — Environment variable template

**Source Code**:
- `core/` — Application logic (orchestrator, processors)
- `services/` — Data integration (sanctions, conglomerate, financial, OSINT)
- `intelligence/` — LLM report generation
- `persistence/` — Database and cache management
- `visualization/` — Graph, map, chart generation
- `export/` — PDF, Excel, JSON exporters
- `ui/` — Streamlit UI components
- `integrations/` — External API clients
- `utils/` — Shared utilities

**Documentation**:
- `docs/architecture.md` — This document
- `docs/api_reference.md` — API documentation
- `docs/user_guide.md` — End-user guide
- `docs/deployment_guide.md` — Deployment instructions

**Testing**:
- `tests/unit/` — Unit tests
- `tests/integration/` — Integration tests
- `tests/fixtures/` — Test data

---

**END OF SOLUTION ARCHITECTURE DOCUMENT**

---

**Document Control**
**Version**: 1.0
**Author**: Senior Product Manager
**Approved By**: [Pending Review]
**Next Review Date**: 2026-06-12 (Quarterly)
