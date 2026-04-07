# Value Proposition: Entity Background Check Bot

**Document Version**: 1.0
**System Version**: 2.1.0
**Date**: 2026-03-11
**Audience**: Development Team & Documentation

---

# 1. Value Proposition Statement

Complete the following statement:

**For** (target user)\
**who** (has this problem)\
**our solution** (product / service)\
**that** (key benefit)\
**unlike** (current alternatives)\
**we** (unique advantage).

## Your Value Proposition

**For** international relations staff, compliance officers, and risk analysts\
**who** need to conduct background checks on entities to assess sanctions risk and relationship exposure, and who must answer "Is there risk in associating with this entity?" and "What is the extent (1st/2nd order) of that risk?"\
**our solution** is the Entity Background Research Agent - an AI-powered intelligence operations system with a modern React web interface and three-tiered research system (base/network/deep)\
**that** automates multi-source research with user-controlled depth: quick compliance checks (base tier, 30-60 sec), corporate network analysis (network tier, 2-5 min), or comprehensive investigations (deep tier, 5-15 min) - all accessible through a modern, responsive web interface\
**unlike** manual research processes that require staff to separately query USA sanctions sites (OFAC, BIS, etc.), SEC EDGAR filings, OpenCorporates, and conduct Google searches across scattered interfaces - and unlike rigid tools that provide the same depth regardless of decision importance\
**we** integrate all data sources into a single React/Next.js interface with tier-selectable research depth, REST API backend for integrations, fuzzy name matching, automated SEC EDGAR extraction, real-time progress tracking, relationship mapping, and save/restore functionality that provides 15-300x faster results (< 2 seconds vs 30 seconds - 10 minutes) on subsequent queries.

---

# 2. Problem Statement

Describe the core problem your team is solving.

## What problem exists?

International relations staff receive entity names from stakeholders who want to know: **"Is there any risk working, collaborating, or being associated with that entity?"** and **"What is the extent of the risks involved - first-order, second-order?"** Stakeholders are particularly concerned about how the USA views these entities.

Currently, staff must conduct time-consuming manual research across multiple disconnected systems:

1. **Scattered data sources**: 10+ different sanctions databases (OFAC SDN, BIS Entity List, Treasury, State Department, DOD 1260H, FCC Covered List) require separate searches
2. **Complex corporate structures**: Determining sanctions exposure for conglomerates requires manually searching for subsidiaries, parent companies, and sister companies
3. **Financial intelligence gaps**: SEC EDGAR filings must be manually reviewed to identify directors, shareholders, and related party transactions
4. **Tedious subsidiary screening**: Each subsidiary found must be individually screened against all sanctions lists
5. **Name variation challenges**: Entities may be listed under different names, transliterations, or abbreviations
6. **No research reuse**: Previous searches cannot be easily retrieved, forcing redundant work
7. **Inconsistent methodology**: Research quality varies depending on analyst experience and time available

**Typical time investment**: 30 minutes to several hours per entity, with significantly longer times for complex conglomerates.

## Why does it matter?

- **Decision delays**: Stakeholders waiting for background checks cannot proceed with partnerships, collaborations, or engagements
- **Compliance risk**: Missing sanctions information can result in regulatory violations, legal liability, and reputational damage
- **Inefficiency**: Staff spend significant time on repetitive research tasks that could be automated
- **Incomplete analysis**: Time pressure may lead to incomplete screening of subsidiaries or related entities
- **No institutional memory**: Previous research is not easily accessible for future reference
- **Inconsistent quality**: Manual processes produce variable results depending on thoroughness and expertise

## Who experiences this problem?

**Primary users**:
- **International relations staff**: Receive entity names from stakeholders and must assess risk for engagement decisions
- **Compliance officers**: Responsible for sanctions screening and regulatory adherence
- **Risk analysts**: Evaluate counterparty risk and association exposure

**Secondary users**:
- **Due diligence teams**: Conduct pre-engagement assessments
- **Legal departments**: Review entities for contract and partnership agreements
- **Financial investigators**: Trace ownership structures and financial relationships
- **Government agency analysts**: Screen entities for policy and regulatory purposes

---

# 3. Target Users

Describe the primary users of your solution.

## Primary user group:

**International Relations Staff**

These are professionals who:
- Receive entity names from internal stakeholders (management, partnerships team, business development)
- Are tasked with answering whether there is risk in associating with the entity
- Must assess both direct risk (entity itself) and indirect risk (parent companies, subsidiaries, related entities)
- Need to provide defensible documentation of their findings
- Work under time pressure to enable stakeholder decisions
- May not have deep expertise in sanctions screening or corporate structure analysis

