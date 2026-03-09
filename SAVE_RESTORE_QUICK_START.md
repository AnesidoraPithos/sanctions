# Save & Restore Feature - Quick Start Guide

## 🚀 Quick Start (5 Minutes)

This guide will help you test the new Save & Restore feature in 5 minutes.

---

## Step 1: Start the Application

```bash
cd "/Users/faith/Desktop/IMDA/International/sanctions free"
streamlit run app.py
```

---

## Step 2: Test Auto-Save

### 2.1 Check Auto-Save Setting
1. Open the **⚙️ SETTINGS** expander
2. Verify "Auto-save all searches" is **checked** (enabled by default)
3. You should see: "✓ All searches will be automatically saved"

### 2.2 Perform a Test Search
1. Go to **01 // SEARCH PARAMS**
2. Enter entity name: **"Huawei"**
3. Select country: **CN**
4. Enable **FUZZY LOGIC** (if not already)
5. Click **"EXECUTE QUERY"**

### 2.3 Verify Auto-Save
1. Wait for search to complete
2. Scroll to **"💾 SAVE & EXPORT"** section
3. You should see:
   - Toast notification: "✓ Search auto-saved (ID: search_...)"
   - Status indicator: "✓ AUTO-SAVED" (green box)

---

## Step 3: Test Restore

### 3.1 Clear Current Search
1. Click the **🗑️** button (next to EXECUTE QUERY)
2. This clears the current results

### 3.2 Open Search History
1. Scroll to bottom of page
2. Open **"📜 SAVED SEARCH HISTORY"** expander

### 3.3 Restore Your Search
1. You should see your "Huawei" search listed
2. Click **"📂 Restore"** button
3. **Expected Result**:
   - Page refreshes in < 2 seconds
   - Banner appears: "📂 Displaying Restored Search - No API calls were made"
   - All search results appear instantly
   - All tabs work normally (sanctions, media, intel report, etc.)

---

## Step 4: Test Manual Save with Notes

### 4.1 Perform Another Search
1. Click **"🔄 Start New Search"** (to clear restored search)
2. Search for: **"Alibaba"**
3. Enable **CONGLOMERATE SEARCH**
4. Click **"EXECUTE QUERY"**
5. When subsidiary selection appears, select a few subsidiaries
6. Click **"PROCEED WITH SELECTED"**
7. Wait for results

### 4.2 Manual Save
1. Scroll to **"💾 SAVE & EXPORT"** section
2. Click **"💾 SAVE SEARCH"** button
3. In the form:
   - **Notes**: "Test search for Alibaba conglomerate. Found 5 subsidiaries."
   - **Tags**: "test, conglomerate, q1-2026"
4. Click **"💾 Save"**
5. You should see: "✓ Search saved! ID: search_..."

---

## Step 5: Test Search History Features

### 5.1 Filter by Entity Name
1. Open **"📜 SAVED SEARCH HISTORY"**
2. In "🔍 Filter by entity name", type: **"Alibaba"**
3. Only Alibaba search should appear

### 5.2 Filter by Tags
1. Clear entity name filter
2. In "🏷️ Filter by tags", select: **"test"**
3. Only searches with "test" tag should appear

### 5.3 Edit Metadata
1. Find your Alibaba search
2. Click **"✏️ Edit"**
3. Add to notes: " - Reviewed by legal team"
4. Add tag: "legal-review"
5. Click **"Save Changes"**
6. Expand the search again and verify changes

---

## Step 6: Test Export

### 6.1 Export from Search History
1. Find your Alibaba search in history
2. Click **"📤 Export"**
3. Three export buttons should appear

### 6.2 Test JSON Export
1. Click **"📥 Download JSON"**
2. A file should download: `search_Alibaba_<id>.json`
3. Open it in a text editor
4. Verify it contains search data, results, notes, and tags

### 6.3 Test Excel Export
1. Click **"📥 Download Excel"**
2. A file should download: `search_Alibaba_<id>.xlsx`
3. Open it in Excel/Numbers/LibreOffice
4. Verify multiple sheets:
   - Summary
   - Sanctions Matches
   - Media Coverage
   - Subsidiaries
   - Sister Companies
   - Intelligence Report

### 6.4 Test PDF Export
1. Click **"📥 Download PDF Report"**
2. A PDF should download: `report_Alibaba_<id>.pdf`
3. Open it
4. Verify it's the intelligence report

---

## Step 7: Test Delete

### 7.1 Delete a Search
1. In search history, find your first "Huawei" search
2. Click **"🗑️ Delete"**
3. You should see: "Search deleted"
4. Search should disappear from list

---

## Step 8: Test Auto-Save Toggle

