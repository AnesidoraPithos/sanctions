# SEC EDGAR Source Links - Documentation

## Overview

When subsidiaries are found via **SEC EDGAR**, the system now provides a **direct link** to the original Exhibit 21 document where the subsidiary list was obtained. This provides transparency and allows you to verify the source data directly.

---

## What You'll See

### In the UI

When you search for a US public company, you'll see:

```
╔════════════════════════════════════════════════════════════╗
║  Found 13 subsidiaries and 0 sister companies for Apple Inc║
║  Search Method: SEC EDGAR (10-K Filings)                   ║
║  📋 View Original SEC Exhibit 21 (Filed: 2025-10-31)       ║
╚════════════════════════════════════════════════════════════╝
```

The **"View Original SEC Exhibit 21"** link is **clickable** and opens the actual SEC filing in a new tab.

---

## What the Link Shows

When you click the link, you'll see:

### Original Exhibit 21 Document
- **Official SEC filing** from the company's 10-K annual report
- **Legal document** listing all subsidiaries
- **Jurisdiction information** for each subsidiary
- **Filed and verified** by company executives

### Example: Apple Inc's Exhibit 21
```
URL: https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/a10-kexhibit21109272025.htm

Document shows:
┌────────────────────────────────────────┬─────────────────────┐
│ Name of Subsidiary                     │ Jurisdiction        │
├────────────────────────────────────────┼─────────────────────┤
│ Apple Asia Limited                     │ Hong Kong           │
│ Apple Asia LLC                         │ Delaware, U.S.      │
│ Apple Canada Inc.                      │ Canada              │
│ Apple Computer Trading (Shanghai)...   │ China               │
│ Apple Distribution International Ltd   │ Ireland             │
│ ... (and more)                         │                     │
└────────────────────────────────────────┴─────────────────────┘
```

---

## When the Link Appears

### ✅ Link Available
- **SEC EDGAR method** used
- US public company
- Recent 10-K filing found
- Exhibit 21 successfully located

**Badge shows:**
- "SEC EDGAR (10-K Filings)" - Link available for subsidiaries
- "SEC EDGAR + DuckDuckGo" - Link available for subsidiaries (not sisters)

### ❌ Link Not Available
- **OpenCorporates API** - No single source document
- **DuckDuckGo Search** - Multiple web sources, no single document
- **Private companies** - Don't file with SEC
- **Non-US companies** - Not in SEC database

---

## Technical Details

### URL Format

SEC EDGAR URLs follow this pattern:
```
https://www.sec.gov/Archives/edgar/data/{CIK}/{ACCESSION}/{EXHIBIT_FILENAME}

Example:
https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/a10-kexhibit21109272025.htm
                                         ^^^^^^  ^^^^^^^^^^^^^^^^^^  ^^^^^^^^^^^^^^^^^^^^^^^^
                                         CIK     Accession Number    Exhibit 21 Filename
```

**Components:**
- **CIK**: Company's Central Index Key (e.g., 320193 for Apple)
- **Accession**: Unique filing ID (e.g., 000032019325000079)
- **Filename**: Exhibit 21 document name (varies by company)

### Filing Date

The filing date shows when the 10-K was submitted to SEC:
- Format: YYYY-MM-DD
- Example: "2025-10-31" (October 31, 2025)
- Represents the most recent 10-K filing

---

## Use Cases

### 1. Verification
**Scenario:** You need to verify that a subsidiary is officially listed

**Action:**
1. Click "View Original SEC Exhibit 21"
2. Search (Ctrl+F) for the subsidiary name
3. Verify it appears in the official filing

### 2. Audit Trail
**Scenario:** Creating a compliance report

**Action:**
1. Copy the SEC Exhibit 21 URL
2. Include it in your report as the source citation
3. Screenshot the Exhibit 21 page for documentation

**Example Citation:**
```
Source: Apple Inc. Form 10-K, Exhibit 21
Filed: October 31, 2025
URL: https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/a10-kexhibit21109272025.htm
```

### 3. Additional Information
**Scenario:** You want more details about a subsidiary

**Action:**
1. Open the Exhibit 21 link
2. Review additional details that may be in the filing:
   - Ownership percentages (sometimes included)
   - Notes about specific subsidiaries
   - Changes from previous year

### 4. Historical Comparison
**Scenario:** Track how subsidiaries changed over time

**Action:**
1. Access current year's Exhibit 21 (via link)
2. Navigate to previous 10-K filings on SEC
3. Compare subsidiary lists year-over-year

---

## Example Workflows

### Workflow 1: Disney Search

**Step 1:** Search for "Disney" with conglomerate enabled

**Result:**
```
Found 20 subsidiaries and 0 sister companies for Walt Disney Co
Search Method: SEC EDGAR (10-K Filings)
📋 View Original SEC Exhibit 21 (Filed: 2024-11-27)
```

**Step 2:** Click the link

**Opens:** https://www.sec.gov/Archives/edgar/data/1001039/.../dis-ex211_8.htm