**Key characteristics**:
- Variable technical expertise (from basic to advanced)
- Need clear, actionable outputs (not raw data)
- Require audit trails and exportable reports
- Value speed and completeness over exhaustive manual control
- Work with both English and non-English entity names

## Secondary users (if any):

1. **Compliance Officers**: Ensure organizational adherence to sanctions regulations, conduct periodic screenings
2. **Risk Analysts**: Assess counterparty risk, evaluate relationship exposure, identify hidden connections
3. **Due Diligence Teams**: Pre-engagement screening, merger/acquisition research, partnership evaluation
4. **Legal Departments**: Contract review, regulatory compliance verification, legal risk assessment
5. **Financial Investigators**: Trace ownership structures, investigate financial flows, map related party transactions
6. **Government Agencies**: Policy enforcement, regulatory screening, national security assessments

## Context in which they use the solution:

**Workflow context**:
1. **Reactive requests**: Stakeholder provides entity name → Staff must research quickly to unblock decisions
2. **Pre-engagement due diligence**: Before signing contracts or partnerships → Need comprehensive risk profile
3. **Ongoing monitoring**: Periodic re-screening of existing relationships → Leverage save/restore for updates
4. **Complex structure analysis**: Investigating conglomerates with many subsidiaries → Map full corporate hierarchy
5. **Documentation requirements**: Must provide stakeholders with formal reports → Export to PDF/Excel

**Usage patterns**:
- **Ad-hoc searches**: Single entity queries for immediate decisions (most common)
- **Batch screening**: Multiple related entities from a single stakeholder request
- **Deep investigations**: Conglomerate searches with 2-3 levels of depth for high-risk engagements
- **Historical review**: Restoring previous searches to check if status has changed or to reference findings

**Time sensitivity**:
- **Urgent**: Same-day turnaround required (< 2 hours)
- **Standard**: 1-3 days for comprehensive analysis
- **Deep dive**: 1 week for complex conglomerates with extensive subsidiary networks

**Output requirements**:
- **Internal**: Risk assessment and recommendation for stakeholder decision
- **External**: Formal documentation for contracts, board reports, regulatory filings (PDF/Excel)
- **Audit trail**: Saved searches with timestamps for compliance review

---

# 4. Value Proposition Canvas

## Customer Profile

### Customer Jobs

What users are trying to accomplish.

1. **Determine sanctions status**: Check if entity is on USA sanctions lists (OFAC SDN, BIS Entity List, Treasury, State Department, DOD 1260H, FCC Covered List)
2. **Assess first-order risk**: Identify direct sanctions exposure or regulatory concerns with the entity itself
3. **Assess second-order risk**: Evaluate indirect exposure through parent companies, subsidiaries, and sister companies
4. **Map corporate structures**: Understand ownership hierarchies, subsidiary relationships, and conglomerate boundaries
5. **Identify key personnel**: Find directors, officers, shareholders, and their sanctions status
6. **Trace financial relationships**: Map related party transactions, ownership percentages, and financial flows
7. **Gather public intelligence**: Collect media coverage, government announcements, and OSINT on entity activities
8. **Synthesize findings**: Combine data from multiple sources into coherent risk assessment
9. **Generate documentation**: Create formal reports with evidence and recommendations for stakeholders
10. **Make informed decisions**: Provide stakeholders with defensible basis for engagement/association decisions
11. **Maintain institutional knowledge**: Save and retrieve previous research to avoid redundant work
12. **Monitor changes over time**: Re-screen entities to detect changes in sanctions status or corporate structure

### Pains

Problems, frustrations, or risks users experience.

