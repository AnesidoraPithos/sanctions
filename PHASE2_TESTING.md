# Phase 2: Quick Testing Guide

## Quick Start (5 Minutes)

### Step 1: Start the Backend
```bash
cd backend
uvicorn app:app --reload
```

Verify backend is running:
```bash
curl http://localhost:8000/api/health
```

### Step 2: Start the Frontend
```bash
cd frontend
npm run dev
```

Open browser: http://localhost:3000

### Step 3: Run a Quick Test

**Test Entity**: "Apple Inc."
**Tier**: Network
**Depth**: 1 (fastest)
**Duration**: ~2-3 minutes

1. Select "Network Tier" card
2. Leave depth at 1
3. Enter "Apple Inc."
4. Click "Start Network Tier Research"
5. Wait ~2-3 minutes
6. View results:
   - Click "Network Graph" tab → See interactive visualization
   - Click "Financial Intelligence" tab → See directors, shareholders
   - Click "Subsidiaries" tab → See subsidiary list

---

## Expected Results

### Network Graph Tab
- Interactive graph with zoom/pan
- Blue node = Apple Inc. (parent)
- Green nodes = Subsidiaries
- Orange hexagons = Directors
- Yellow diamonds = Shareholders
- Can export as PNG

### Financial Intelligence Tab
- Directors & Officers table (10-20 people)
- Major Shareholders table (institutional investors)
- Related Party Transactions (if available)

### Subsidiaries Tab
- List of Apple subsidiaries (20-40 entities)
- Jurisdiction, ownership %, status
- Sanctions status (likely none for Apple)

---

## Test Without OpenCorporates API Key

**To test graceful fallback**:

1. Remove `OPENCORPORATES_API_KEY` from `backend/.env`
2. Restart backend
3. Run same search
4. **Expected**: Warning banner appears:
   - "OpenCorporates API key not configured - skipping"
   - "Data sources used: sec_edgar, wikipedia"
5. **Still works**: Subsidiaries discovered via SEC EDGAR

---

## Test Chinese Company (Sanctions Risk)

**Test Entity**: "Huawei Technologies"
**Expected**:
- HIGH or VERY_HIGH risk level
- Multiple sanctions hits
- Limited subsidiary data (non-US company)
- Warning: "No SEC filing data found (normal for non-US entities)"

---

## Test Deep Search (10 Minutes)

**Test Entity**: "Berkshire Hathaway"
**Tier**: Network
**Depth**: 2
**Duration**: ~5-7 minutes

**Expected**:
- 50-100+ subsidiaries
- Multi-level graph (parent → subsidiary → sub-subsidiary)
- Large network visualization

---

## Troubleshooting

### "Module cytoscape not found"
```bash
cd frontend
npm install cytoscape @types/cytoscape
```

### "USA_TRADE_GOV_API_KEY not set"
Add to `backend/.env`:
```
USA_TRADE_GOV_API_KEY=your_key_here
```

### Backend 500 error on /network
Check backend logs for detailed error message:
```bash
# Backend terminal will show stack trace
```

### Graph doesn't render
- Open browser DevTools (F12)
- Check Console tab for JavaScript errors
- Verify API response includes `network_data`

---

## Performance Notes

**Normal Durations**:
- Depth 1: 2-3 minutes
- Depth 2: 5-7 minutes
- Depth 3: 7-10 minutes

**If taking > 15 minutes**:
- Large company with 100+ subsidiaries
- Network issues connecting to SEC EDGAR
- Check backend logs for errors

---

## Success Criteria

✅ Network tier search completes in < 10 minutes
✅ Network graph displays and is interactive
✅ Can zoom, pan, drag nodes
✅ Click node shows details panel
✅ Financial intelligence tables display
✅ Subsidiaries list displays
✅ Warnings appear when OpenCorporates key missing
✅ Base tier still works (backward compatibility)

---

## Next: Full Testing (Phase 2C)

After quick testing, proceed to comprehensive testing in PHASE2_COMPLETE.md:
- Test cases 1-6
- API testing with curl
- Performance benchmarks
- Edge cases
