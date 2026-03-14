# Quick Start Guide - Phase 1 Complete! 🎉

## What's Been Built

✅ **Backend API** (FastAPI) - Port 8000
✅ **Frontend UI** (Next.js) - Port 3000
✅ **Base Tier Research** - Sanctions + OSINT + AI Reports
✅ **Defense/Cyber Theme** - Dark navy styling
✅ **Full Integration** - Working end-to-end

## Start the System (2 Steps)

### Step 1: Start Backend

```bash
cd backend
uvicorn app:app --reload
```

✅ Backend running at: **http://localhost:8000**
📚 API docs at: **http://localhost:8000/docs**

### Step 2: Start Frontend

Open a **new terminal**:

```bash
cd frontend
npm run dev
```

✅ Frontend running at: **http://localhost:3000**

## Test It Out

1. **Open**: http://localhost:3000
2. **Enter entity**: e.g., "Huawei Technologies"
3. **Select country**: "China" (optional)
4. **Click**: "Start Background Research"
5. **Wait**: 30-60 seconds
6. **View results**: Sanctions hits, media intelligence, AI report

## Example Search

**Test Entity**: Huawei Technologies
**Country**: China
**Expected Result**: HIGH risk level, 10+ sanctions hits, media coverage

## What You Can Do

### Search Features
- ✅ Entity name search with fuzzy matching
- ✅ Country filter (China, Russia, Iran, etc.)
- ✅ Adjustable fuzzy threshold (0-100%)
- ✅ Real-time loading status

### Results Display
- ✅ Risk level badges (color-coded)
- ✅ Sanctions hits with match quality scores
- ✅ Media intelligence (official + general sources)
- ✅ AI-generated intelligence report

## File Structure

```
backend/          # FastAPI API (Python)
frontend/         # Next.js UI (TypeScript + React)
agents/           # Existing (reused)
core/             # Existing (reused)
sanctions.db      # SQLite database
```

## API Endpoints

### Available Now
- `GET /api/health` - Health check
- `POST /api/search/base` - Base tier search
- `GET /api/results/{id}` - Get search results
- `GET /api/results/` - Search history
- `GET /docs` - Interactive API documentation

### Coming in Phase 2
- `POST /api/search/network` - Network tier (conglomerates)
- `POST /api/search/deep` - Deep tier (financial flows)

## Test with curl

```bash
# Health check
curl http://localhost:8000/api/health

# Base tier search
curl -X POST http://localhost:8000/api/search/base \
  -H "Content-Type: application/json" \
  -d '{"entity_name": "Huawei Technologies", "country": "China", "fuzzy_threshold": 80, "tier": "base"}'
```

## Troubleshooting

**Backend won't start?**
- Check `backend/.env` exists and has `USA_TRADE_GOV_API_KEY`
- Verify Ollama is running: `ollama list`
- Check port 8000 is available

**Frontend won't connect?**
- Verify backend is running first
- Check `frontend/.env.local` has `NEXT_PUBLIC_API_URL=http://localhost:8000`
- Clear browser cache and reload

**Search takes too long?**
- Base tier is expected to take 30-60 seconds
- This is normal for comprehensive research

## Next Steps

Read detailed documentation:
- **Phase 1 Summary**: `PHASE1_COMPLETE.md`
- **Backend docs**: `backend/README.md`
- **Frontend docs**: `frontend/README.md`

## Ready for Phase 2?

Phase 2 will add:
- Network tier research
- Conglomerate search
- Network graph visualization
- Director/shareholder extraction

---

**Status**: Phase 1 Complete ✅
**Date**: March 14, 2026
**Architecture**: Streamlit → React/Next.js + REST API ✅