1. **Time-consuming manual research**: Checking 10+ databases and manually reviewing SEC filings takes 30 minutes to several hours per entity
2. **Scattered data sources**: Multiple logins, interfaces, and search syntaxes across OFAC, BIS, SEC EDGAR, OpenCorporates, Google
3. **Risk of missed information**: Name variations (transliterations, abbreviations, legal entity suffixes) may cause entities to be overlooked
4. **Complex corporate hierarchies**: Difficulty understanding multi-level ownership structures and identifying all relevant subsidiaries
5. **Subsidiary tracking challenges**: Cannot easily keep track of which subsidiaries have been screened vs. not screened
6. **Tedious SEC EDGAR review**: Manually reading 10-K, 20-F, and proxy statements to find directors and shareholders is error-prone and slow
7. **No research reuse**: Previous searches are not easily retrievable, forcing analysts to repeat work for recurring entities
8. **Inconsistent quality**: Research thoroughness varies by analyst skill, time pressure, and fatigue
9. **Lack of documentation standards**: No standardized format for presenting findings to stakeholders
10. **Inability to visualize relationships**: Difficult to explain complex corporate structures and connection paths without diagrams
11. **Name matching uncertainty**: Unsure whether similar names represent the same entity or different entities
12. **Hidden subsidiaries**: May miss subsidiaries that are not prominently listed in public sources
13. **No decision support**: Raw data without interpretation leaves stakeholders unsure how to proceed
14. **Lack of audit trail**: Difficult to justify decisions months/years later when research process is not documented

### Gains

Desired outcomes or benefits.

1. **Faster turnaround**: Complete entity background checks in minutes rather than hours
2. **Comprehensive coverage**: Confidence that all relevant sanctions databases have been checked systematically
3. **Clear relationship visualization**: Interactive diagrams that make complex corporate hierarchies instantly understandable
4. **Automated subsidiary discovery**: System finds subsidiaries automatically rather than relying on manual research
5. **Consistent methodology**: Every analyst uses the same comprehensive research process regardless of experience level
6. **Efficient research reuse**: One-click access to previous searches without repeating expensive API calls
7. **Exportable documentation**: PDF and Excel reports that can be shared with stakeholders and archived for compliance
8. **Reduced sanctions violation risk**: Systematic screening reduces likelihood of missing critical information
9. **Financial transparency**: SEC EDGAR extraction reveals ownership structures and related party transactions automatically
10. **Strategic insights**: Relationship mapping uncovers non-obvious connections between entities
11. **Defensible decisions**: Multi-source validation and risk scoring provide justifiable basis for recommendations
12. **Proactive screening**: Ability to screen subsidiaries before they become subjects of specific inquiries
13. **Knowledge accumulation**: Saved searches create organizational knowledge base that grows over time
14. **Improved stakeholder communication**: Clear risk levels (SAFE, LOW, MID, HIGH, VERY HIGH) facilitate decision discussions

---

## Value Map

### Products / Features

What your solution provides.

0. **Three-Tiered Research System**: User-selectable research depth via intuitive slider interface
   - **Base Research**: Sanctions screening + AI report + media sources (30-60 sec)
   - **Network Research**: Base + corporate structure + personnel discovery (2-5 min)
   - **Deep Research**: Network + financial flows + criminal history (5-15 min)

1. **Modern React/Next.js Web Interface**: Fast, responsive single-page application with real-time updates
   - Component-based UI with dark cyber theme (navy/black with neon accents)
   - Real-time progress tracking for long searches via WebSocket
   - Instant page transitions and smooth interactions
   - Mobile-responsive design for tablet/phone access
   - Progressive Web App (PWA) for offline saved search access

2. **REST API Backend**: Decoupled API-first architecture enabling integrations
   - OpenAPI 3.0 documented endpoints (`/api/search/{tier}`, `/api/results`, `/api/history`)
   - JWT authentication and rate limiting (100 req/hr base, 500 req/hr premium)
   - Async task processing for long operations (network/deep tiers)
   - WebSocket support for real-time progress updates
   - Webhook support for automation workflows