### 8.1 Disable Auto-Save
1. Go to **⚙️ SETTINGS**
2. **Uncheck** "Auto-save all searches"
3. You should see: "⚠ Manual save required for each search"

### 8.2 Search Without Auto-Save
1. Search for: **"ZTE"**
2. After results appear, check **"💾 SAVE & EXPORT"** section
3. Status indicator should show: **"MANUAL MODE"** (blue box)
4. No toast notification should appear

### 8.3 Manually Save
1. Click **"💾 SAVE SEARCH"**
2. Add notes and tags
3. Click **"💾 Save"**
4. Search is now in history

### 8.4 Re-enable Auto-Save
1. Go to **⚙️ SETTINGS**
2. **Check** "Auto-save all searches" again

---

## ✅ Verification Checklist

After completing all steps, verify:

- [ ] Auto-save works (toast notification appears)
- [ ] Restore works (< 2 seconds, banner appears)
- [ ] Restored search shows all data (sanctions, media, report, PDF)
- [ ] Manual save works (form accepts notes and tags)
- [ ] Search history shows saved searches
- [ ] Entity name filter works
- [ ] Tag filter works
- [ ] Sort options work (try different sorts)
- [ ] Edit metadata works (changes persist)
- [ ] Delete works (search removed)
- [ ] JSON export downloads and is valid
- [ ] Excel export downloads and has multiple sheets
- [ ] PDF export downloads and is readable
- [ ] Auto-save toggle works (on/off)
- [ ] Manual mode indicator shows when auto-save disabled
- [ ] "Start New Search" button clears restored search
- [ ] Conglomerate search save/restore works

---

## Common Issues & Solutions

### Issue: "Auto-save not working"
**Check**:
- Is auto-save checkbox enabled in Settings?
- Do you see "✓ AUTO-SAVED" indicator after search?
- Check search history - is search listed?

**Solution**: Make sure Settings → "Auto-save all searches" is checked

---

### Issue: "Restore button doesn't work"
**Check**:
- Did page refresh?
- Do you see the banner "Displaying Restored Search"?

**Solution**: Check browser console (F12) for errors, refresh page

---

### Issue: "Export buttons don't appear"
**Check**:
- Is search saved? (Check search history)
- Did you click the "📤 Export" button first?

**Solution**: Make sure to click "📤 Export" button to show download options

---

### Issue: "Search history is empty"
**Check**:
- Is auto-save enabled?
- Have you performed any searches since implementing the feature?

**Solution**: Perform a new search with auto-save enabled

---

## Performance Benchmarks

Expected performance:

| Operation | Expected Time |
|-----------|---------------|
| Auto-save (basic search) | < 1 second |
| Auto-save (conglomerate 10 subs) | 1-2 seconds |
| Restore (any size) | < 2 seconds |
| Load search history (50 searches) | < 1 second |
| JSON export | < 1 second |
| Excel export (basic) | 1-2 seconds |
| Excel export (conglomerate 100 subs) | 2-5 seconds |

---

## Advanced Testing (Optional)

### Test Conglomerate Save/Restore
1. Search "Microsoft" with conglomerate mode, depth 2
2. Select 10+ subsidiaries
3. Wait for complete results
4. Should auto-save (may take 2-5 seconds for large search)
5. Restore search
6. Verify all subsidiaries, sisters, directors, shareholders, transactions appear
7. Verify relationship diagram works

### Test Reverse Search Save/Restore
1. Search "LinkedIn" (subsidiary of Microsoft)
2. Enable "SEARCH FOR PARENT & SISTERS"
3. Complete search
4. Should show Microsoft as parent, other subsidiaries as sisters
5. Restore search
6. Verify parent and sisters structure intact

### Stress Test (100 Searches)
1. Enable auto-save
2. Perform 100 different entity searches
3. Check database file size: `ls -lh sanctions.db`
4. Expected size: ~5-50 MB (depending on search types)
5. Test search history performance with filters
6. Test restore speed (should still be < 2 seconds)

---

## Next Steps

After successful testing:

1. **Read Full Documentation**: See `SAVE_RESTORE_FEATURE_GUIDE.md`
2. **Review Implementation**: See `SAVE_RESTORE_IMPLEMENTATION_SUMMARY.md`
3. **Use in Production**: Start using the feature for real investigations
4. **Provide Feedback**: Note any issues or feature requests
5. **Backup Database**: Regularly backup `sanctions.db`

---

## Support

For questions or issues:
- Check the full documentation (`SAVE_RESTORE_FEATURE_GUIDE.md`)
- Review troubleshooting section
- Check implementation summary for technical details

---

**Feature Status**: ✅ Ready for Testing
**Estimated Testing Time**: 10-15 minutes for full test
**Quick Test Time**: 5 minutes (Steps 1-3 only)

---

Enjoy the new Save & Restore feature! 🎉
