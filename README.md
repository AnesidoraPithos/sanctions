# BEAR² — Entity Background Research Agent

> AI-powered sanctions screening and corporate intelligence platform for international relations staff.

**Current architecture**: FastAPI backend + Next.js frontend (version3 branch)
**Legacy Streamlit app**: archived at `archive/legacy_streamlit/`

---

## What It Does

BEAR² helps staff answer two questions about any entity:
1. **"Is there risk in associating with this entity?"**
2. **"What is the extent — first-order, second-order?"**

It automates research across 10+ USA sanctions databases, SEC EDGAR, OpenCorporates, and public OSINT sources, then generates a risk-scored intelligence report.

---

## Research Tiers

| Tier | Time | What It Does |
|------|------|--------------|
| **Base** | 30-60s | Sanctions screening + OSINT media + AI report + risk level |
| **Network** | 2-5 min | Base + corporate structure (subsidiaries/parent/sisters) + directors/shareholders + relationship graph |
| **Deep** | 5-15 min | Network + financial flows (USAspending.gov) + director pivot + infrastructure correlation + beneficial ownership + advanced OSINT |

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env — see Environment Variables below
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

API available at:
- Endpoints: http://localhost:8000
- Interactive docs: http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend available at: http://localhost:3000

---

## Environment Variables

Create `backend/.env`:

```bash
# Sanctions API (required)
USA_TRADE_GOV_API_KEY=your_key_here   # from https://developer.trade.gov

# LLM (choose one)
LLM_PROVIDER=ollama                    # "ollama" or "openai"
OLLAMA_BASE_URL=http://localhost:11434 # if using Ollama
OPENAI_API_KEY=your_key_here           # if using OpenAI
ANTHROPIC_API_KEY=your_key_here        # if using Anthropic/Claude

# Database
DATABASE_PATH=../sanctions.db          # path to SQLite file

# Optional
OPENCORPORATES_API_KEY=your_key_here   # improves conglomerate search
CORS_ORIGINS=http://localhost:3000     # frontend URL
```

---

## File Structure

```
sanctions-free/
├── backend/                       # FastAPI application
│   ├── app.py                     # Entry point
│   ├── config.py                  # Settings and env vars
│   ├── routes/                    # API endpoints
│   │   ├── search_routes.py       # POST /api/search/{base|network|deep}
│   │   ├── results_routes.py      # GET /api/results/
│   │   ├── export_routes.py       # GET /api/export/{id}
│   │   └── health_routes.py       # GET /api/health
│   ├── services/                  # Business logic
│   │   ├── sanctions_service.py   # Sanctions API wrapper
│   │   ├── research_service.py    # OSINT + LLM
│   │   ├── conglomerate_service.py# Subsidiary/parent discovery
│   │   ├── network_service.py     # Graph data generation
│   │   ├── risk_assessment_service.py
│   │   ├── director_pivot_service.py   # Deep tier
│   │   ├── infrastructure_service.py   # Deep tier
│   │   ├── beneficial_ownership_service.py # Deep tier
│   │   └── osint_advanced_service.py   # Deep tier
│   ├── models/                    # Pydantic request/response models
│   ├── db_operations/             # SQLite database wrapper
│   ├── utils/                     # Fuzzy matching, graph builder
│   └── websocket/                 # WebSocket progress handler
│
├── frontend/                      # Next.js application
│   ├── app/
│   │   ├── page.tsx               # Home / search
│   │   ├── results/[id]/page.tsx  # Results display
│   │   └── saved/page.tsx         # Search history
│   ├── components/                # UI components
│   │   ├── SearchForm.tsx
│   │   ├── TierSelector.tsx
│   │   ├── ProgressTracker.tsx
│   │   ├── NetworkGraph.tsx
│   │   ├── RiskBadge.tsx
│   │   ├── ManagementNetworkTab.tsx
│   │   ├── InfrastructureTab.tsx
│   │   └── BeneficialOwnershipTab.tsx
│   └── lib/
│       ├── api-client.ts          # Backend API calls
│       ├── websocket.ts           # WebSocket client
│       └── types.ts               # TypeScript types
│
├── archive/legacy_streamlit/      # Old Streamlit app (reference only)
├── key documents/                 # Project specifications and vision
│   ├── requirements.md            # Full feature spec (source of truth)
│   ├── value_proposition.md       # Product rationale and user stories
│   ├── rationale.md               # Brief project overview
│   └── Mapping *.md               # Research reference guides
├── docs/
│   └── implementation-status.md  # What's built vs. what's not
│
├── sanctions.db                   # SQLite database
├── CLAUDE.md                      # AI assistant configuration
├── STYLE_GUIDE.md                 # Frontend design system
└── CHANGELOG.md                   # Feature history
```

---

## Data Sources

| Source | What It Provides |
|--------|-----------------|
| USA Trade.gov CSL | OFAC SDN, BIS Entity List, Treasury, State Dept, Commerce |
| Local DB | DOD Section 1260H (Chinese Military), FCC Covered List |
| SEC EDGAR | Subsidiaries (10-K Exhibit 21), directors/shareholders (DEF 14A, 20-F), transactions |
| OpenCorporates | Global corporate registry (requires API key) |
| Wikipedia | Subsidiary lists for major corporations |
| DuckDuckGo | General OSINT and media coverage (free, no key required) |
| USAspending.gov | US federal procurement records (deep tier) |

---

## Risk Levels

| Level | Meaning |
|-------|---------|
| SAFE | No sanctions matches |
| LOW | Fuzzy match only, no media coverage |
| MID | Exact match with limited media, or high AI risk score |
| HIGH | Exact sanctions match + significant media coverage |
| VERY HIGH | Extensive official media coverage, clear sanctions exposure |

---

## Development

### Run tests

```bash
cd backend
pytest tests/

# Static analysis
ruff check .
mypy .
black --check .
```

### Add a new API endpoint

1. Create route file in `backend/routes/`
2. Register in `backend/app.py`:
   ```python
   from routes import my_routes
   app.include_router(my_routes.router, prefix="/api/my", tags=["My"])
   ```

---

## Documentation

| Doc | Purpose |
|-----|---------|
| `key documents/requirements.md` | Full feature specification and user journeys |
| `key documents/value_proposition.md` | Product rationale and target users |
| `docs/implementation-status.md` | What's built vs. spec — start here to understand current state |
| `CHANGELOG.md` | Feature history by date |
| `STYLE_GUIDE.md` | Frontend design system (colors, typography, components) |
| `backend/README.md` | Backend API reference |

---

## License

Internal IMDA use only. Not for public distribution.