3. **Multi-source sanctions screening**: Automated checks against USA databases (OFAC, BIS Entity List, Treasury, State Department, DOD 1260H, FCC Covered List) - 10+ sources
4. **Conglomerate search with configurable depth**: Map corporate structures 1-3 levels deep through subsidiaries, parents, and sister companies
5. **Ownership filtering**: Filter subsidiaries by ownership percentage (100%, >50%, or custom threshold)
6. **Multiple conglomerate data sources**: SEC EDGAR (10-K, 20-F), OpenCorporates API, Wikipedia, DuckDuckGo fallback
7. **Reverse search capability**: Find parent company and sister companies when starting from a subsidiary
8. **SEC EDGAR financial intelligence extraction**: Automatically extract directors, officers, major shareholders, and related party transactions from 10-K, 20-F, and DEF 14A filings
9. **Automatic sanctions cross-checking**: Flag directors and shareholders who appear on sanctions lists
10. **AI-powered OSINT research**: DuckDuckGo searches for media coverage, government announcements, and public information
11. **Source verification**: Distinguish between official government sources and general media
12. **Interactive relationship visualizations**: D3.js/Cytoscape network graphs with drag, zoom, and filter controls
13. **Geographic mapping**: Visualize entity locations by jurisdiction on interactive maps
14. **Graph path finder**: Discover connection chains between any two entities in the relationship network
15. **Fuzzy name matching**: Advanced Levenshtein distance matching with configurable thresholds to catch name variations
16. **Combined risk scoring**: 5-level risk assessment (SAFE, LOW, MID, HIGH, VERY HIGH) integrating name similarity, entity type, and address matching
17. **Save & Restore functionality**: Auto-save all searches, restore in < 2 seconds without re-running APIs (15-300x speedup)
18. **Search history management**: Filter, sort, and organize saved searches by entity name, tags, risk level, or date
19. **Notes and tags**: Annotate saved searches with custom notes and tags for organization
20. **LLM-generated intelligence reports**: AI synthesis of findings with executive summary, risk assessment, and recommendations
21. **Multi-format export**: Download as JSON (data integration), Excel multi-sheet (analysis), or PDF (formal documentation)
22. **Selective subsidiary processing**: Choose which subsidiaries to analyze at each level of conglomerate search
23. **Real-time progress tracking**: WebSocket-powered live updates with estimated time remaining and cancel option
24. **Settings panel**: Configure auto-save, fuzzy matching thresholds, and data source preferences

### Pain Relievers

How your solution reduces user pain.

1. **Eliminates decision paralysis** → Clear three-tier system helps users choose appropriate depth based on decision importance, avoiding over/under-investigation

2. **Provides research flexibility** → Users start with fast base check, can upgrade to deeper tiers if initial results warrant further investigation

3. **Eliminates scattered research workflow** → Single interface automatically integrates 10+ data sources without requiring multiple logins or manual navigation
4. **Dramatically reduces time investment** → Restore feature provides 15-300x speedup (< 2 seconds vs 30 seconds - 10 minutes), fresh searches complete in minutes vs hours
5. **Prevents missed information** → Fuzzy matching catches name variations, conglomerate search discovers hidden subsidiaries across multiple data sources
6. **Simplifies complex corporate structures** → Interactive D3.js/Cytoscape visualizations make multi-level hierarchies instantly understandable with drag-and-drop exploration
7. **Ensures systematic completeness** → Automated workflow checks all configured sanctions databases systematically, eliminating human error from checklist fatigue
8. **Saves tedious SEC EDGAR work** → AI extraction automatically pulls directors, shareholders, and transactions from filings without manual review
9. **Enables effortless research reuse** → Auto-save and one-click restore make previous searches instantly accessible without re-running expensive APIs
10. **Standardizes research quality** → All analysts follow the same comprehensive methodology regardless of experience level or time pressure
11. **Provides ready-made documentation** → Export to PDF/Excel creates audit trail and stakeholder reports without manual formatting
12. **Eliminates subsidiary tracking confusion** → Visual indicators and structured data show which subsidiaries have been screened and their results
13. **Reduces name matching uncertainty** → Match scores (0-100%) and fuzzy logic settings provide transparency in entity identification
14. **Automates cross-checking** → Directors and shareholders automatically screened against sanctions lists without manual lookup
15. **Removes interface juggling** → No need to maintain multiple browser tabs or remember different search syntaxes across databases
16. **Prevents redundant API calls** → Save/restore functionality means never re-running the same search unnecessarily

### Gain Creators

How your solution creates additional value.

1. **Cost control and efficiency** → Users pay/wait only for depth needed: base for routine checks, deep for critical decisions

2. **Modern user experience** → React interface provides instant feedback, smooth interactions, and real-time progress vs. Streamlit page refreshes

3. **API-enabled automation** → REST API allows integration with existing workflows, ticketing systems, or automated screening pipelines

