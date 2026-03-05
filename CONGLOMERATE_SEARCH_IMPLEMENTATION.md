# Conglomerate Search Feature - Implementation Summary

## Overview
Successfully implemented the Conglomerate Search feature that allows users to search for a parent company's subsidiaries and run sanctions checks on selected subsidiaries.

## Implementation Date
March 5, 2026

## Files Modified

### 1. research_agent.py
**Lines Added: ~180 lines**

#### New Methods:
- `find_subsidiaries(parent_company_name, depth=1)` (lines 363-402)
  - Searches for subsidiaries at specified depth levels (1-3)
  - Handles deduplication across levels
  - Returns list of subsidiary dictionaries with name, jurisdiction, status, and level

- `_search_subsidiaries_level(company_name, level)` (lines 403-481)
  - Searches OpenCorporates via DuckDuckGo for subsidiaries
  - Uses LLM (Ollama) to extract structured subsidiary information
  - Returns list of subsidiaries for a specific level

### 2. app.py
**Lines Added: ~300 lines**

#### UI Components:
1. **Conglomerate Toggle** (line 347)
   - Added "CONGLOMERATE SEARCH" toggle to control panel

2. **Depth Selector** (lines 350-354)
   - Dropdown to select search depth (1-3 levels)
   - Only visible when conglomerate search is enabled

#### Modified Logic:
3. **Search Execution Flow** (lines 372-385)
   - Modified to handle conglomerate search workflow
   - Routes to subsidiary selection before running analysis

4. **Display Results Logic** (lines 387-408)
   - Added subsidiary selection interface display
   - Routes to appropriate analysis function based on search type

#### New Functions:
5. **display_subsidiary_selection()** (lines 447-550)
   - Displays found subsidiaries in organized interface
   - Groups subsidiaries by hierarchy level
   - Provides SELECT ALL / CLEAR ALL buttons
   - Shows subsidiary details: name, jurisdiction, status
   - Handles cancellation and proceeding with search

6. **display_entity_results()** (lines 881-1027)
   - Extracted from run_analysis() for code reuse
   - Displays results for a single entity
   - Includes threat calculation, status bar, and result tabs

7. **run_conglomerate_analysis()** (lines 1029-1131)
   - Analyzes parent company + selected subsidiaries
   - Shows progress bar during multi-entity search
   - Displays grouped results with expandable sections
   - Logs conglomerate searches to database with "[CONGLOMERATE]" prefix

## Features Implemented

### 1. Subsidiary Discovery
- Searches OpenCorporates for company subsidiaries
- Supports 3 depth levels:
  - Level 1: Direct subsidiaries
  - Level 2: Subsidiaries + their children
  - Level 3: Three levels deep
- Uses LLM to extract structured data from search results
- Handles deduplication across levels

### 2. Subsidiary Selection Interface
- Displays all found subsidiaries in organized format
- Groups by hierarchy level with expandable sections
- Shows subsidiary details:
  - Company name (full legal name)
  - Jurisdiction (country/state)
  - Status (active/inactive)
  - Hierarchy level
- Interactive selection with checkboxes
- Bulk actions: SELECT ALL / CLEAR ALL
- Visual status indicators (green for active, gray for inactive)

### 3. Multi-Entity Analysis
- Searches parent company + all selected subsidiaries
- Progress bar shows real-time search status
- Caches individual entity results for performance
- Calculates total matches across all entities

### 4. Grouped Results Display
- Overall summary showing:
  - Parent company name
  - Number of subsidiaries checked
  - Total entities searched
  - Total database matches
- Expandable sections for each entity:
  - Parent company section
  - Individual subsidiary sections (grouped by level)
  - Auto-expands sections with matches
- Color-coded based on match status
- Reuses existing entity display logic

### 5. Database Logging
- Logs conglomerate searches to analysis_history table
- Uses "[CONGLOMERATE]" prefix for easy identification
- Records total matches across all entities
- Tags with "CONGLOMERATE_SEARCH" analysis type

## Technical Details

### Search Flow
1. User enters parent company name
2. User enables "CONGLOMERATE SEARCH" toggle
3. User selects search depth (1-3)
4. User clicks "EXECUTE QUERY"
5. System searches for subsidiaries using OpenCorporates
6. LLM extracts structured subsidiary data
7. System displays subsidiary selection interface
8. User selects subsidiaries to check
9. User clicks "PROCEED WITH SEARCH"
10. System runs sanctions checks on parent + selected subsidiaries
11. System displays grouped results with expandable sections

