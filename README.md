# Entity Background Check Bot - Intelligence Operations System

> **Version 2.1.0** | Advanced sanctions screening and entity intelligence platform with AI-powered analysis

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [Usage Guide](#usage-guide)
  - [Basic Search](#basic-search)
  - [Conglomerate Search](#conglomerate-search)
  - [Reverse Search](#reverse-search)
  - [Financial Intelligence](#financial-intelligence)
  - [Save & Restore](#save--restore)
- [Data Sources](#data-sources)
- [Architecture](#architecture)
- [Export & Reporting](#export--reporting)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Version History](#version-history)

---

## Overview

The **Entity Background Check Bot** is a comprehensive intelligence analysis system that combines multiple data sources to provide deep insights into entities, companies, and individuals for sanctions screening, compliance, and due diligence.

### What It Does

- **Sanctions Screening**: Check entities against USA sanctions databases (OFAC, BIS, etc.)
- **Conglomerate Analysis**: Map corporate structures with subsidiaries and sister companies
- **Financial Intelligence**: Extract directors, shareholders, and transactions from SEC filings
- **OSINT Research**: Gather media coverage and intelligence from public sources
- **AI Analysis**: Generate comprehensive intelligence reports using LLM analysis
- **Relationship Mapping**: Visualize entity relationships in Neo4j-style interactive graphs
- **Save & Restore**: Save complete searches and restore them instantly without re-running APIs

### Built For

- Compliance Officers
- Risk Analysts
- Due Diligence Teams
- Legal Departments
- Financial Investigators
- Government Agencies

---

## Key Features

### 1. 🔍 Multi-Source Sanctions Screening

- **USA Sanctions Databases**: OFAC, BIS Entity List, Treasury, State Department
- **Local Databases**: DOD Section 1260H, FCC Covered List
- **Fuzzy Matching**: Advanced name matching with configurable thresholds
- **Risk Scoring**: 5-level risk assessment (SAFE, LOW, MID, HIGH, VERY HIGH)
- **Combined Scoring**: Integrates name similarity, type matching, and address verification

### 2. 🏢 Conglomerate Search

Map complete corporate structures:

- **Multi-Level Depth**: Search 1-3 levels deep through subsidiaries
- **Ownership Filtering**: Filter by ownership percentage (100%, >50%, or custom threshold)
- **Multiple Data Sources**:
  - SEC EDGAR filings (10-K, 20-F)
  - OpenCorporates API
  - Wikipedia extraction
  - DuckDuckGo fallback
- **Sister Companies**: Find other entities owned by the same parent
- **Selective Processing**: Choose which subsidiaries to analyze at each level

### 3. 🔄 Reverse Search

- Search for a subsidiary to find its parent company
- Automatically discover sister companies (other subsidiaries of the same parent)
- Useful for understanding corporate ownership chains

### 4. 💼 Financial Intelligence (SEC EDGAR)

Extract from SEC filings:

- **Directors & Officers**: Names, titles, nationalities, biographies
- **Major Shareholders**: Ownership percentages, voting rights, jurisdictions
- **Related Party Transactions**: Counterparties, amounts, relationships
- **Automatic Sanctions Cross-Check**: Flag directors/shareholders on sanctions lists
- **Filing Sources**: 10-K (US companies), 20-F (foreign issuers), DEF 14A (proxy statements)

### 5. 🌐 Relationship Diagrams

Interactive Neo4j-style network visualizations:

- **Network View**: Drag, zoom, and explore entity relationships
- **Geographic View**: Map entities by jurisdiction
- **Graph Explorer**: Query relationships and find paths between entities
- **Filter Controls**: Show/hide directors, shareholders, transactions
- **Path Finder**: Discover connection chains between any two entities

### 6. 💾 Save & Restore (NEW in 2.1.0)

**Never lose a search again:**

- **Auto-Save**: Every search automatically saved to database
- **One-Click Restore**: Load previous searches in < 2 seconds (no API calls)
- **Complete Data**: Restores all results, reports, diagrams, and financial intel
- **Notes & Tags**: Organize searches with custom notes and tags
- **Export**: Download as JSON, Excel (multi-sheet), or PDF
- **Search History**: Filter and sort saved searches by entity, tags, risk level, or date
- **Speedup**: 15-300x faster than re-running search

**Performance**:
- Save: < 5 seconds (even 100+ subsidiaries)
- Restore: < 2 seconds (any size)
- Storage: ~50KB - 5MB per search

### 7. 🤖 AI Intelligence Reports

LLM-powered analysis includes:

- Executive summary with risk assessment
- Detailed sanctions analysis
- Media coverage synthesis
- Geopolitical context
- Recommendations for further investigation
- PDF export

### 8. 📊 OSINT & Media Intelligence

- **Official Sources**: Government press releases, sanctions announcements
- **General Media**: News articles, blog posts, investigative reports
- **Source Verification**: Distinguishes official vs. general sources
- **Relevance Scoring**: Prioritizes most relevant findings

---

## Quick Start

### Prerequisites

```bash
# Python 3.8+
pip install -r requirements.txt
```

### Required Environment Variables

Create a `.env` file:

```bash
# LLM API (choose one)
OPENAI_API_KEY=your_openai_key
# or
ANTHROPIC_API_KEY=your_anthropic_key

# Optional: OpenCorporates API for enhanced conglomerate search
OPENCORPORATES_API_KEY=your_opencorporates_key
```

### Installation

```bash
# Clone repository
cd "/path/to/sanctions free"

# Install dependencies
pip install -r requirements.txt

# Initialize database
python3 -c "import database as db; db.init_db()"

# (Optional) Load external sources
python3 load_external_sources.py --all

# Start application
streamlit run app.py
```

### First Run

1. Open browser to http://localhost:8501
2. Enable auto-save in ⚙️ SETTINGS (enabled by default)
3. Try a test search: "Huawei" with country "CN"
4. Review results in all tabs
5. Check "📜 SAVED SEARCH HISTORY" to see saved search
6. Click "📂 Restore" to reload instantly

---

## Usage Guide

### Basic Search

**Purpose**: Check if a single entity is sanctioned

**Steps**:
1. Enter entity name (e.g., "Huawei Technologies")
2. Select country of origin (or GLOBAL)
3. Enable "FUZZY LOGIC" for name variations
4. Click "EXECUTE QUERY"

**Results Include**:
- Sanctions matches with scores
- Media coverage (official + general sources)
- AI intelligence report
- Risk level assessment
- PDF export

---

### Conglomerate Search

**Purpose**: Map corporate structures and find all subsidiaries

**When to Use**:
- Compliance screening of large corporations
- Understanding ownership structures
- Finding hidden subsidiaries
- Comprehensive due diligence

**Steps**:
1. Enter parent company name (e.g., "Alibaba Group")
2. Enable "CONGLOMERATE SEARCH"
3. Set search depth (1-3)
4. Set ownership threshold
5. Click "EXECUTE QUERY"

**Data Sources** (in priority order):
1. SEC EDGAR (10-K, 20-F filings) - Most comprehensive
2. OpenCorporates API (if API key provided) - Global coverage
3. Wikipedia - For major corporations
4. DuckDuckGo - Fallback search

---

### Reverse Search

**Purpose**: Find parent company and sister companies of a subsidiary

**Steps**:
1. Enter subsidiary name (e.g., "Lazada")
2. **Disable** "CONGLOMERATE SEARCH"
3. **Enable** "SEARCH FOR PARENT & SISTERS"
4. Click "EXECUTE QUERY"

---

### Financial Intelligence

**Purpose**: Extract key personnel and ownership data from SEC filings

**Automatic Extraction**:
When conglomerate search finds a company with SEC filings, the system automatically extracts:

- **Directors & Officers**: Names, titles, nationalities, biographies
- **Major Shareholders**: Ownership %, voting rights, jurisdictions
- **Related Party Transactions**: Amounts, counterparties, relationships
- **Sanctions Cross-Check**: Auto-checks all directors and shareholders

**Data Sources**:
- **10-K**: Annual reports (US companies)
- **20-F**: Annual reports (foreign issuers)
- **DEF 14A**: Proxy statements (detailed governance)

---

### Save & Restore

**Purpose**: Save searches for later review without re-running expensive API calls

#### Auto-Save (Recommended)

**Setup**:
1. Open **⚙️ SETTINGS** expander
2. Ensure "Auto-save all searches" is **checked** (default)
3. Every search automatically saved

**What Gets Saved**:
- All sanctions matches
- Media hits and sources
- Intelligence report & PDF
- Conglomerate data (subsidiaries, sisters)
- Financial intelligence (directors, shareholders, transactions)
- Relationship diagrams
- Search parameters

#### Manual Save

**Steps**:
1. After search completes, go to **"💾 SAVE & EXPORT"** section
2. Click **"💾 SAVE SEARCH"**
3. Add notes and tags
4. Click **"Save"**

#### Restore Search

**Steps**:
1. Open **"📜 SAVED SEARCH HISTORY"** expander
2. Use filters (entity name, tags, sort)
3. Find your saved search
4. Click **"📂 Restore"** button

**Result**:
- Page refreshes in < 2 seconds
- Banner: "📂 Displaying Restored Search - No API calls were made"
- Complete results displayed instantly

**Performance**:
- Fresh Search: 30 seconds - 10 minutes
- Restored Search: < 2 seconds
- **Speedup: 15-300x faster**

#### Search History Management

**Actions** (per search):
- **📂 Restore**: Load search results
- **📤 Export**: Download as JSON, Excel, or PDF
- **✏️ Edit**: Update notes and tags
- **🗑️ Delete**: Permanently remove search

#### Export Formats

**JSON Export**:
- Complete search data structure
- Use Case: Data integration, backup

**Excel Export** (Multi-Sheet):
- Summary, Sanctions Matches, Media Coverage
- Subsidiaries, Sisters, Directors, Shareholders
- Transactions, Intelligence Report
- Use Case: Team collaboration, analysis

**PDF Export**:
- Intelligence report as formatted PDF
- Use Case: Formal documentation

#### Storage

**Database Location**: `sanctions.db`

**Storage Estimates**:
| Search Type | Per Search | 100 Searches |
|-------------|------------|--------------|
| Basic | 50-200 KB | 5-20 MB |
| Conglomerate (10 subs) | 500 KB - 1 MB | 50-100 MB |
| Conglomerate (100 subs) | 2-5 MB | 200-500 MB |

**Recommendations**:
- Backup database weekly
- Monitor size if > 1 GB
- Delete old test searches regularly

---

## Data Sources

### 1. USA Sanctions Databases

**Primary Source**: USA Sanctions Search API
- OFAC SDN List
- BIS Entity List
- State Department Nonproliferation Sanctions
- Commerce Unverified List
- Treasury Sanctions Programs

**Coverage**: 15,000+ sanctioned entities

### 2. Local External Sources

**DOD Section 1260H** (Chinese Military Companies):
- ~60 entities designated under NDAA
- Refresh via UI or CLI

**FCC Covered List** (Communications Equipment):
- ~100+ entities posing national security risk
- Includes equipment manufacturers

### 3. SEC EDGAR (Financial Intelligence)

- API: https://data.sec.gov/
- Filing types: 10-K, 20-F, DEF 14A
- Directors, shareholders, transactions

### 4. OpenCorporates API (Conglomerate Search)

- Global corporate registry data
- Subsidiary relationships
- Optional API key

### 5. OSINT Sources

- DuckDuckGo Search API
- Government press releases
- News articles and media

---

## Architecture

### Technology Stack

**Frontend**: Streamlit, Plotly, Folium, PyVis
**Backend**: Python 3.8+, SQLite, pandas
**AI/LLM**: OpenAI GPT-4 or Anthropic Claude
**Data Processing**: BeautifulSoup, PyPDF2, fuzzywuzzy, geopy

### File Structure

```
sanctions-free/
├── app.py                          # Main Streamlit application
├── database.py                     # Database operations (SQLite)
├── usa_agent.py                    # USA sanctions API agent
├── research_agent.py               # OSINT and LLM agent
├── graph_builder.py                # Relationship graph construction
├── visualizations.py               # Interactive visualizations
├── serialization_utils.py          # Save/restore data serialization
├── export_utils.py                 # Export functionality
├── load_external_sources.py        # DOD/FCC data ingestion
├── config.py                       # Configuration settings
├── requirements.txt                # Python dependencies
├── sanctions.db                    # SQLite database
└── README.md                       # This file
```

### Database Schema

**Core Tables**:
- `analysis_history`: Basic search history
- `saved_searches`: Complete search results with all data
- `local_entities`: DOD 1260H and FCC Covered List
- `directors_officers`: SEC EDGAR directors
- `major_shareholders`: SEC EDGAR shareholders
- `related_party_transactions`: SEC EDGAR transactions
- `search_comparisons`: Search comparison sessions (future)

---

## Export & Reporting

### Intelligence Report (PDF)

**Contents**:
- Executive summary with risk assessment
- Sanctions analysis
- Media intelligence
- Geopolitical context
- Recommendations

### Excel Export (Multi-Sheet)

**Sheets**: Summary, Sanctions Matches, Media Coverage, Subsidiaries, Sisters, Directors, Shareholders, Transactions, Intelligence Report

### JSON Export

Complete search data structure for system integration

---

## Troubleshooting

### Common Issues

#### Issue: "No results found" for known sanctioned entity

**Solutions**:
1. Enable "FUZZY LOGIC" toggle
2. Try alternative name spellings
3. Search in entity's primary language (auto-translates)
4. Try GLOBAL country filter

#### Issue: Conglomerate search finds no subsidiaries

**Solutions**:
1. Try exact official company name
2. Check if company has SEC filings
3. Try parent company if searching subsidiary

#### Issue: Auto-save not working

**Solution**: Toggle auto-save off and on in ⚙️ SETTINGS

#### Issue: Restore button doesn't work

**Solution**: Refresh page and try again, check browser console

#### Issue: Export buttons don't appear

**Solution**: Save search manually first, then try export

---

## Development

### Setup Development Environment

```bash
# Clone and setup
cd "/path/to/sanctions free"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with API keys

# Initialize database
python3 -c "import database as db; db.init_db()"

# Run application
streamlit run app.py
```

### Testing

**Unit Tests**:
```bash
python3 -m pytest tests/
```

**Integration Tests**:
```bash
# Test database
python3 -c "import database as db; db.init_db(); print('✓ DB OK')"

# Test serialization
python3 -c "import serialization_utils; print('✓ Serialization OK')"
```

---

## Version History

### Version 2.1.0 (2026-03-09) - Save & Restore Feature

**New Features**:
- ✨ Auto-save all searches to database
- ✨ One-click restore in < 2 seconds
- ✨ Enhanced search history with filtering
- ✨ Export as JSON, Excel, or PDF
- ✨ Edit notes and tags
- ✨ Settings panel with auto-save toggle

**Performance**:
- Save: < 5 seconds
- Restore: < 2 seconds
- Speedup: 15-300x faster

### Version 2.0.0 (2026-02) - Major Feature Release

**New Features**:
- ✨ Conglomerate search (multi-level depth)
- ✨ Reverse search
- ✨ Financial intelligence from SEC EDGAR
- ✨ Interactive Neo4j-style relationship diagrams
- ✨ Geographic visualization
- ✨ Progress tracking

### Version 1.0.0 (2025) - Initial Release

**Core Features**:
- Basic sanctions screening
- USA sanctions database integration
- OSINT media research
- LLM intelligence reports
- Risk level assessment
- PDF export

---

## FAQ

**Q: How accurate is the fuzzy name matching?**
A: Uses Levenshtein distance with configurable threshold (typically 80%+). Always review matches manually.

**Q: Can I search non-English entity names?**
A: Yes! System automatically translates using LLM.

**Q: How often are sanctions databases updated?**
A: USA Sanctions API updated in real-time. Local databases (DOD, FCC) must be manually refreshed.

**Q: Why didn't conglomerate search find all subsidiaries?**
A: Data comes from public sources (SEC, OpenCorporates, Wikipedia). Private subsidiaries may not appear.

**Q: How do I know if restored results are up-to-date?**
A: Restored searches show original search date timestamp. Run fresh search for current data.

---

## Support & Contact

**Documentation**:
- This README (comprehensive guide)
- `dev-logs.md` (development changelog)
- Inline code comments

**Troubleshooting**:
- See Troubleshooting section above
- Check browser console (F12)
- Review Streamlit terminal output

---

## License

Internal use only. Not for public distribution.

---

## Acknowledgments

**Data Sources**: USA Sanctions API, SEC EDGAR, OpenCorporates, DuckDuckGo
**Technologies**: Streamlit, OpenAI/Anthropic, SQLite, Python
**Developed By**: IMDA International Team

---

**Version**: 2.1.0
**Last Updated**: 2026-03-09
**Status**: ✅ Production Ready

---

**Quick Links**:
- [Quick Start](#quick-start)
- [Usage Guide](#usage-guide)
- [Save & Restore](#save--restore)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