4. **Strategic relationship insights** → Network graph path finder reveals non-obvious connections between entities that manual research would miss
5. **Deeper intelligence synthesis** → LLM analysis combines findings from sanctions, SEC filings, and media sources into actionable insights with geopolitical context
6. **Proactive subsidiary screening** → Conglomerate discovery enables screening entities before they become subjects of specific stakeholder inquiries
7. **Financial transparency and ownership mapping** → SEC EDGAR integration exposes ownership structures, voting rights, and related party transactions that illuminate control relationships
8. **Confidence in high-stakes decisions** → Multi-source validation, risk scoring, and comprehensive documentation provide defensible basis for recommendations to leadership
9. **Organizational knowledge accumulation** → Saved searches with notes and tags create persistent knowledge base that benefits all team members
10. **Adaptive investigation flexibility** → Configurable depth (1-3 levels), ownership thresholds (100%, >50%, custom), and fuzzy matching adapt to different use case requirements
11. **Geographic and jurisdictional awareness** → Interactive maps show entity locations and jurisdictional exposure, highlighting regulatory complexity
12. **Continuous monitoring capability** → Timestamp tracking on restored searches enables efficient re-screening to detect status changes over time
13. **Scalable research productivity** → System handles conglomerates with 100+ subsidiaries that would be impractical to research manually
14. **Media intelligence aggregation** → OSINT gathering provides context beyond compliance data (reputation, controversies, government actions)
15. **Cross-functional utility** → Exported data serves multiple departments (compliance, legal, risk, finance) without reformatting
16. **Risk communication clarity** → 5-level risk scoring (SAFE → VERY HIGH) provides common language for stakeholder discussions
17. **Source attribution and credibility** → Results show which databases/filings produced each finding, supporting evidence-based decision-making

---

# 5. Key Assumptions

List assumptions that must be true for your idea to succeed.

1. **Data Availability Assumption**: Sanctioned entities and corporate relationships are sufficiently documented in public databases (USA Sanctions API, SEC EDGAR, OpenCorporates) for the system to find them

2. **Name Consistency Assumption**: Entity names provided by stakeholders can be matched to database records with reasonable accuracy using fuzzy matching (acknowledging some manual validation may be needed)

3. **Internet Access Assumption**: Users have reliable internet connectivity to query external APIs (USA Sanctions, SEC EDGAR, OpenCorporates) and search engines (DuckDuckGo)

4. **API Reliability Assumption**: External data sources remain accessible, maintained, and stable over time (USA Sanctions API, SEC EDGAR, OpenCorporates, DuckDuckGo)

5. **User Capability Assumption**: International relations staff can interpret risk assessments, review fuzzy match scores (0-100%), and validate AI-generated reports rather than relying on system output blindly

6. **Scope Sufficiency Assumption**: USA-centric sanctions perspective is sufficient for organizational risk assessment needs (system focuses on OFAC, BIS, Treasury, etc., not EU or other jurisdictions)

7. **Timeliness Trade-off Assumption**: Users accept that restored searches show historical data with timestamps, understanding they may need to run fresh searches for time-sensitive decisions

8. **LLM Access Assumption**: Organization maintains API access to OpenAI or Anthropic for AI analysis features (intelligence report generation, synthesis)

9. **Public Source Quality Assumption**: Public data sources (Wikipedia, DuckDuckGo results, corporate websites) provide reasonably accurate information about corporate relationships and ownership structures

10. **Regulatory Stability Assumption**: USA sanctions lists and compliance requirements remain relevant to organizational decision-making needs over the system's operational lifetime

11. **Database Infrastructure Assumption**: SQLite database performance is adequate for storage requirements (50KB - 5MB per search) and query patterns (< 2 second restore times)

12. **Sanctions Centrality Assumption**: Sanctions screening is the primary risk indicator for association decisions, with other factors (reputation, financial stability) being secondary

13. **Automation Acceptability Assumption**: Stakeholders trust system-generated reports sufficiently to base decisions on them (with appropriate human review)

14. **English Language Assumption**: While the system can translate non-English entity names using LLM, most source data (sanctions lists, SEC filings) is available in English

15. **Single-User Focus Assumption**: The system is designed for individual analyst use rather than collaborative multi-user workflows with concurrent editing or approval chains

16. **Tier Sufficiency Assumption**: Users can accurately assess which research tier they need based on decision context, or are willing to upgrade if initial results are insufficient

17. **React/API Accessibility Assumption**: Users can access modern web browsers supporting latest React features (ES6+, WebSockets) and have stable internet for API calls

18. **Backend Performance Assumption**: REST API backend with async task processing can handle concurrent users without significant degradation (< 5 concurrent deep searches per server instance)

---

## Document Metadata

**Created**: 2026-03-11
**System Version**: 2.1.0
**Source Documents**:
- `templates/value_proposition_template.md`
- `key documents/rationale.md`
- `README.md`

**Related Documentation**:
- `README.md` - Complete system documentation and user guide
- `key documents/rationale.md` - Project purpose and functional overview
- `STYLE_GUIDE.md` - Development and documentation standards

---

**End of Value Proposition Document**