**Shows:** Official list of Disney's subsidiaries including:
- ABC, Inc.
- ESPN, Inc.
- Marvel Entertainment, LLC
- Pixar
- 20th Century Studios
- ... and more

**Step 3:** Verify specific subsidiary

Press Ctrl+F and search for "Marvel" → Found in official filing ✅

---

### Workflow 2: Mixed Source (SEC + DuckDuckGo)

**Step 1:** Search for "Apple" with sister companies enabled

**Result:**
```
Found 13 subsidiaries and 2 sister companies for Apple Inc
Search Method: SEC EDGAR + DuckDuckGo
📋 View Original SEC Exhibit 21 (Filed: 2025-10-31)
```

**Understanding:**
- **Subsidiaries (13)**: From SEC EDGAR - link shows these
- **Sister companies (2)**: From DuckDuckGo - not in SEC filing (no official source)

**Step 2:** Click the link

**Shows:** Only the 13 subsidiaries (SEC doesn't list sister companies)

**Note:** Link verifies subsidiaries only; sister companies are web-sourced

---

## Benefits

### 1. **Transparency** 🔍
- See exactly where the data came from
- Verify it's from an official legal document
- Build trust in the data quality

### 2. **Auditability** 📋
- Provide source citations for compliance
- Create audit trail for due diligence
- Document your research methodology

### 3. **Verification** ✅
- Cross-check subsidiary information
- Confirm spelling and jurisdictions
- Look for additional notes or details

### 4. **Legal Defensibility** ⚖️
- Based on official SEC filings
- Required by law to be accurate
- Audited by company and regulators

---

## Comparison: Source Links by Method

| Method | Source Link | Why |
|--------|-------------|-----|
| **SEC EDGAR** | ✅ Yes - Direct link to Exhibit 21 | Single official document |
| **OpenCorporates API** | ❌ No link | Data from API, not single document |
| **DuckDuckGo** | ❌ No link | Multiple web sources |

---

## Frequently Asked Questions

### Q: Can I access the full 10-K report, not just Exhibit 21?
**A:** Yes! From the Exhibit 21 page:
1. Look for navigation links at the top
2. Click on the main 10-K document link
3. Or modify the URL to access the index page

**Example:**
```
Exhibit 21: .../a10-kexhibit21109272025.htm
Main 10-K:  .../{accession-number}.htm
Index:      .../{accession-number}-index.htm
```

### Q: Why do some companies show a link and others don't?
**A:** The link only appears when:
- Company is US-listed (trades on US exchanges)
- Search used SEC EDGAR method
- Exhibit 21 was successfully located

Private companies and non-US companies won't have SEC filings.

### Q: Is the link permanent?
**A:** Yes! SEC archives are permanent. The URL will work indefinitely, allowing you to reference it years later.

### Q: What if the link doesn't work?
**A:** Rare, but possible causes:
- SEC website maintenance
- Network issues
- Filing was recently submitted (may take hours to appear)

Try again later or contact SEC if persistent.

### Q: Can I download the Exhibit 21?
**A:** Yes! In your browser:
1. Right-click on the page
2. Select "Save As" or "Print to PDF"
3. Save for offline reference

---

## Technical Implementation

### Data Flow

```
search_sec_edgar_cik()
    ↓
get_latest_10k_filing()
    ↓
extract_subsidiaries_from_10k()
    ↓ (captures exhibit_url)
find_subsidiaries_sec_edgar()
    ↓ (includes source_url in return)
find_subsidiaries()
    ↓ (passes through source_url)
display_subsidiary_selection() [UI]
    ↓ (displays link)
User clicks → Opens SEC Exhibit 21 in new tab
```

### Return Structure

```python
{
    'subsidiaries': [...],
    'sisters': [...],
    'parent': None,
    'method': 'sec_edgar',
    'source_url': 'https://www.sec.gov/Archives/edgar/data/...',  # ← NEW
    'filing_date': '2025-10-31'  # ← NEW
}
```

### UI Display Code

```python
if source_url:
    st.markdown(f"""
        📋 <a href="{source_url}" target="_blank">
            View Original SEC Exhibit 21
        </a> (Filed: {filing_date})
    """)
```

---

## Best Practices

### For Research
1. ✅ Always check the source link when available
2. ✅ Verify critical subsidiaries in the original document
3. ✅ Note the filing date for time-sensitive decisions

### For Compliance
1. ✅ Include source URL in your reports
2. ✅ Screenshot or download Exhibit 21 for records
3. ✅ Document the filing date

### For Due Diligence
1. ✅ Compare web-sourced data against SEC filings
2. ✅ Prioritize SEC EDGAR data for US companies
3. ✅ Use the link to research additional context

---

## Summary

The **SEC source link** feature provides:

- 🔗 **Direct access** to official Exhibit 21 documents
- 📅 **Filing date** for context
- ✅ **Verification** capability
- 📋 **Audit trail** for compliance
- ⚖️ **Legal defensibility**

This transparency helps you understand exactly where each piece of data comes from and allows independent verification of the subsidiary information.

**Example Link:**
https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/a10-kexhibit21109272025.htm

Click it and see Apple's official subsidiary list yourself! 🍎
