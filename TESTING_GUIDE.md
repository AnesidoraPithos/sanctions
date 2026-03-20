# Phase 2 Critical Fixes - Testing Guide

## Quick Start

### 1. Start Backend
```bash
cd "/Users/faith/Desktop/IMDA/International/sanctions free/backend"
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 2. Start Frontend (New Terminal)
```bash
cd "/Users/faith/Desktop/IMDA/International/sanctions free/frontend"
npm run dev
```

**Expected Output**:
```
▲ Next.js 14.x
- Local:        http://localhost:3000
- Ready in 2.5s
```

### 3. Open Browser
Navigate to: http://localhost:3000

---

## Test Case 1: Huawei (Parent Company Discovery)

### Objective
Verify that parent company discovery works for non-US companies.

### Steps
1. Enter entity name: **Huawei**
2. Select tier: **Network**
3. Set network depth: **1**
4. Click **Search**
5. Wait 2-5 minutes for search to complete
6. Results page should load automatically

### Expected Results ✅

#### Network Tier Confirmation Banner (Blue)
```
🔬 Network Tier Research Completed
Corporate structure analysis performed (1 level deep). Discovered X entities.

Data sources checked: OpenCorporates API, SEC EDGAR, Wikipedia, DuckDuckGo
```

#### Warnings Banner (Yellow) - May appear if OpenCorporates API key missing
```
⚠️ Data Source Limitations
• OpenCorporates API key not configured - skipped

Data sources used: sec_edgar, wikipedia, duckduckgo
```

#### Subsidiaries Tab - Parent Company Section (Purple)
```
⬆️ Parent Company Discovered

Huawei Investment & Holding Co., Ltd    [Parent]

Jurisdiction: China
Relationship: Parent
Confidence: High (or Medium/Low)
Source: https://en.wikipedia.org/wiki/Huawei

This entity is owned by or is a subsidiary of the parent company shown above.
```

#### Subsidiaries List
Should show discovered subsidiaries like:
- Huawei Device Co., Ltd.
- Huawei Cloud
- HiSilicon Technologies
- etc.

### Pass Criteria
- ✅ Parent company "Huawei Investment & Holding Co., Ltd" is displayed
- ✅ Purple banner appears in Subsidiaries tab
- ✅ Data sources checked shows all sources tried
- ✅ Confidence level is displayed (high/medium/low)
- ✅ Source URL is clickable and valid

---

## Test Case 2: Apple (SEC EDGAR Visibility)

### Objective
Verify that SEC EDGAR appears in data sources when it's the primary method used.

### Steps
1. Enter entity name: **Apple Inc**
2. Select tier: **Network**
3. Set network depth: **1**
4. Click **Search**
5. Wait 2-5 minutes

### Expected Results ✅

#### Network Tier Confirmation Banner
```
Data sources checked: OpenCorporates API, SEC EDGAR, Wikipedia, DuckDuckGo
```

**CRITICAL**: "SEC EDGAR" must appear in the list!

#### Subsidiaries Tab
- Should show subsidiaries from SEC EDGAR Exhibit 21.1
- NO parent company section (Apple is top-level)

#### Browser Console (F12 → Console)
Check metadata in Network tab or console:
```javascript
metadata: {
  conglomerate_method: "sec_edgar_10k",
  data_sources_used: ["opencorporates_api", "sec_edgar", ...]  // SEC EDGAR MUST BE HERE
}
```

### Pass Criteria
- ✅ SEC EDGAR appears in "Data sources checked"
- ✅ Subsidiaries are discovered from SEC filings
- ✅ No parent company section displayed
- ✅ metadata.data_sources_used includes 'sec_edgar'

---

## Test Case 3: Unknown Company (Transparency)

### Objective
Verify that user sees all data sources tried even when no results found.

### Steps
1. Enter entity name: **XYZ Nonexistent Corporation 9999**
2. Select tier: **Network**
3. Set network depth: **1**
4. Click **Search**
5. Wait 2-5 minutes

### Expected Results ✅

#### Empty State in Subsidiaries Tab
```
🏢 Subsidiary Search Completed
No subsidiaries were found for this entity.

Search parameters:
• Search depth: 1 level(s)
• Ownership threshold: 0%
• Include sisters: Yes

Data sources checked:
OPENCORPORATES_API, SEC EDGAR, WIKIPEDIA, DUCKDUCKGO

This is normal for private companies, small businesses,
non-US entities, or individuals.
```

#### Warnings Banner (Yellow)
```
⚠️ Data Source Limitations
• OpenCorporates API key not configured - skipped

