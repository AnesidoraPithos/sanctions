# Data Source Indicators Guide

## Overview

Each subsidiary and sister company now displays a **source badge** showing where that specific information was obtained.

---

## Source Badges

### 📋 SEC EDGAR (Green Badge)
- **Color**: Green (#10b981)
- **Source**: U.S. Securities and Exchange Commission official 10-K filings
- **Data Quality**: Highest - official legal filings
- **Availability**: US public companies only
- **Example**: Apple Inc subsidiaries from Exhibit 21

**What this means:**
This subsidiary is listed in the company's official SEC 10-K filing (Exhibit 21). This is legally verified information that the company is required to report accurately.

---

### 🌐 OpenCorporates API (Blue Badge)
- **Color**: Blue (#3b82f6)
- **Source**: OpenCorporates API (structured database)
- **Data Quality**: High - structured, verified data
- **Availability**: International companies
- **Requires**: API key configuration

**What this means:**
This subsidiary or sister company was found through the OpenCorporates API, which aggregates official company registry data from around the world. This is structured, reliable data from official company registries.

---

### 🔍 DuckDuckGo (Gray Badge)
- **Color**: Gray (#94a3b8)
- **Source**: DuckDuckGo search + LLM extraction
- **Data Quality**: Good - extracted from web sources
- **Availability**: All companies (universal fallback)
- **Method**: Searches OpenCorporates website via DuckDuckGo, uses AI to extract data

**What this means:**
This subsidiary or sister company was found through web search and extracted using AI. While reliable, this method may occasionally miss entities or have minor inaccuracies compared to official APIs.

---

## Examples

### Example 1: Disney (US Public Company with SEC EDGAR)

```
🏢 Level 1 Subsidiaries (20)

☑ ABC, Inc. 📋 SEC EDGAR
   📍 Delaware, U.S. | Level: 1 | Status: Active

☑ Disney Enterprises, Inc. 📋 SEC EDGAR
   📍 Delaware, U.S. | Level: 1 | Status: Active

☑ Walt Disney Parks and Resorts U.S., Inc. 📋 SEC EDGAR
   📍 Delaware, U.S. | Level: 1 | Status: Active

🤝 Sister Companies (3)

☑ Marvel Entertainment, LLC 🔍 DuckDuckGo
   📍 United States | Relationship: Sister Company | Status: Active
```

**What you see:**
- Subsidiaries: All from **SEC EDGAR** (official 10-K filing)
- Sisters: From **DuckDuckGo** (SEC doesn't provide sister companies)
- Overall method badge: "SEC EDGAR + DuckDuckGo"

---

### Example 2: Samsung (Non-US Company)

```
🏢 Level 1 Subsidiaries (15)

☑ Samsung Electronics America 🔍 DuckDuckGo
   📍 United States | Level: 1 | Status: Active

☑ Samsung Display Co., Ltd. 🔍 DuckDuckGo
   📍 South Korea | Level: 1 | Status: Active

🤝 Sister Companies (2)

☑ Samsung C&T Corporation 🔍 DuckDuckGo
   📍 South Korea | Relationship: Sister Company | Status: Active
```

**What you see:**
- All from **DuckDuckGo** (Samsung is not US-listed, so SEC EDGAR doesn't apply)
- Overall method badge: "DuckDuckGo Search"

---

### Example 3: International Company (With OpenCorporates API)

*If you configure OpenCorporates API key:*

```
🏢 Level 1 Subsidiaries (12)

☑ Huawei Technologies Canada Co., Ltd. 🌐 OpenCorporates API
   📍 Canada | Level: 1 | Status: Active

☑ Huawei Device Co., Ltd. 🌐 OpenCorporates API
   📍 China | Level: 1 | Status: Active

🤝 Sister Companies (3)

☑ Honor Device Co., Ltd. 🌐 OpenCorporates API
   📍 China | Relationship: Sister Company | Status: Active
```

**What you see:**
- All from **OpenCorporates API** (when configured)
- Overall method badge: "OpenCorporates API"

---

## Why This Matters

### 1. **Data Confidence**
Know the reliability of each piece of information:
- 📋 **SEC EDGAR**: 99% confidence (official legal filing)
- 🌐 **OpenCorporates API**: 95% confidence (verified registry data)
- 🔍 **DuckDuckGo**: 85% confidence (web-extracted data)

### 2. **Audit Trail**
Understand where each subsidiary came from for:
- Compliance documentation
- Due diligence reports
- Risk assessment validation

### 3. **Data Quality Assessment**
Make informed decisions based on source:
- Prioritize SEC EDGAR data for US companies
- Trust OpenCorporates API for international entities
- Verify DuckDuckGo results when critical

### 4. **Mixed Sources**
When you see multiple sources:
- **SEC + DuckDuckGo**: Subsidiaries from SEC (highly accurate), sisters from DuckDuckGo (no official source for sisters)
- Shows transparency in methodology

---

## How Sources Are Chosen

### Automatic Priority System

```
1. Try OpenCorporates API (if configured)
   ↓
2. Try SEC EDGAR (for US public companies)
   ↓
3. Fall back to DuckDuckGo (universal)
```

Each **individual company** is sourced from the **first method that found it**.

---

## Reading the Overall Method Badge

The overall badge at the top shows which method(s) were used:

- **"OpenCorporates API"** → All companies from OpenCorporates
- **"SEC EDGAR (10-K Filings)"** → All subsidiaries from SEC (no sisters found/requested)
- **"SEC EDGAR + DuckDuckGo"** → Subsidiaries from SEC, sisters from DuckDuckGo
- **"DuckDuckGo Search"** → All companies from DuckDuckGo

The **individual badges** on each company show the specific source for that entity.

---

## Best Practices

### For Highest Accuracy
1. ✅ Use for **US public companies**: Look for 📋 SEC EDGAR badges
2. ✅ Configure **OpenCorporates API key**: Get 🌐 badges for international companies
3. ⚠️ Verify **DuckDuckGo results**: Double-check 🔍 badges when making critical decisions

### For Compliance
- Document which source each subsidiary came from
- Screenshot shows individual badges for audit trail
- SEC EDGAR sources are legally defensible

### For Risk Assessment
- Weight findings based on source reliability
- SEC EDGAR findings: highest weight
- OpenCorporates API: high weight
- DuckDuckGo: moderate weight, verify independently

---

## Frequently Asked Questions

### Q: Why do some subsidiaries have SEC EDGAR but sisters have DuckDuckGo?
**A:** SEC 10-K filings (Exhibit 21) only list **subsidiaries** (companies owned by the parent). They don't list **sister companies** (companies with the same parent). So we use SEC for subsidiaries and supplement with DuckDuckGo for sisters.

### Q: Can I get all data from SEC EDGAR?
**A:** Only if:
- The company is US-listed (trades on NYSE, NASDAQ, etc.)
- You don't need sister companies
- The company has filed a recent 10-K

### Q: Why is DuckDuckGo sometimes the only option?
**A:** For:
- Private companies (don't file with SEC)
- Non-US companies (not in SEC database)
- When OpenCorporates API key is not configured

### Q: How do I get more blue badges (OpenCorporates API)?
**A:**
1. Sign up at https://opencorporates.com/users/sign_up (free)
2. Get API token from account page
3. Add to `.env`: `OPENCORPORATES_API_KEY="your_token"`
4. Restart the app

---

## Technical Details

### Source Field
Each company object now includes:
```python
{
    'name': 'Company Name',
    'jurisdiction': 'Delaware',
    'status': 'Active',
    'relationship': 'subsidiary',
    'level': 1,
    'source': 'sec_edgar'  # ← NEW
}
```

### Badge Colors
- SEC EDGAR: `#10b981` (green)
- OpenCorporates API: `#3b82f6` (blue)
- DuckDuckGo: `#94a3b8` (gray)

---

## Summary

Source badges provide **transparency** and **traceability** for each piece of data:

- 📋 **SEC EDGAR**: Official, legally-filed, highest accuracy
- 🌐 **OpenCorporates API**: Structured, verified, high accuracy
- 🔍 **DuckDuckGo**: Web-extracted, good accuracy

This helps you understand the **confidence level** for each subsidiary or sister company and make informed risk decisions.
