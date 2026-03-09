# Save & Restore Search Results - User Guide

## Overview

The Entity Background Check Bot now includes a comprehensive **Save & Restore** feature that allows you to:

- **Auto-save all searches** for future reference
- **Restore previous searches** without re-running expensive API calls
- **Organize searches** with notes and tags
- **Export searches** in multiple formats (JSON, Excel, PDF)
- **Compare searches** to track changes over time

This feature provides significant benefits:
- ⏱️ **Time Savings**: Instantly restore previous searches without waiting
- 💰 **Cost Savings**: Avoid redundant API calls and LLM analysis
- 📊 **Audit Trail**: Maintain complete records of all investigations
- 🤝 **Collaboration**: Share search results with team members
- 🔍 **Trend Analysis**: Track changes in entity status over time

---

## Feature Components

### 1. Auto-Save Settings

**Location**: Settings panel (⚙️ SETTINGS expander)

**How to Use**:
1. Open the "⚙️ SETTINGS" section
2. Check/uncheck "Auto-save all searches"
3. When enabled, every search is automatically saved to the database

**Status Indicators**:
- ✓ **AUTO-SAVED** (green): Search was automatically saved
- **MANUAL MODE** (blue): Auto-save is disabled, manual save required

**Default**: Auto-save is **enabled** by default

---

### 2. Manual Save

**Location**: Save & Export section after search results

**How to Use**:
1. After completing a search, scroll to "💾 SAVE & EXPORT" section
2. Click "💾 SAVE SEARCH" button
3. Fill in the save form:
   - **Notes**: Add context, findings, or reminders about this search
   - **Tags**: Add comma-separated tags (e.g., "high-priority, q1-2026, compliance")
4. Click "Save" to store the search

**Use Cases**:
- Add important context not captured in the automated report
- Tag searches for easy filtering (e.g., by project, priority, or client)
- Save searches when auto-save is disabled

---

### 3. Search History Browser

**Location**: "📜 SAVED SEARCH HISTORY" expander at bottom of page

**Features**:

#### Filtering & Search
- **Entity Name Filter**: Search for specific entities
- **Tag Filter**: Filter by one or multiple tags
- **Sort Options**:
  - Date (newest/oldest)
  - Risk Level (highest to lowest)
  - Entity Name (alphabetical)

#### Search List View
Each saved search displays:
- Entity name and search timestamp
- Risk level (color-coded: VERY HIGH → SAFE)
- Match count, subsidiary count, sister count
- Country filter, fuzzy search status
- Tags and notes
- Auto-saved vs. manually saved status

#### Action Buttons
Each search has 4 action buttons:

1. **📂 Restore**: Load the complete search without re-running APIs
2. **📤 Export**: Export as JSON, Excel, or PDF
3. **✏️ Edit**: Edit notes and tags
4. **🗑️ Delete**: Remove the search from history

---

### 4. Restore Search

**How It Works**:
1. Open "📜 SAVED SEARCH HISTORY"
2. Find the search you want to restore
3. Click "📂 Restore"
4. The complete search results are loaded instantly

**What Gets Restored**:
- All sanctions matches with scores
- Media hits (OSINT/news articles)
- Intelligence report
- PDF export (if generated)
- Conglomerate data (subsidiaries, sisters, directors, shareholders)
- Relationship diagrams and financial intelligence
- Search parameters (country, fuzzy search settings)

**Benefits**:
- **No API calls**: Results load in under 2 seconds
- **No cost**: Avoid re-running expensive LLM analysis
- **Exact snapshot**: See results exactly as they were at search time
- **Full functionality**: All tabs, visualizations, and exports work normally

**Visual Indicator**:
When viewing a restored search, you'll see:
```
📂 Displaying Restored Search - No API calls were made
```

**Return to New Search**:
Click "🔄 Start New Search" to clear the restored search and perform a new query.

---

### 5. Export Searches

**Formats Available**:

#### JSON Export
- Complete search data in structured JSON format
- Includes all metadata, results, and parameters
- Excludes binary PDF data (use PDF export for that)
- **Use Case**: Data integration, backup, programmatic access

#### Excel Export
Multi-sheet workbook containing:
- **Summary**: Entity name, date, risk level, match counts
- **Sanctions Matches**: All sanctions database hits
- **Media Coverage**: OSINT and news articles
- **Subsidiaries**: Subsidiary companies (if conglomerate search)
- **Sister Companies**: Sister companies (if applicable)
- **Directors**: Directors and officers (from SEC filings)
- **Shareholders**: Major shareholders (from SEC filings)
- **Transactions**: Related party transactions (from SEC filings)
- **Intelligence Report**: Full text report

**Use Case**: Sharing with team, Excel analysis, reports

#### PDF Export
- Intelligence report as formatted PDF
- Same PDF generated during original search
- **Use Case**: Formal reports, documentation, archival

---

### 6. Edit Search Metadata

**How to Use**:
1. In search history, click "✏️ Edit" for any search
2. Update notes and/or tags
3. Click "Save Changes"

**Use Cases**:
- Add follow-up notes after investigation
- Update tags as projects evolve
- Correct mistakes in original notes