### Session State Management
- `search_conglomerate`: Boolean flag for conglomerate mode
- `search_depth`: Selected depth level (1-3)
- `show_subsidiary_selection`: Controls subsidiary UI display
- `subsidiaries_found`: Cached subsidiary search results
- `selected_sub_indices`: User-selected subsidiary indices
- `selected_subsidiaries`: Full subsidiary data for selected entities

### Caching Strategy
- `fetch_analysis_data()` remains cached for individual entities
- Subsidiary search results cached in session state
- Prevents re-fetching during UI interactions

### Error Handling
- Gracefully handles no subsidiaries found
- LLM extraction errors return empty list
- Network/search errors logged and handled
- Empty result lists handled safely

## Testing Recommendations

### Test Case 1: Basic Conglomerate Search
- Input: "Huawei"
- Depth: 1
- Expected: Multiple subsidiaries found, selection interface displayed
- Action: Select 3-5 subsidiaries, proceed with search
- Expected: Each entity searched, results grouped correctly

### Test Case 2: Empty Subsidiary Results
- Input: Small company with no subsidiaries
- Expected: Warning message, proceeds with parent search only

### Test Case 3: Multi-Level Search
- Input: Large conglomerate
- Depth: 2
- Expected: Level 1 and Level 2 subsidiaries found
- Verify: No duplicate subsidiaries

### Test Case 4: Selection Interface
- Verify: SELECT ALL button works
- Verify: CLEAR ALL button works
- Verify: Individual checkboxes work
- Verify: Can cancel and return to search form

### Test Case 5: Result Display
- Verify: Parent company section appears
- Verify: Subsidiaries grouped by level
- Verify: Match counts accurate
- Verify: Expandable sections work
- Verify: Threat levels calculated correctly per entity

### Edge Cases
- Very large subsidiary lists (400+ entries)
- No network connection (DuckDuckGo fails)
- LLM/Ollama not running
- Session state conflicts

## Known Limitations

1. **OpenCorporates Coverage**: Depends on data availability in OpenCorporates
2. **LLM Dependency**: Requires Ollama to be running for subsidiary extraction
3. **Performance**: Large subsidiary lists (100+) may be slow to search
4. **Rate Limiting**: DuckDuckGo may rate limit if too many searches
5. **Accuracy**: LLM extraction may miss some subsidiaries or include false positives

## Enhancement: Sister Companies & OpenCorporates API (March 5, 2026)

### Overview
Enhanced the conglomerate search feature to:
1. Find both **subsidiaries AND sister companies**
2. Use **OpenCorporates API** for direct, structured access (primary method)
3. Fall back to DuckDuckGo search when API unavailable
4. Display sister companies separately with distinct visual styling

### What Are Sister Companies?
Sister companies are companies that share the same parent company but are not owned by the target company. They're important for sanctions checks because:
- They share ownership structure/parent
- Sanctions on one sister may indicate risks for others
- They often operate in related industries/jurisdictions

Example: If Company A and Company B are both owned by Parent Corp, and A is sanctioned, B is higher risk.

### Implementation Changes

#### research_agent.py (New Methods)
1. **search_opencorporates_company()** (lines 364-408)
   - Searches OpenCorporates API for company by name
   - Returns jurisdiction_code and company_number for further queries
   - Handles rate limiting (429 errors)

2. **find_related_companies_api()** (lines 410-535)
   - Finds subsidiaries (companies controlled by target)
   - Finds parent company (who controls the target)
   - Finds sister companies (other companies controlled by same parent)
   - Returns structured dict with 'subsidiaries', 'sisters', 'parent', 'method'

3. **_search_sister_companies()** (lines 537-610)
   - DuckDuckGo fallback for finding sister companies
   - Uses enhanced query: "parent company" OR "sister company" OR "affiliated with"
   - LLM extracts sister companies (not subsidiaries or parent)

4. **Modified find_subsidiaries()** (lines 612-671)
   - Now accepts `include_sisters` parameter (default=True)
   - Returns dict instead of list: `{'subsidiaries': [...], 'sisters': [...], 'parent': {...}, 'method': 'api'|'duckduckgo'}`
   - Tries OpenCorporates API first
   - Falls back to DuckDuckGo if:
     - No API key configured
     - Rate limit exceeded
     - API returns no results
   - Prints informative log messages about which method was used

