# Entity Background Research API - Backend

FastAPI backend for the Entity Background Research Agent. Provides REST API endpoints for sanctions screening, OSINT research, and intelligence reporting.

## Architecture

This backend replaces the monolithic Streamlit application with a modern REST API architecture:

```
backend/
├── app.py                     # FastAPI application entry point
├── config.py                  # Configuration management
├── routes/                    # API endpoints
│   ├── health_routes.py       # Health check endpoints
│   ├── search_routes.py       # Search endpoints (base/network/deep)
│   └── results_routes.py      # Results retrieval endpoints
├── services/                  # Business logic layer
│   ├── sanctions_service.py   # Sanctions screening (wraps agents/usa_agent.py)
│   └── research_service.py    # OSINT research (wraps agents/research_agent.py)
├── models/                    # Pydantic models
│   ├── requests.py            # Request validation models
│   └── responses.py           # Response models
├── database/                  # Database operations
│   └── db.py                  # Wraps core/database.py
└── middleware/                # Middleware (CORS, auth, etc.)
```

## Installation

### Prerequisites

- Python 3.10+
- USA Trade API key (from data.trade.gov)
- Ollama (for LLM) OR OpenAI API key
- SQLite database (sanctions.db)

### Setup

1. **Install dependencies:**

```bash
cd backend
pip install -r requirements.txt
```

2. **Configure environment variables:**

```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

Required environment variables:
- `USA_TRADE_GOV_API_KEY` - USA Trade API key for sanctions screening
- `LLM_PROVIDER` - Either "ollama" or "openai"
- `OLLAMA_BASE_URL` - Ollama server URL (if using Ollama)
- `OPENAI_API_KEY` - OpenAI API key (if using OpenAI)
- `DATABASE_PATH` - Path to sanctions.db (default: ../sanctions.db)

3. **Verify configuration:**

```bash
python config.py
```

This will show your current configuration and any warnings.

## Running the Server

### Development Mode (with auto-reload):

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- **API Base:** http://localhost:8000
- **Interactive API Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## API Endpoints

### Health Check

**GET /api/health**
- Check API health status and configuration
- Returns database accessibility and warnings

**GET /api/ping**
- Simple connectivity check

### Base Tier Search

**POST /api/search/base**

Perform base tier entity background search (30-60 seconds).

Request body:
```json
{
  "entity_name": "Huawei Technologies",
  "country": "China",
  "fuzzy_threshold": 80,
  "tier": "base"
}
```

Response:
```json
{
  "search_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "tier": "base",
  "entity_name": "Huawei Technologies",
  "risk_level": "HIGH",
  "sanctions_hits": 12,
  "media_hits": 8,
  "intelligence_report": "# Due Diligence Intelligence Report...",
  "timestamp": "2026-03-14T10:30:00Z"
}
```

### Retrieve Results

**GET /api/results/{search_id}**
- Retrieve full search results by ID
- Returns sanctions data, media intelligence, and intelligence report

**GET /api/results/**
- Get search history
- Query parameter: `limit` (default: 50, max: 100)

## Current Implementation Status

### ✅ Phase 1A Complete: Backend API Foundation

- [x] FastAPI application with CORS
- [x] Configuration management
- [x] Health check endpoints
- [x] Sanctions service (refactored from agents/usa_agent.py)
- [x] Research service (refactored from agents/research_agent.py)
- [x] Pydantic request/response models
- [x] POST /api/search/base endpoint
- [x] GET /api/results/{id} endpoint
- [x] Database operations wrapper

### 🚧 Phase 2: Network Tier (Coming Soon)

- [ ] POST /api/search/network endpoint
- [ ] Conglomerate search (SEC EDGAR + OpenCorporates)
- [ ] Director/shareholder extraction
- [ ] Network graph data generation

### 🚧 Phase 3: Deep Tier (Coming Soon)

- [ ] POST /api/search/deep endpoint
- [ ] Financial flow analysis
- [ ] WebSocket progress updates

## Testing

### Manual Testing with curl:

**Health check:**
```bash
curl http://localhost:8000/api/health
```

**Base tier search:**
```bash
curl -X POST http://localhost:8000/api/search/base \
  -H "Content-Type: application/json" \
  -d '{
    "entity_name": "Huawei Technologies",
    "country": "China",
    "fuzzy_threshold": 80,
    "tier": "base"
  }'
```

**Get results:**
```bash
curl http://localhost:8000/api/results/{search_id}
```

### Testing with Interactive Docs:

Visit http://localhost:8000/docs to use the interactive Swagger UI for testing all endpoints.

## Code Reuse Strategy

This backend **reuses existing code** rather than rewriting everything:

| Existing Module | Backend Service | Purpose |
|-----------------|-----------------|---------|
| `agents/usa_agent.py` | `services/sanctions_service.py` | Sanctions API client (wrapper) |
| `agents/research_agent.py` | `services/research_service.py` | OSINT + LLM (wrapper) |
| `core/database.py` | `database/db.py` | Database operations (wrapper) |
| `core/matching_utils.py` | (imported directly) | Fuzzy matching logic |

This minimizes the risk of introducing bugs and maintains compatibility with existing functionality.

## Troubleshooting

### Common Issues:

1. **"Missing API Key" error:**
   - Check that `USA_TRADE_GOV_API_KEY` is set in `.env`
   - Verify the key is valid at data.trade.gov

2. **"Database not found" warning:**
   - Ensure `sanctions.db` exists in the parent directory
   - Update `DATABASE_PATH` in `.env` if it's in a different location

3. **LLM errors:**
   - If using Ollama: verify Ollama is running (`ollama list`)
   - If using OpenAI: check `OPENAI_API_KEY` is valid

4. **Import errors:**
   - Ensure you're in the `backend/` directory when running
   - The services add parent directories to Python path to import from `agents/` and `core/`

5. **CORS errors (from frontend):**
   - Check `CORS_ORIGINS` in `.env` includes your frontend URL
   - Default: `http://localhost:3000,http://127.0.0.1:3000`

## Development Notes

### Adding New Endpoints:

1. Create route file in `backend/routes/`
2. Import and register in `backend/app.py`:
   ```python
   from routes import my_routes
   app.include_router(my_routes.router, prefix="/api/my", tags=["My"])
   ```

### Adding New Services:

1. Create service file in `backend/services/`
2. Add service factory function (e.g., `get_my_service()`)
3. Import in routes that need the service

### Code Quality:

Run static analysis:
```bash
ruff check .
mypy .
black --check .
```

## Next Steps

After completing Phase 1A (Backend), the next steps are:

1. **Phase 1B**: Build Next.js frontend
2. **Phase 1C**: Integration testing (frontend + backend)
3. **Phase 1D**: Polish and deployment prep
4. **Phase 2**: Network tier implementation

## License

Internal IMDA project.