---

### 7. Delete Searches

**How to Use**:
1. In search history, click "🗑️ Delete" for any search
2. Search is permanently removed from database

**When to Delete**:
- Test searches
- Duplicate searches
- Outdated searches no longer relevant

**Note**: Deletion is permanent and cannot be undone.

---

## Workflow Examples

### Example 1: Quick Investigation with Auto-Save

**Scenario**: You need to check if "Alibaba Group" is sanctioned.

**Steps**:
1. Ensure auto-save is enabled (⚙️ SETTINGS)
2. Enter "Alibaba Group" and click "EXECUTE QUERY"
3. Review results
4. Search is automatically saved in the background
5. Toast notification appears: "✓ Search auto-saved"

**Later** (1 week later):
1. Open "📜 SAVED SEARCH HISTORY"
2. Find "Alibaba Group" search from last week
3. Click "📂 Restore"
4. Results appear instantly (< 2 seconds)
5. Review previous findings without re-running analysis

**Time Saved**: ~30-60 seconds (no API calls, no LLM analysis)

---

### Example 2: Detailed Investigation with Notes & Tags

**Scenario**: Investigating "Huawei Technologies" for a compliance audit.

**Steps**:
1. Search "Huawei Technologies" with conglomerate mode
2. Review sanctions matches, subsidiaries, media hits
3. Click "💾 SAVE SEARCH" (even if auto-save is on, to add notes)
4. Add notes:
   ```
   Compliance audit Q1 2026. Found 3 subsidiaries on sanctions list.
   Recommend further investigation of Huawei Cloud division.
   Follow-up meeting scheduled with legal team 2026-03-15.
   ```
5. Add tags: `compliance-audit, q1-2026, high-priority, legal-review`
6. Click "Save"

**Later** (for audit report):
1. Open search history
2. Filter by tag: `compliance-audit`
3. Find Huawei search
4. Click "📤 Export" → "📥 Download Excel"
5. Excel workbook includes all subsidiaries, sanctions matches, and your notes
6. Share with legal team

---

### Example 3: Tracking Changes Over Time

**Scenario**: Monitor "ZTE Corporation" quarterly to track sanctions status.

**Steps**:

**Q1 Search** (January 2026):
1. Search "ZTE Corporation"
2. Auto-saved with timestamp
3. Result: 2 sanctions matches, Risk Level: MID

**Q2 Search** (April 2026):
1. Search "ZTE Corporation" again
2. Auto-saved with new timestamp
3. Result: 5 sanctions matches, Risk Level: HIGH

**Comparison**:
1. Open search history
2. Filter by "ZTE Corporation"
3. See both searches (Q1 and Q2)
4. Compare results:
   - Q1: 2 matches, MID risk
   - Q2: 5 matches, HIGH risk
5. Action: Risk level increased, escalate to management

**Future Enhancement**: Automated comparison view (coming soon)

---

## Database Schema

### Saved Searches Table

The `saved_searches` table stores complete search results:

**Metadata Fields**:
- `search_id`: Unique identifier
- `timestamp`: Search execution time
- `entity_name`: Searched entity name
- `translated_name`: Translated name (if applicable)

**Search Parameters**:
- `country_filter`: Country filter (GLOBAL, CN, RU, etc.)
- `fuzzy_search`: Fuzzy search enabled (0/1)
- `is_conglomerate`: Conglomerate mode (0/1)
- `is_reverse_search`: Reverse search mode (0/1)
- `search_depth`: Search depth (1-3)
- `ownership_threshold`: Ownership filter percentage

**Summary Metrics** (for quick display):
- `match_count`: Number of sanctions matches
- `risk_level`: SAFE, LOW, MID, HIGH, VERY HIGH
- `subsidiary_count`: Number of subsidiaries found
- `sister_count`: Number of sister companies found

**User Metadata**:
- `notes`: User-added notes
- `tags`: JSON array of tags
- `is_auto_saved`: Auto-saved (1) vs. manual (0)

**Results Data** (JSON/BLOB):
- `sanctions_data`: All sanctions matches (JSON)
- `media_data`: All media hits (JSON)
- `report_text`: Intelligence report (TEXT)
- `pdf_data`: PDF bytes (BLOB)
- `conglomerate_data`: Subsidiaries, sisters, financial intel (JSON)

**Access Tracking**:
- `last_accessed`: Last restore timestamp
- `access_count`: Number of times restored

**Sharing** (future feature):
- `is_shared`: Search is shared (0/1)
- `share_token`: Shareable link token

---

## Storage Considerations

### Storage Estimates

**Per Search**:
- Basic search (no conglomerate): ~50-200 KB
- Conglomerate search (10 subsidiaries): ~500 KB - 1 MB
- Conglomerate search (100 subsidiaries): ~2-5 MB
- PDF data: ~100-500 KB

**100 Searches**:
- Basic searches: ~5-20 MB
- Mixed searches: ~50-100 MB

**1000 Searches**:
- ~500 MB - 1 GB

### Database Location

Database file: `sanctions.db` (SQLite)

**Backup Recommendation**: Regularly backup the database file to prevent data loss.

---