Data sources used: sec_edgar, wikipedia, duckduckgo
```

### Pass Criteria
- ✅ Empty state shows all data sources checked
- ✅ User sees transparency about what was tried
- ✅ No crash or error
- ✅ Helpful explanation provided

---

## Debugging Tips

### Backend Logs (Terminal 1)

**Look for these log messages**:

#### Parent Company Search
```
INFO:agents.research_agent:Searching for parent company of 'Huawei'...
INFO:agents.research_agent:✓ Found parent company: Huawei Investment & Holding Co., Ltd (confidence: high)
```

#### Data Sources Tried
```
INFO:backend.services.conglomerate_service:Starting conglomerate search for 'Huawei' (depth=1, ownership_threshold=0%, include_sisters=True)
WARNING:backend.services.conglomerate_service:OpenCorporates API key not configured - will use fallback methods
INFO:agents.research_agent:Trying OpenCorporates API for Huawei...
INFO:agents.research_agent:No OpenCorporates API key configured
INFO:agents.research_agent:Trying SEC EDGAR for Huawei...
INFO:agents.research_agent:SEC EDGAR returned no results
INFO:agents.research_agent:Trying Wikipedia for Huawei...
INFO:agents.research_agent:Using DuckDuckGo search for Huawei...
```

### Frontend Console (F12 → Console)

**Check for errors**:
```javascript
// Good - No errors
✓ API request successful

// Bad - Error
❌ Error: Failed to fetch
```

**Inspect API Response** (Network Tab):
1. Open DevTools (F12)
2. Go to Network tab
3. Click on POST request to `/api/search/network`
4. Click Response tab
5. Look for:
   - `data_sources_used: ["opencorporates_api", "sec_edgar", "wikipedia", "duckduckgo"]`
   - `network_data.parent_info: { name: "...", jurisdiction: "...", ... }`

### Common Issues

#### Issue: "Port 8000 already in use"
**Solution**:
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn app:app --reload --port 8001
```

#### Issue: Frontend can't connect to backend
**Check**:
1. Backend is running on http://localhost:8000
2. Frontend .env.local has: `NEXT_PUBLIC_API_URL=http://localhost:8000`
3. CORS is enabled in backend (should be by default)

#### Issue: "Module not found" error in backend
**Solution**:
```bash
cd backend
pip install -r requirements.txt
```

#### Issue: TypeScript errors in frontend
**Solution**:
```bash
cd frontend
npm install
npm run build  # Check for type errors
```

---

## Performance Expectations

| Operation | Expected Duration |
|-----------|------------------|
| Backend startup | 2-5 seconds |
| Frontend startup | 5-10 seconds |
| Base tier search | 30-60 seconds |
| Network tier search (depth 1) | 2-5 minutes |
| Network tier search (depth 2) | 5-7 minutes |
| Network tier search (depth 3) | 7-10 minutes |
| Parent company search | +5 seconds (within network search) |

---

## Success Indicators

### ✅ All Tests Pass When:
1. **Huawei Test**: Parent company "Huawei Investment & Holding Co., Ltd" is displayed with purple banner
2. **Apple Test**: SEC EDGAR appears in "Data sources checked"
3. **Unknown Company Test**: Empty state shows all data sources tried
4. **No Crashes**: No errors in backend logs or frontend console
5. **Backend Imports**: `python3 -c "from routes.search_routes import router"` succeeds
6. **Frontend Builds**: `npm run build` completes without TypeScript errors

### ⚠️ Partial Success (Needs Investigation):
- Parent company found but confidence is "low"
- SEC EDGAR found but no subsidiaries extracted
- Some data sources return errors but search continues

### ❌ Test Fails When:
- Backend crashes with import errors
- Frontend shows blank page or crashes
- API returns 500 errors
- Parent company never displays even for Huawei
- SEC EDGAR never appears in data sources list
- data_sources_tried is missing from response

---

## Manual Verification Checklist

Before marking Phase 2 complete, verify:

- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] Can perform base tier search (sanity check)
- [ ] Can perform network tier search
- [ ] Huawei search finds parent company
- [ ] Apple search shows SEC EDGAR in data sources
- [ ] Unknown company shows empty state with transparency
- [ ] Purple banner displays parent company info correctly
- [ ] Network graph includes parent company nodes (if applicable)
- [ ] All tabs (Sanctions, Media, Report, Network, Financial, Subsidiaries) work
- [ ] No console errors in browser DevTools
- [ ] No Python errors in backend logs

---

## Reporting Issues

If any test fails, collect these details:

1. **Test case that failed**: Huawei / Apple / Unknown Company
2. **Error message**: Copy full error from logs or console
3. **Screenshots**: Capture the failure state
4. **API response**: Copy JSON from Network tab in DevTools
5. **Backend logs**: Copy relevant log lines (last 50 lines)
6. **Environment**:
   - Python version: `python3 --version`
   - Node version: `node --version`
   - OS: macOS/Linux/Windows
   - Branch: version3

---

## Next Steps After Testing

### If All Tests Pass ✅
1. Commit changes with suggested commit message from PHASE2_CRITICAL_FIXES_COMPLETE.md
2. Update PHASE2_COMPLETE.md with test results
3. Proceed to Phase 3 (Deep Tier) or other improvements

### If Tests Fail ❌
1. Review error messages in logs
2. Check PHASE2_CRITICAL_FIXES_COMPLETE.md for troubleshooting
3. Verify all files were modified correctly
4. Re-run failed test with increased logging
5. Report issue with collected details

---

**Good luck with testing! 🚀**

**Questions?** Check PHASE2_CRITICAL_FIXES_COMPLETE.md for detailed implementation notes.