#### app.py (UI Enhancements)
1. **Sister Companies Checkbox** (lines 352-353)
   - Added "INCLUDE SISTER COMPANIES" checkbox (default: checked)
   - Only visible when conglomerate search enabled
   - Stored in `st.session_state.include_sisters`

2. **display_subsidiary_selection()** (lines 447-565)
   - Renamed session state key: `subsidiaries_found` → `related_companies_found`
   - Handles dict result structure with 'subsidiaries' and 'sisters' keys
   - Displays search method used: "OpenCorporates API" or "DuckDuckGo Search"
   - Shows count: "Found X subsidiaries and Y sister companies"
   - Separate expanders for:
     - **🏢 Level N Subsidiaries** (green border for active)
     - **🤝 Sister Companies** (blue border, always expanded)
   - Combined `all_companies` list for unified selection handling

3. **run_conglomerate_analysis()** (lines 1049-1057, 1117-1121)
   - Passes `relationship` field through entity data
   - Distinguishes entity labels:
     - "🏢 PARENT" for parent company
     - "🤝 SISTER COMPANY" for sister companies
     - "🔗 SUBSIDIARY (LN)" for subsidiaries

### Configuration

#### Environment Variables (.env)
```bash
# OpenCorporates API Key (optional - for enhanced conglomerate search)
# Get your API key from: https://opencorporates.com/users/sign_up
# Free tier: 200 requests/month, 50 requests/day
OPENCORPORATES_API_KEY=""
```

#### Setup Instructions
1. Sign up at https://opencorporates.com/users/sign_up
2. Go to account page to get API token
3. Add token to `.env` file: `OPENCORPORATES_API_KEY="your_token_here"`
4. Restart the application

**Note**: Feature works without API key (falls back to DuckDuckGo), but API provides:
- More accurate results (structured JSON vs LLM parsing)
- Faster searches (direct API vs search engine)
- Better sister company detection

### API Rate Limits
- **Free Tier**: 200 requests/month, 50 requests/day
- **Strategy**:
  - Results cached in session state
  - API tried first for each search
  - Automatic fallback to DuckDuckGo if rate limited
  - User informed which method was used

### Search Flow (Updated with SEC EDGAR)
1. User enters parent company name
2. User enables "CONGLOMERATE SEARCH" toggle
3. User selects search depth (1-3)
4. **User checks/unchecks "INCLUDE SISTER COMPANIES"**
5. User clicks "EXECUTE QUERY"
6. **Three-tier fallback system**:
   - **Priority 1**: OpenCorporates API (if API key configured) - Fast, accurate, structured JSON for international companies
   - **Priority 2**: **SEC EDGAR (NEW)** - Official 10-K Exhibit 21 for US public companies
   - **Priority 3**: DuckDuckGo Search + LLM parsing - Reliable fallback for all companies
7. **System displays subsidiaries AND sister companies separately**
8. User selects companies to check (both subsidiaries and sisters)
9. User clicks "PROCEED WITH SEARCH"
10. System runs sanctions checks on parent + selected companies
11. **Results show sister companies with 🤝 icon**

### SEC EDGAR Integration (NEW - March 5, 2026)
**Added as middle-tier fallback for US public companies**

**What is SEC EDGAR?**
- US Securities and Exchange Commission's Electronic Data Gathering, Analysis, and Retrieval system
- Contains official filings from all US public companies
- **Exhibit 21** in 10-K annual reports lists ALL subsidiaries legally
- Most accurate source for US public company subsidiaries

**How it works:**
1. Searches SEC's company tickers database for CIK (Central Index Key)
2. Retrieves latest 10-K annual filing for the company
3. Locates Exhibit 21 (Subsidiaries of the Registrant)
4. Parses exhibit using LLM to extract subsidiary names and jurisdictions
5. Returns official, legally-filed subsidiary list

**Advantages:**
- ✅ **Highest accuracy** for US public companies (official legal filings)
- ✅ **Comprehensive** - Exhibit 21 lists ALL significant subsidiaries
- ✅ **Free** - No API key required
- ✅ **Structured data** - Includes jurisdiction of incorporation
- ✅ **Authoritative** - Legal requirement, verified by company