## Troubleshooting

### Issue: Auto-save not working

**Solution**:
1. Check "⚙️ SETTINGS" → "Auto-save all searches" is checked
2. Verify you see "✓ AUTO-SAVED" indicator after search completes
3. Check search history to confirm saves

### Issue: Restored search missing data

**Possible Causes**:
- Database corruption
- Incomplete save (interrupted search)
- Very old search with deprecated data format

**Solution**:
- Delete corrupted search
- Re-run search and save again

### Issue: Export buttons not working

**Solution**:
1. Ensure search is saved (check search history)
2. Try restoring search first, then export
3. Check browser console for errors

### Issue: Search history is slow to load

**Cause**: Too many saved searches (> 1000)

**Solution**:
1. Use filters to narrow results
2. Delete old/unnecessary searches
3. Consider implementing archival/cleanup (future feature)

---

## Best Practices

### 1. Tag Naming Conventions

**Recommended Tags**:
- **Priority**: `high-priority`, `medium-priority`, `low-priority`
- **Status**: `pending-review`, `approved`, `rejected`, `escalated`
- **Projects**: `q1-2026`, `audit-2026`, `client-abc`
- **Type**: `compliance`, `due-diligence`, `risk-assessment`
- **Action**: `follow-up-needed`, `legal-review`, `approved-for-business`

**Example**:
```
Tags: high-priority, q1-2026, compliance, legal-review
```

### 2. Note-Taking

**Good Note Example**:
```
Initial screening for vendor onboarding. Found 2 subsidiaries on OFAC list.
Risk assessment: MEDIUM. Recommended action: Request additional documentation
from vendor explaining relationship with sanctioned entities.
Follow-up: Legal team to review by 2026-03-20.
Contact: John Doe (john@example.com)
```

**Poor Note Example**:
```
Has issues
```

**Tips**:
- Include date and context
- Mention specific findings
- Add action items and deadlines
- Include contact information
- Use clear, concise language

### 3. Regular Cleanup

**Weekly**:
- Review auto-saved searches
- Delete test/duplicate searches
- Add notes/tags to important searches

**Monthly**:
- Export important searches as backup
- Archive old searches (if using external system)
- Review storage usage

### 4. Backup Strategy

**Recommended**:
1. Weekly backup of `sanctions.db`
2. Export critical searches as Excel
3. Store backups in secure location
4. Test restore process quarterly

---

## Future Enhancements

### Planned Features

1. **Comparison View**: Side-by-side comparison of multiple searches
2. **Share Links**: Generate shareable links for read-only access
3. **Automated Monitoring**: Schedule recurring searches and get alerts on changes
4. **Bulk Operations**: Export/delete multiple searches at once
5. **Search Templates**: Save search parameters as reusable templates
6. **Advanced Filtering**: Filter by risk level, date range, search type
7. **Cloud Sync**: Sync searches across devices
8. **Team Workspaces**: Shared search repositories for teams

---

## API Reference

### Database Functions

#### `save_search_results(search_id, entity_name, translated_name, search_params, results_data, summary_metrics, user_metadata=None)`
Save complete search results to database.

#### `load_search_results(search_id)`
Load complete search results from database.

#### `get_saved_searches(limit=50, filters=None)`
Get list of saved searches with optional filtering.

#### `update_search_metadata(search_id, notes=None, tags=None)`
Update notes and tags for a saved search.

#### `delete_saved_search(search_id)`
Delete a saved search from database.

#### `get_all_tags()`
Get all unique tags from saved searches.

### Serialization Functions

#### `serialize_search_results(results_data)`
Convert complex search results into database-serializable format.

#### `deserialize_search_results(db_row)`
Convert database row back into original data structures.

#### `generate_search_id()`
Generate a unique search ID.

#### `parse_tags(tags_input)`
Parse comma-separated tags for database storage.

### Export Functions

#### `export_search_json(search_data, entity_name)`
Export search data as JSON bytes.

#### `export_search_excel(search_data, entity_name)`
Export search data as Excel workbook.

---

## Technical Details

### Data Flow

1. **Search Execution**:
   ```
   User Input → API Calls → LLM Analysis → Results Display
   ```

2. **Auto-Save**:
   ```
   Results → Serialize → Calculate Metrics → Save to DB → Toast Notification
   ```

3. **Restore**:
   ```
   User Click → Load from DB → Deserialize → Display Results (skip APIs)
   ```

### Performance

**Save Operation**:
- Basic search: < 1 second
- Conglomerate search (100 subsidiaries): 2-5 seconds

**Restore Operation**:
- Any search size: < 2 seconds
- No network calls
- No LLM processing

**Comparison** (for 100-subsidiary conglomerate search):
- Fresh search: 5-10 minutes (API calls + LLM)
- Restored search: < 2 seconds
- **Speedup**: 150-300x faster

---

## Support

For issues, questions, or feature requests, please check:
- This documentation
- Developer logs (`dev-logs.md`)
- Implementation notes (`IMPLEMENTATION_COMPLETE.md`)

---

**Version**: 2.1.0
**Last Updated**: 2026-03-09
**Feature Status**: ✅ Production Ready