**Limitations:**
- ❌ Only US **public** companies (must file with SEC)
- ❌ Only subsidiaries (no sister companies)
- ❌ Requires latest 10-K to be filed
- ❌ Exhibit 21 format varies (requires LLM parsing)

**Performance:**
- Moderate speed (10-20 seconds)
- More accurate than DuckDuckGo
- No rate limits (but be respectful)

**When used:**
- Automatically tries for all companies after OpenCorporates API
- Best results for: Apple, Microsoft, Google, Amazon, Tesla, etc.
- Falls through to DuckDuckGo for non-US or private companies

**Combined Mode:**
- If sister companies requested: Uses SEC EDGAR for subsidiaries + DuckDuckGo for sisters
- Badge shows: "SEC EDGAR + DuckDuckGo"

### Visual Distinctions
- **Subsidiaries**: Green border (active) or gray (inactive), grouped by level
- **Sister Companies**: Blue border (#3b82f6), separate expander, "Sister Company" label
- **Method Badge**: Shows "OpenCorporates API", "SEC EDGAR (10-K Filings)", "SEC EDGAR + DuckDuckGo", or "DuckDuckGo Search"

### Testing

#### Test Case 1: API Method with Sister Companies
- Input: "Huawei"
- Enable conglomerate search, include sister companies
- With valid OpenCorporates API key
- Expected:
  - Uses API method (shown in UI)
  - Shows subsidiaries AND sister companies
  - Companies grouped by relationship type
  - All selected companies are searched

#### Test Case 2: DuckDuckGo Fallback
- Input: "Samsung"
- No API key configured OR rate limit exceeded
- Expected:
  - Falls back to DuckDuckGo (shown in UI)
  - Shows warning about method used
  - Still finds subsidiaries and sister companies (less accurate)

#### Test Case 3: Sisters Only
- Input: Company with no subsidiaries but has sisters
- Include sister companies checked
- Expected:
  - Shows sister companies section
  - Subsidiaries section empty/hidden

#### Test Case 4: UI Distinction
- Verify: Subsidiaries and sister companies in separate expanders
- Verify: Different icons (🏢 parent, 🔗 subsidiary, 🤝 sister)
- Verify: Color coding (green=active, blue=sister, gray=inactive)

#### Test Case 5: Rate Limit Handling
- Make many API calls to trigger rate limit
- Expected: Gracefully falls back to DuckDuckGo
- Expected: Shows appropriate message to user

### Benefits
1. **More Accurate**: Direct API access vs indirect search engine queries
2. **More Complete**: Finds both subsidiaries AND sister companies
3. **More Reliable**: Structured JSON data vs LLM parsing
4. **Transparent**: Shows which method was used (API or fallback)
5. **Fallback Ready**: Still works without API key
6. **Rate Limit Aware**: Handles API limits gracefully

### Known Limitations (Updated)
1. **OpenCorporates Coverage**: API only returns data available in OpenCorporates
2. **API Rate Limits**: Free tier has daily/monthly limits (50/day, 200/month)
3. **Sister Company Detection**:
   - API method: Requires control statements data in OpenCorporates
   - DuckDuckGo method: Relies on LLM parsing, may miss entities
4. **LLM Dependency**: DuckDuckGo fallback still requires Ollama
5. **Performance**: API calls add latency (but more accurate than web scraping)

## Future Enhancements

1. **Batch Processing**: Parallelize subsidiary searches for better performance
2. **Caching**: Cache subsidiary search results across sessions
3. **Filtering**: Add filters for jurisdiction, status, etc.
4. **Export**: Export conglomerate search results to PDF/CSV
5. **Retry Logic**: Add retry mechanism for failed searches
6. **Alternative Sources**: Use additional data sources beyond OpenCorporates
7. ~~**API Integration**: Direct OpenCorporates API integration if available~~ ✅ **IMPLEMENTED**

## Configuration

No configuration changes required. Feature uses existing:
- Ollama LLM connection (localhost:11434)
- DuckDuckGo search (no API key needed)
- Existing database schema

## Dependencies

- All existing dependencies
- No new packages required

## Deployment Notes

1. Ensure Ollama is running before testing
2. Clear browser cache if UI doesn't update
3. Test with known companies with subsidiaries (e.g., Huawei, Apple, Microsoft)
4. Monitor performance with large subsidiary lists

## Version
- Implementation Version: 1.0
- Application Version: 2.0.0
- Compatible with existing codebase

## Author
Implemented according to detailed plan provided by user
