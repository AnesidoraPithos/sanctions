# Requirements Document - Entity Background Check Bot

**Document Version**: 1.1
**System Version**: 2.1.0
**Date**: 2026-03-11
**Project**: Entity Background Research Agent - Intelligence Operations System
**Status**: Production Ready

---

## 1. Overview

### Problem Being Solved

International relations staff receive entity names from stakeholders who need to answer: **"Is there any risk working, collaborating, or being associated with this entity?"** and **"What is the extent of the risks involved - first-order, second-order?"**

Currently, staff must conduct time-consuming manual research across 10+ scattered sanctions databases (OFAC, BIS, Treasury, State Department, DOD, FCC), manually review SEC EDGAR filings for corporate structures, and separately query OpenCorporates and conduct Google searches. This process takes 30 minutes to several hours per entity, with significantly longer times for complex conglomerates, resulting in decision delays, compliance risk, inefficiency, and inconsistent quality.

### Target Users

**Primary Users**:
- **International Relations Staff**: Receive entity names from stakeholders and must assess risk for engagement decisions
- **Compliance Officers**: Responsible for sanctions screening and regulatory adherence
- **Risk Analysts**: Evaluate counterparty risk and association exposure

**Secondary Users**:
- Due Diligence Teams (pre-engagement assessments)
- Legal Departments (contract and partnership review)
- Financial Investigators (ownership structure tracing)
- Government Agency Analysts (policy and regulatory screening)

### Solution Summary

The **Entity Background Research Agent** is an AI-powered intelligence operations system that automates multi-source research across 10+ databases, visualizes entity relationships, and generates comprehensive risk assessments in minutes rather than hours. The system integrates all data sources into a single interface with:

- Multi-source sanctions screening (OFAC, BIS, Treasury, State, DOD, FCC)
- Conglomerate search with configurable depth (1-3 levels) and ownership filtering
- Automated SEC EDGAR extraction (directors, shareholders, transactions)
- Fuzzy name matching with configurable thresholds
- Interactive relationship visualizations (Neo4j-style network graphs)
- Save/restore functionality providing 15-300x faster results (< 2 seconds vs 30 seconds - 10 minutes)
- LLM-generated intelligence reports with export capabilities (JSON, Excel, PDF)

---

# 2. User Journeys

## Journey 1 – Basic Sanctions Screening

**Purpose**: Quickly determine if a single entity poses sanctions risk for a stakeholder engagement decision.

**Steps**:
1. Stakeholder provides entity name (e.g., "Huawei Technologies") and country (e.g., "China")
2. Staff enters entity name and country into system
3. Staff enables fuzzy logic toggle for name variations
4. Staff clicks "EXECUTE QUERY"
5. System automatically checks 10+ sanctions databases (OFAC SDN, BIS Entity List, Treasury, State Department, DOD 1260H, FCC Covered List)
6. System conducts OSINT research via DuckDuckGo (official government sources + general media)
7. System generates LLM intelligence report with executive summary, sanctions analysis, and recommendations
8. System assigns risk level (SAFE, LOW, MID, HIGH, VERY HIGH) based on combined scoring
9. System auto-saves search to database with timestamp
10. Staff reviews results across tabs: sanctions matches, media coverage, intelligence report
11. Staff exports intelligence report as PDF for stakeholder

**Outcome**: Staff provides stakeholder with comprehensive risk assessment and formal documentation in minutes instead of hours, enabling timely engagement decision with defensible basis.

---

## Journey 2 – Conglomerate Investigation

**Purpose**: Map complete corporate network of a conglomerate by querying official registries, leveraging director/officer networks, analyzing digital infrastructure, cross-referencing offshore leaks, and identifying beneficial ownership - providing a multi-dimensional view of corporate control beyond what companies officially disclose.

**Enhanced Steps**:

#### Phase 1: Official Registry Discovery (Steps 1-6 - Enhanced)
1. Stakeholder requests assessment of large corporation (e.g., "Alibaba Group Holding Limited")
2. Staff enters parent company name
3. Staff enables "CONGLOMERATE SEARCH" toggle
4. Staff configures search depth (1-3 levels) and ownership threshold (100%, >50%, or custom %)
5. Staff clicks "EXECUTE QUERY"
6. **ENHANCED**: System searches for subsidiaries using multi-source priority waterfall:
   - **SEC EDGAR** (US): 10-K, 20-F Exhibit 21.1 for official subsidiary listings
   - **OpenCorporates API**: Global corporate registry aggregator for control statements
   - **Companies House UK**: PSC (Persons with Significant Control) data if UK jurisdiction
   - **Open Ownership Register**: Beneficial ownership data via BODS standard
   - **BRIS (EU)**: Business Register Interconnection System for EU companies
   - **National Registries**: ASIC (Australia), Unternehmensregister (Germany), ACRA (Singapore) if relevant
   - **Wikipedia + DuckDuckGo**: Fallback for major corporations

#### Phase 2: Director/Officer Network Pivoting (Steps 7-10 - NEW)
7. **NEW**: System extracts all directors and officers from SEC EDGAR DEF 14A filings (already implemented) and OpenCorporates data
8. **NEW**: For each identified director/officer, system performs **Officer Pivot Search**:
   - Query OpenCorporates "Officer search" for all other companies where this individual holds board positions
   - Query Companies House UK for other companies with same director
   - Query LittleSis for interlocking directorates and influence networks
9. **NEW**: System identifies **sister companies discovered via shared management**:
   - Companies with multiple overlapping directors (likely under common control)
   - Companies with same CEO/CFO (potential unreported subsidiaries)
   - Hidden affiliates not disclosed in official filings
10. **NEW**: System displays "Management Network" tab showing:
    - Director/officer names with count of associated companies
    - Interactive graph: director nodes connected to all their companies
    - Flag potential conflicts of interest (director on boards of competitors)

#### Phase 3: Registered Address & Infrastructure Correlation (Steps 11-15 - NEW)
11. **NEW**: System extracts registered address from OpenCorporates/Companies House for parent and discovered subsidiaries
12. **NEW**: System performs **Registered Address Pivot Search**:
    - Search OpenCorporates for all other companies at exact same address
    - Flag companies at known "virtual office" or registered agent addresses (indicators of shell companies)
13. **NEW**: System performs **Digital Infrastructure Analysis**:
    - **WHOIS Lookup**: Extract domain registration details (registrant email, phone, address)
    - **Reverse WHOIS**: Find all other domains registered with same email/phone/address
    - **ASN/IP Mapping**: Identify Autonomous System Number, map all IP ranges owned by parent
    - **Reverse DNS**: Find all domains hosted on parent company's IP space
    - **Technology Stack**: Use BuiltWith API to identify shared Google Analytics tracking codes, AdSense IDs, tag managers
14. **NEW**: System identifies **sister companies discovered via infrastructure**:
    - Domains with shared WHOIS registrant details
    - Websites hosted on same IP blocks/ASN
    - Sites using same Google Analytics ID (definitive proof of common ownership)
15. **NEW**: System displays "Infrastructure Correlation" tab showing:
    - Shared domains, IPs, analytics codes
    - Visual network: companies clustered by shared infrastructure
    - Confidence scores (shared GA code = 95% confidence, same address = 60%)

#### Phase 4: Offshore & Beneficial Ownership Discovery (Steps 16-20 - NEW)
16. **NEW**: System flags any subsidiaries in **tax haven jurisdictions** (Cayman Islands, BVI, Bermuda, Panama, Luxembourg, Malta, Seychelles, etc.)
17. **NEW**: For offshore entities, system queries:
    - **OCCRP Aleph**: Cross-reference against Panama Papers, Pandora Papers, Paradise Papers, OpenLux leaks
    - **Open Ownership Register**: Query beneficial ownership data via BODS standard
    - **Companies House UK PSC**: If UK entity, extract Persons with Significant Control
    - **FinCEN BOI** (if available): US Beneficial Ownership Information for US shell companies
18. **NEW**: System performs **Beneficial Ownership Tracing**:
    - Identify UBOs (Ultimate Beneficial Owners) - the natural persons who ultimately control entities
    - Flag nominee directors (individuals listed but acting for undisclosed principals)
    - Flag bearer shares (anonymous stock certificates)
    - Calculate ownership path length (# of layers from UBO to subsidiary = opacity score)
19. **NEW**: System flags **high-risk ownership patterns**:
    - Complex multi-layer offshore structures (> 3 layers)
    - Shell companies with no clear business purpose
    - Entities using secrecy jurisdictions + nominee directors
20. **NEW**: System displays "Beneficial Ownership" tab showing:
    - UBO chains: entity → holding company → intermediate company → UBO
    - Opacity Score (0-100, higher = more opaque)
    - Red flags: offshore + nominee directors + bearer shares

#### Phase 5: Advanced OSINT Reconnaissance (Steps 21-24 - NEW)
21. **NEW**: System performs **Google Dorking** for exposed documents:
    - `site:targetcompany.com filetype:pdf "organizational chart" OR "subsidiaries" OR "corporate structure"`
    - `intitle:"index of" "parent directory" site:targetcompany.com` (exposed directories with internal docs)
    - `site:targetcompany.com "confidential" OR "internal use only" filetype:xlsx OR filetype:pdf`
22. **NEW**: System runs **SpiderFoot** (open-source OSINT tool) if configured:
    - Automated scraping of subdomains, IP addresses, employee emails
    - Cross-reference emails against data breach databases
    - Identify hosting providers, CDNs, technology stack
23. **NEW**: System queries **OCCRP Aleph** for investigative cross-references:
    - Check if parent/subsidiaries appear in offshore leak databases
    - Cross-reference against sanction lists, court records, government gazettes
24. **NEW**: System queries **LittleSis** for power mapping:
    - Political connections of directors (lobbying, campaign contributions)
    - Board interlocks with other corporations
    - Visual influence maps

#### Phase 6: Corporate Intelligence & Stakeholder Analysis (Steps 25-28 - NEW)
25. **NEW**: For public companies, system queries **WhaleWisdom**:
    - Parse SEC 13F filings to identify institutional investors
    - Track hedge funds, mutual funds, pension funds with significant equity
    - Show quarter-over-quarter position changes (buying/selling trends)
26. **NEW**: For tech/startup companies, system queries **Crunchbase**:
    - Identify venture capital investors and funding rounds
    - Extract board members appointed by VCs
    - Map acquisition history and acqui-hires
27. **NEW**: System optionally queries **B2B intelligence tools** (if API keys configured):
    - **Apollo.io** / **Hunter.io**: Extract operational org chart and employee contacts
    - **ZoomInfo**: Identify senior management not disclosed in SEC filings
28. **NEW**: System displays "Stakeholder Intelligence" tab showing:
    - Institutional investors with % ownership
    - VC investors and board seats
    - Key executives with verified contact info

#### Phase 7: Synthesis & Visualization (Steps 29-31 - Enhanced)
29. **ENHANCED**: System builds **multi-layer relationship graph** showing:
    - Parent-subsidiary relationships (existing)
    - Sister companies connected via shared parent (existing)
    - Director interlocks (NEW - directors as nodes connecting companies)
    - Infrastructure links (NEW - companies sharing IP/GA codes)
    - Beneficial ownership chains (NEW - UBO → intermediates → entities)
    - Institutional stakeholders (NEW - investors connected to public companies)
30. **ENHANCED**: System generates **comprehensive intelligence report** including:
    - **Section 1**: Official Registry Summary (SEC, OpenCorporates subsidiaries)
    - **Section 2**: Management Network Analysis (director interlocks, sister companies via officers)
    - **Section 3**: Digital Infrastructure Correlation (shared domains, IPs, analytics)
    - **Section 4**: Beneficial Ownership Analysis (UBOs, offshore structures, opacity score)
    - **Section 5**: Stakeholder Intelligence (institutional investors, VCs, political connections)
    - **Section 6**: OSINT Discoveries (Google Dorks, leak database matches, exposed docs)
    - **Section 7**: Risk Assessment (sanctions exposure across full network, hidden affiliations)
31. **ENHANCED**: Staff exports **multi-sheet Excel workbook** with new sheets:
    - Summary Dashboard (existing)
    - Sanctions Matches (existing)
    - Subsidiaries (existing)
    - **NEW**: Sister Companies (via management + infrastructure)
    - **NEW**: Directors & Officers Network (all companies per director)
    - **NEW**: Beneficial Ownership Chains (UBO → entity paths)
    - **NEW**: Digital Infrastructure (domains, IPs, WHOIS, analytics)
    - **NEW**: Institutional Stakeholders (13F investors, VCs)
    - **NEW**: OSINT Discoveries (Dork results, leak matches)
    - Financial Intelligence (existing)

**Outcome**: Staff provides stakeholder with **comprehensive corporate network map** that goes far beyond official disclosures, uncovering hidden sister companies through director networks, exposing offshore beneficial owners, identifying sister companies via digital infrastructure, and mapping institutional stakeholders - enabling detection of corporate relationships that companies deliberately obscure.

---

## Journey 3 – Reverse Search (Parent & Sister Company Discovery)

**Purpose**: Starting from a subsidiary, discover its parent company and identify sister companies using official registries, director networks, infrastructure correlation, and offshore leak databases - providing comprehensive ownership context beyond what the subsidiary officially discloses.

**Enhanced Steps**:

#### Phase 1: Official Registry Reverse Lookup (Steps 1-7 - Enhanced)
1. Stakeholder provides subsidiary name (e.g., "Lazada Southeast Asia")
2. Staff enters subsidiary name
3. Staff **disables** "CONGLOMERATE SEARCH" toggle
4. Staff **enables** "SEARCH FOR PARENT & SISTERS" toggle
5. Staff clicks "EXECUTE QUERY"
6. **ENHANCED**: System searches multiple sources to identify parent company:
   - **OpenCorporates API**: Control statements showing controller entities
   - **Companies House UK PSC**: Persons/entities with significant control
   - **SEC EDGAR**: Check if subsidiary mentioned in any 10-K Exhibit 21.1 (implies that company is parent)
   - **Open Ownership Register**: Trace beneficial ownership upward
   - **OCCRP Aleph**: Check if subsidiary appears in leak databases with parent references
7. System displays parent company information with **confidence score** (95% if from official registry, 70% if from leaks)

#### Phase 2: Sister Company Discovery via Management (Steps 8-11 - NEW)
8. **NEW**: System extracts directors/officers of the subsidiary from:
   - OpenCorporates officer data
   - Companies House if UK company
   - SEC EDGAR if US subsidiary with filings
9. **NEW**: For each director/officer, system performs **Officer Pivot**:
   - Query OpenCorporates for all other companies where this person holds positions
   - Query LittleSis for interlocking directorates
10. **NEW**: System identifies **sister companies via shared directors**:
    - Companies with ≥2 overlapping directors with subsidiary (likely sisters under same parent)
    - Companies with same CEO/CFO as subsidiary (high confidence of common control)
11. **NEW**: System displays "Management-Based Sisters" section showing:
    - Sister companies discovered through shared management
    - Director network graph: directors connecting subsidiary to sisters
    - Confidence scores based on # of shared directors

#### Phase 3: Sister Company Discovery via Infrastructure (Steps 12-16 - NEW)
12. **NEW**: System extracts subsidiary's digital footprint:
    - WHOIS lookup for subsidiary's domain
    - IP address and ASN lookup
    - Technology stack analysis (BuiltWith API)
13. **NEW**: System performs **Reverse WHOIS** search:
    - Find all domains registered with same email, phone, or address
    - Identify other companies using those domains (likely sisters)
14. **NEW**: System performs **IP/ASN correlation**:
    - Find all domains hosted on same IP range
    - Reverse DNS lookup to discover sister company domains
15. **NEW**: System performs **Technology Stack correlation**:
    - Find all websites using same Google Analytics tracking code
    - Find all sites with same AdSense publisher ID
    - Find all sites with same GTM (Google Tag Manager) container
16. **NEW**: System displays "Infrastructure-Based Sisters" section showing:
    - Sister companies discovered via shared infrastructure
    - Infrastructure correlation graph: domains/IPs connecting companies
    - Confidence scores (shared GA = 95%, shared IP = 60%, shared registrant = 80%)

#### Phase 4: Beneficial Ownership Tracing (Steps 17-20 - NEW)
17. **NEW**: If parent company is in offshore jurisdiction, system queries:
    - **OCCRP Aleph**: Check Panama Papers, Pandora Papers for UBO revelations
    - **Open Ownership Register**: Trace beneficial ownership chains
    - **Companies House UK**: If UK parent, extract PSC data
18. **NEW**: System traces **ownership path** from subsidiary to UBO:
    - Subsidiary → Immediate Parent → Intermediate Holdings → Ultimate Parent → UBO
    - Calculate path length (# of corporate layers)
    - Flag each layer's jurisdiction (highlight tax havens)
19. **NEW**: System flags **opacity indicators**:
    - Nominee directors or secretaries at any layer
    - Bearer shares
    - Jurisdictions with weak disclosure laws (Cayman, BVI, Panama)
20. **NEW**: System displays "Beneficial Ownership Chain" visualization:
    - Hierarchical tree: subsidiary at bottom, UBO at top
    - Each layer shows jurisdiction, incorporation date, ownership %
    - Red flags for opaque layers

#### Phase 5: Sister Company Discovery via Parent (Steps 21-24 - Enhanced)
21. **ENHANCED**: Once parent identified, system automatically discovers sister companies:
    - **OpenCorporates API**: Query all entities controlled by parent
    - **SEC EDGAR**: If parent is US-listed, extract all subsidiaries from 10-K Exhibit 21.1
    - **Companies House UK**: If parent is UK, find all companies with same PSC
22. **ENHANCED**: System cross-references discovered sisters against:
    - Sisters found via director networks (validate consistency)
    - Sisters found via infrastructure (validate consistency)
    - Flag discrepancies (companies appearing in one source but not others = potential hidden affiliates)
23. Staff reviews **consolidated sister company list** with source attribution:
    - Sisters from official registries (high confidence)
    - Sisters from director networks (medium-high confidence)
    - Sisters from infrastructure (medium confidence)
    - Sisters from OSINT/leaks (lower confidence, requires validation)
24. Staff selectively adds relevant sister companies to analysis

#### Phase 6: Advanced OSINT & Intelligence (Steps 25-28 - NEW)
25. **NEW**: System performs **Google Dorking** on parent company:
    - Search for exposed org charts mentioning subsidiary and sisters
    - `site:parentcompany.com "subsidiaries" OR "affiliated companies" filetype:pdf`
26. **NEW**: If parent is publicly traded, system queries **WhaleWisdom**:
    - Identify institutional investors in parent (indirect stakeholders in subsidiary)
    - Show major funds with voting power over parent
27. **NEW**: System queries **LittleSis** for parent's political connections:
    - Lobbying expenditures by parent (reveals strategic interests)
    - Campaign contributions from parent's executives
    - Board interlocks between parent and other corporations
28. **NEW**: System displays "Stakeholder Context" section:
    - Who controls the parent (institutional investors, VCs, UBOs)
    - Political connections and influence networks
    - Strategic partnerships revealed through board interlocks

#### Phase 7: Synthesis & Export (Steps 29-31 - Enhanced)
29. **ENHANCED**: System builds **multi-dimensional relationship graph**:
    - Subsidiary → Parent → Sisters (core structure)
    - Directors connecting subsidiary to sisters (management layer)
    - Infrastructure links between subsidiary and sisters (digital layer)
    - UBO → Parent → Subsidiary (ownership layer)
    - Institutional investors → Parent (stakeholder layer)
30. **ENHANCED**: System generates **intelligence report** including:
    - **Section 1**: Parent Company Identification (sources, confidence score)
    - **Section 2**: Sister Companies Summary (count, jurisdictions, discovery methods)
    - **Section 3**: Management Network Analysis (shared directors, interlocks)
    - **Section 4**: Infrastructure Correlation Analysis (shared domains, IPs, analytics)
    - **Section 5**: Beneficial Ownership Context (UBO chains, opacity scores)
    - **Section 6**: Stakeholder Intelligence (institutional investors, political connections)
    - **Section 7**: Sanctions Exposure Assessment (subsidiary + parent + all sisters)
31. **ENHANCED**: Staff exports findings with new data:
    - Parent company details
    - Consolidated sister company list (with discovery method attribution)
    - Director network details
    - Infrastructure correlation data
    - Beneficial ownership chains
    - Stakeholder intelligence

**Outcome**: Staff provides stakeholder with **complete ownership context** of subsidiary, identifying not just the official parent, but hidden sister companies through director networks and digital infrastructure, exposing ultimate beneficial owners through offshore leak databases, and mapping institutional stakeholders - revealing the full corporate family and control structure that subsidiary filings alone would never disclose.

---

## Journey 4 – Comprehensive Financial Flow Mapping and Intelligence Extraction

**Purpose**: Map complete financial ecosystem of an entity by extracting SEC regulatory data, tracing operational capital outflows through trade data, identifying B2B vendor networks through procurement records, analyzing marketing expenditures, and uncovering hidden offshore structures - providing a 360-degree view of where money flows.

**Steps**:

### Phase 1: SEC EDGAR Financial Intelligence (Steps 1-8)
1. During conglomerate search, system identifies entities with SEC filings
2. System automatically retrieves relevant SEC documents:
   - **10-K**: Annual reports for US companies
   - **20-F**: Annual reports for foreign issuers
   - **DEF 14A**: Proxy statements with detailed governance
3. System extracts structured data:
   - **Directors & Officers**: Names, titles, nationalities, biographies
   - **Major Shareholders**: Names, ownership percentages, voting rights, jurisdictions
   - **Related Party Transactions**: Counterparty names, transaction amounts, relationship types
4. System automatically cross-checks all extracted personnel against 10+ sanctions databases
5. System flags any directors, officers, or shareholders with sanctions matches
6. Staff reviews extracted data in dedicated tabs:
   - "👔 DIRECTORS & OFFICERS" tab with sanctions status column
   - "💼 MAJOR SHAREHOLDERS" tab with ownership % and jurisdiction
   - "🔄 RELATED PARTY TRANSACTIONS" tab with amounts and relationships
7. System includes financial intelligence in relationship graph (personnel nodes connected to entities)
8. Staff exports financial intelligence as part of comprehensive Excel workbook

### Phase 2: Global Trade Data Analysis (Steps 9-15)
9. System checks if entity engages in physical product imports/exports
10. System queries trade intelligence platforms:
    - **ImportYeti** (US sea shipments) - Free tier for initial screening
    - **ImportGenius** (100+ countries) - if API access available
    - **Panjiva/TradeInt** (enterprise tier) - if configured
11. System extracts Bills of Lading (BOL) data:
    - Supplier/shipper names (who entity is paying)
    - Consignee information
    - Product descriptions (HS codes)
    - Shipment volumes and frequencies
    - Estimated transaction values
12. System calculates estimated capital outflows to foreign suppliers
13. System flags potential Trade-Based Money Laundering (TBML) indicators:
    - Over-invoicing (price > market rate)
    - Under-invoicing (price < market rate)
    - Mismatched HS codes and product descriptions
14. System adds supplier entities to relationship graph with "SUPPLIER" edge type
15. System runs sanctions screening on all discovered suppliers

### Phase 3: Government Procurement & B2B Networks (Steps 16-22)
16. System queries **USAspending.gov API** for federal contracts where entity is prime contractor
17. System extracts sub-award data showing subcontractors (entity's B2B vendors)
18. System queries **OpenTender.eu/TED** for EU public procurement if entity operates in Europe
19. System calculates:
    - Total government revenue (inbound)
    - Subcontractor payments (outbound to vendors)
    - Net federal spending flow
20. System identifies entity's trusted B2B vendor network
21. System runs sanctions screening on all subcontractors
22. System adds procurement relationships to graph

### Phase 4: Marketing & Technology Infrastructure Spend (Steps 23-27)
23. System queries **Pathmatics** (if API access) for digital advertising spend:
    - Estimated monthly ad spend by platform (Facebook, YouTube, Instagram, Display)
    - Ad creatives and campaigns
    - Historical spending trends
24. System identifies major marketing capital outflows to tech platforms
25. System analyzes technology stack (DNS records, Shodan scans) to identify:
    - Cloud providers (AWS, Azure, GCP) - recurring infrastructure costs
    - SaaS platforms (Salesforce, HubSpot) - recurring subscription costs
    - MarTech vendors - marketing technology spending
26. System estimates total technology infrastructure spend
27. System flags if entity uses offshore hosting or privacy-centric infrastructure (potential red flag)

### Phase 5: Corporate Philanthropy & Tax-Exempt Transfers (Steps 28-31)
28. System queries **IRS 990 forms** (if entity is US nonprofit or major donor)
29. System extracts charitable contributions and grant recipients
30. System identifies flow of capital to tax-exempt organizations
31. System checks if charitable recipients have sanctions exposure

### Phase 6: Litigation & Real Estate Financial Flows (Steps 32-35)
32. System queries **PACER** (US federal courts) for litigation where entity is party
33. System extracts:
    - Opposing parties (potential financial disputes)
    - Settlement amounts (capital outflows for legal resolutions)
    - Judgment creditors/debtors
34. System queries real estate registries for property ownership
35. System identifies capital deployed in real estate assets

### Phase 7: Offshore Tax Haven Analysis (Steps 36-39)
36. System checks if entity has subsidiaries in tax haven jurisdictions (Cayman Islands, British Virgin Islands, Bermuda, etc.)
37. System queries **OpenCorporates** for beneficial ownership in offshore jurisdictions
38. System flags offshore entities with opaque ownership structures
39. System estimates capital flows to tax havens (potential money laundering indicator)

### Phase 8: Financial Flow Summary & Risk Assessment (Steps 40-43)
40. System generates comprehensive financial flow summary:
    - Total identified outbound capital flows by category (suppliers, B2B, marketing, offshore)
    - Top 10 recipient entities by estimated dollar volume
    - Geographic distribution of financial flows
    - Sanctions exposure across full financial network
41. System calculates **Financial Flow Risk Score**:
    - High-risk jurisdictions receiving funds (20%)
    - Sanctioned suppliers/vendors (30%)
    - Offshore tax haven exposure (20%)
    - TBML indicators (15%)
    - Opaque beneficial ownership (15%)
42. System includes financial flow analysis in LLM intelligence report
43. Staff exports comprehensive financial ecosystem as Excel workbook with sheets:
    - Trade Data (suppliers)
    - Procurement (subcontractors)
    - Marketing Spend
    - Offshore Entities
    - Financial Flow Summary

**Outcome**: Staff provides stakeholder with **complete financial ecosystem map** showing not just who owns/controls the entity (existing Journey 4), but where money actually flows - enabling detection of hidden sanctions exposure, money laundering indicators, and financial relationships not disclosed in regulatory filings. This comprehensive view supports higher-confidence risk assessments for critical engagement decisions.

---

## Journey 5 – Search Retrieval and Monitoring (Save/Restore)

**Purpose**: Efficiently retrieve previous research to avoid redundant work, monitor entities over time, and provide institutional knowledge base.

**Steps**:

### Initial Search (Day 1)
1. Staff conducts comprehensive conglomerate search on entity (e.g., "Xiaomi Corporation")
2. Search takes 5 minutes and queries multiple APIs
3. System auto-saves search to database (< 5 seconds)
4. Staff adds notes: "Requested by business development for partnership evaluation"
5. Staff adds tags: "technology", "pending-decision", "high-priority"

### Search Retrieval (Day 7)
6. Stakeholder asks for status update on same entity
7. Staff opens "📜 SAVED SEARCH HISTORY" expander
8. Staff filters by entity name "Xiaomi" or tag "high-priority"
9. Staff finds saved search from Day 1 with timestamp "2026-03-04"
10. Staff clicks "📂 Restore" button
11. System loads complete results in < 2 seconds (no API calls made)
12. Banner displays: "📂 Displaying Restored Search - No API calls were made"
13. Staff reviews all tabs: sanctions, subsidiaries, financial intelligence, diagrams
14. Staff notes timestamp to stakeholder: "Data as of 2026-03-04"

### Monitoring (Day 30)
15. Staff needs to check if entity status has changed
16. Staff restores previous search (< 2 seconds)
17. Staff reviews timestamp and determines fresh search is needed
18. Staff runs fresh search to get updated data
19. System auto-saves new search with current timestamp
20. Staff compares current risk assessment with Day 1 findings
21. Staff notes in search history: "Re-screened on Day 30, status unchanged"

### Knowledge Sharing (Day 60)
22. New team member asks about previously researched entity
23. Staff searches history by entity name or tag
24. Staff restores relevant searches and shows new member complete analysis
25. Staff exports as Excel for offline review

**Outcome**: Staff achieves 15-300x speedup on repeated queries (< 2 seconds vs 30 seconds - 10 minutes), eliminates redundant API calls and research effort, maintains institutional knowledge accessible to all team members, enables efficient periodic monitoring, and provides audit trail for compliance review.

---

## Journey 6 – Individual Criminal Background Check

**Purpose**: Screen individuals associated with entities (directors, officers, Ultimate Beneficial Owners) for criminal records, sanctions, and role-specific violations to assess personnel-related risks that could impact entity engagement decisions.

**Steps**:

### Automatic Individual Discovery (Steps 1-3)
1. Staff conducts entity search (Journey 1 or 2) for target company (e.g., "Acme Corporation")
2. System automatically extracts individuals from entity data:
   - Directors and officers from SEC EDGAR DEF 14A filings
   - Ultimate Beneficial Owners (UBOs) from OpenCorporates/Open Ownership Register
   - Key executives from corporate registry data
   - Shareholders with significant holdings from 13F filings
3. System displays extracted individuals in "Personnel" tab with names, roles, and jurisdictions

### Country Detection and Selection (Steps 4-6)
4. System automatically determines which countries to screen for each individual:
   - Extract individual's country from SEC filing addresses (DEF 14A)
   - Infer countries from entity's jurisdiction (e.g., UK company → check UK records)
   - Include countries where entity has subsidiaries (presence = potential activity)
5. System displays country selection interface with checkboxes for each individual
6. Staff can manually add/remove countries (e.g., add US if director has prior US employment)

### Criminal Records Screening (Steps 7-9)
7. System queries national and local criminal records databases per selected countries:
   - **US**: FBI NCIC (via authorized channels if available), state criminal records APIs
   - **UK**: Police National Computer (PNC) equivalent public records
   - **EU**: European Criminal Records Information System (ECRIS) where accessible via member states
   - **Singapore**: Singapore Police Force public records (where accessible)
   - **China**: Public criminal records databases (limited availability)
   - **International**: Interpol Red Notices (public dataset)
8. System flags individuals with criminal convictions, arrests, or outstanding warrants
9. System displays severity classification: felonies (high risk), misdemeanors (medium risk), pending charges

### Sex Offender Registry Screening (Steps 10-11)
10. System checks individuals against national sex offender registries:
    - **US**: National Sex Offender Public Website (NSOPW) integration
    - **UK**: ViSOR (Violent and Sex Offender Register) public access equivalents
    - **Other jurisdictions**: Equivalent registries where available
11. System prominently flags any sex offender registry matches as VERY HIGH RISK

### Role-Specific Screening (Steps 12-15)
12. System infers individual's professional role from job title (CFO, General Counsel, VP Finance, etc.)
13. For **financial roles** (CFO, treasurer, controllers), system queries:
    - FinCEN Enforcement Actions database (money laundering violations)
    - SEC Enforcement Actions and officer/director bars
    - FINRA BrokerCheck for broker-dealer disciplinary history
    - CFTC enforcement actions for commodity trading violations
14. For **other professional roles**, system queries:
    - **Medical roles**: OIG Exclusions Database (healthcare fraud, barred from Medicare/Medicaid)
    - **Legal roles**: State bar disciplinary records and disbarment notices
    - **Accounting roles**: AICPA and state board sanctions
    - **Engineering roles**: Professional engineering board disciplinary actions
15. System queries **government debarment lists**:
    - SAM.gov (System for Award Management) exclusions database
    - UN procurement debarment list
    - World Bank debarment list
    - Cross-reference with USAspending.gov for past contract violations

### Integrated Risk Reporting (Steps 16-18)
16. System generates "Personnel Risk Assessment" section in main intelligence report:
    - List all screened individuals with risk scores (SAFE, LOW, MID, HIGH, VERY HIGH)
    - Display criminal records with jurisdiction, offense type, conviction date, sentence
    - Display sanctions matches, role-specific violations, debarment status
    - Highlight high-risk individuals prominently with red flags
    - Include source citations for all findings (database name, record ID, query date)
17. Staff reviews personnel risks alongside entity-level risks (sanctions, financial flows)
18. Staff exports comprehensive report including personnel section for stakeholder

### Standalone Individual Search (Optional Workflow)
19. **Alternative Entry Point**: Staff selects "Individual Search" mode in UI (not entity search)
20. Staff enters individual details:
    - Full name (required)
    - Date of birth (optional, improves match accuracy)
    - Nationality (optional)
    - Countries of residence (checkboxes: US, UK, EU, Singapore, China, Other)
21. Staff clicks "EXECUTE INDIVIDUAL SEARCH"
22. System performs all background checks (criminal records, sex offender registries, role-specific, debarment)
23. System generates individual-focused risk report with all findings
24. Staff exports individual report as PDF

**Outcome**: Staff provides stakeholder with **comprehensive personnel risk assessment** integrated into entity intelligence report, enabling detection of criminal backgrounds, regulatory violations, and professional sanctions that could pose reputational, compliance, or operational risks. This multi-country screening covers directors, officers, and UBOs automatically discovered during entity searches, while supporting standalone individual lookups when needed.

---

# 3. User Stories

User stories organized by functional category, with implementation status marked as:
- ✅ **Implemented** in v2.1.0
- 📋 **Planned** for future releases
- ❌ **Out of Scope** (Won't Have)

---

## Category 1: Core Sanctions Screening

### US-1.1: Multi-Source Sanctions Database Screening

**Type**: Functional
**Priority**: Must Have
**Status**: ✅ Implemented in v2.1.0

**User Story**

As an international relations staff member
I want to check an entity against all USA sanctions databases in a single query
So that I can ensure comprehensive compliance screening without manually checking 10+ separate databases.

**Acceptance Criteria**

- System queries OFAC SDN List, BIS Entity List, Treasury Sanctions, State Department Nonproliferation, Commerce Unverified List, DOD Section 1260H, and FCC Covered List
- System returns all matches with source attribution (which database found the match)
- System completes screening of all databases within 30 seconds for single entity
- System handles API failures gracefully with fallback to local databases
- System displays match confidence scores (0-100%) for each result

**Verification**

- Integration test: Query known sanctioned entity (e.g., "Huawei") and verify matches returned from multiple databases
- Integration test: Verify all 10+ configured data sources are queried
- Performance test: Measure query time < 30 seconds for single entity
- Unit test: Verify fallback behavior when API unavailable
- UI test: Verify match results display source database and confidence score

---

### US-1.2: Fuzzy Name Matching for Entity Variations

**Type**: Functional
**Priority**: Must Have
**Status**: ✅ Implemented in v2.1.0

**User Story**

As a compliance officer
I want the system to find entity matches even when names have spelling variations, transliterations, or abbreviations
So that I don't miss sanctioned entities due to name differences.

**Acceptance Criteria**

- System uses Levenshtein distance algorithm for fuzzy matching
- System provides configurable similarity threshold (default 80%)
- System flags matches with scores between 70-100% for review
- System handles common variations: abbreviations (Corp vs Corporation), transliterations (Huawei vs 华为), legal suffixes (Ltd, LLC, Inc)
- System displays match score as percentage for transparency
- Users can adjust fuzzy matching threshold in settings (0-100%)

**Verification**

- Unit test: Verify Levenshtein distance calculation accuracy with test cases
- Integration test: Query "Huawei Tech" and verify it matches "Huawei Technologies Co Ltd" with score > 80%
- Integration test: Test transliteration matching with Chinese, Russian, Arabic entity names
- UI test: Verify match score displayed to user
- UI test: Verify settings panel allows threshold adjustment

---

### US-1.3: Combined Risk Scoring System

**Type**: Functional
**Priority**: Must Have
**Status**: ✅ Implemented in v2.1.0

**User Story**

As a risk analyst
I want a clear risk level assessment (SAFE, LOW, MID, HIGH, VERY HIGH) for each entity
So that I can quickly communicate risk to stakeholders without requiring them to interpret raw data.

**Acceptance Criteria**

- System calculates risk score based on: name match score (0-100%), entity type match (boolean), address match (boolean)
- System assigns 5-level risk classification:
  - SAFE: No matches found
  - LOW: Weak matches (< 75% similarity)
  - MID: Moderate matches (75-85% similarity) or type match only
  - HIGH: Strong matches (85-95% similarity) with type match
  - VERY HIGH: Exact/near-exact match (> 95%) with multiple attribute matches
- System displays risk level prominently with color coding
- System includes risk level in intelligence report and exports

**Verification**

- Unit test: Verify risk scoring algorithm with test cases covering all 5 levels
- Integration test: Verify known sanctioned entity (100% match) scores VERY HIGH
- Integration test: Verify non-sanctioned entity scores SAFE
- UI test: Verify risk level displayed with appropriate color (green=SAFE, red=VERY HIGH)
- Manual verification: Review sample intelligence reports for risk level accuracy

---

### US-1.4: OSINT Media Intelligence Gathering

**Type**: Functional
**Priority**: Must Have
**Status**: ✅ Implemented in v2.1.0

**User Story**

As an international relations staff member
I want the system to gather media coverage and public information about entities
So that I can understand reputation, controversies, and context beyond sanctions data.

**Acceptance Criteria**

- System conducts DuckDuckGo searches for entity name + keywords (sanctions, government, investigation)
- System distinguishes between official sources (government press releases, sanctions announcements) and general media (news, blogs)
- System returns top 10-20 relevant results with titles, URLs, and snippets
- System includes media intelligence in LLM report synthesis
- System displays media results in dedicated "📰 MEDIA COVERAGE" tab
- Results include source type indicator (Official/General)

**Verification**

- Integration test: Query known sanctioned entity and verify media results returned
- Integration test: Verify official sources (gov, treasury.gov domains) flagged separately from general media
- UI test: Verify media results displayed with source type indicator
- Manual verification: Review media results relevance for sample entities
- Integration test: Verify media intelligence included in LLM report generation

---

### US-1.5: Source Verification and Attribution

**Type**: Functional
**Priority**: Must Have
**Status**: ✅ Implemented in v2.1.0

**User Story**

As a legal department reviewer
I want to see which specific databases and sources produced each finding
So that I can assess credibility and provide evidence-based documentation.

**Acceptance Criteria**

- Each sanctions match displays source database name (OFAC, BIS, Treasury, etc.)
- Media results show source URL and domain
- Financial intelligence shows SEC filing type (10-K, 20-F, DEF 14A) and accession number
- Conglomerate data shows source (SEC EDGAR, OpenCorporates, Wikipedia, DuckDuckGo)
- Intelligence report includes references section with all sources

**Verification**

- UI test: Verify sanctions matches display source database
- UI test: Verify media results include URL and source type
- UI test: Verify financial intelligence includes filing type
- Manual verification: Review sample intelligence report for source citations
- Integration test: Verify all data elements have source attribution

---

### US-1.6: Non-English Entity Name Translation

**Type**: Functional
**Priority**: Should Have
**Status**: 📋 Planned

**User Story**

As an international relations staff member
I want to search for entities using their native language names (Chinese, Russian, Arabic)
So that I can find matches that may be listed differently in English databases.

**Acceptance Criteria**

- System accepts entity names in non-English characters
- System uses LLM to translate entity name to English
- System searches using both original name and translated name
- System displays translation used in search parameters
- System handles transliteration variations (e.g., multiple ways to romanize Chinese names)

**Verification**

- Integration test: Search Chinese entity name "华为" and verify English results for "Huawei" returned
- Integration test: Test Russian entity name transliteration
- Integration test: Test Arabic entity name transliteration
- UI test: Verify translation displayed to user
- Manual verification: Review translation accuracy for sample entities across languages

---

### US-1.7: EU and UN Sanctions Database Integration

**Type**: Functional
**Priority**: Should Have
**Status**: 📋 Planned

**User Story**

As a compliance officer
I want to check entities against EU sanctions and UN sanctions lists in addition to USA databases
So that I can assess international sanctions exposure beyond USA perspective.

**Acceptance Criteria**

- System integrates EU Consolidated Sanctions List API
- System integrates UN Security Council Sanctions List API
- System provides toggle to enable/disable EU and UN screening
- System displays jurisdiction in match results (USA/EU/UN)
- System includes EU/UN sanctions in risk scoring

**Verification**

- Integration test: Query entity on EU sanctions list and verify match returned
- Integration test: Query entity on UN sanctions list and verify match returned
- UI test: Verify toggle controls for EU/UN screening in settings
- UI test: Verify jurisdiction displayed in match results
- Unit test: Verify risk scoring algorithm incorporates EU/UN matches

---

### US-1.8: Machine Learning Enhanced Name Matching

**Type**: Functional
**Priority**: Could Have
**Status**: 📋 Planned

**User Story**

As a risk analyst
I want the system to learn from my match validation decisions (true positive/false positive)
So that future searches have improved accuracy and fewer manual reviews.

**Acceptance Criteria**

- System provides "Confirm Match" and "Reject Match" buttons for each fuzzy match result
- System stores user feedback in database
- System trains ML model on validated matches to improve scoring
- System displays "ML-Enhanced" indicator for matches scored using trained model
- System allows export of training data for model evaluation

**Verification**

- UI test: Verify feedback buttons present on match results
- Unit test: Verify feedback stored correctly in database
- Integration test: Train model on sample data and verify improved accuracy
- Performance test: Verify ML scoring adds < 2 seconds to query time
- Manual verification: Evaluate model accuracy on held-out test set (target > 90% precision)

---

## Category 2: Conglomerate and Corporate Structure Analysis

### US-2.1: Multi-Level Conglomerate Search

**Type**: Functional
**Priority**: Must Have
**Status**: ✅ Implemented in v2.1.0

**User Story**

As a due diligence analyst
I want to discover all subsidiaries of a parent company up to 3 levels deep
So that I can assess sanctions exposure across the entire corporate structure.

**Acceptance Criteria**

- System provides configurable search depth selector (1, 2, or 3 levels)
- System searches multiple data sources in priority order: SEC EDGAR → OpenCorporates → Wikipedia → DuckDuckGo
- System displays subsidiaries in expandable tree structure with level indicators (L1, L2, L3)
- System shows ownership percentage for each subsidiary where available
- System allows selective processing: user chooses which subsidiaries to analyze at each level
- System handles conglomerates with 100+ subsidiaries without performance degradation
- System displays progress indicator during long searches

**Verification**

- Integration test: Search known conglomerate (e.g., "Alibaba Group") and verify subsidiaries found across 3 levels
- Performance test: Verify 100+ subsidiary conglomerate completes within 10 minutes
- UI test: Verify tree structure with expand/collapse functionality
- UI test: Verify ownership percentages displayed
- UI test: Verify selective processing checkboxes functional
- UI test: Verify progress indicator shows during search

---

### US-2.2: Ownership Percentage Filtering

**Type**: Functional
**Priority**: Must Have
**Status**: ✅ Implemented in v2.1.0

**User Story**

As a compliance officer
I want to filter subsidiaries by ownership threshold (100%, >50%, or custom percentage)
So that I can focus analysis on entities with significant ownership stakes.

**Acceptance Criteria**

- System provides ownership filter options: "100% owned", ">50% owned", "Custom threshold"
- Custom threshold allows user to enter any percentage (0-100%)
- System applies filter during conglomerate search (only returns subsidiaries meeting threshold)
- System displays ownership percentage for each subsidiary
- System shows "Ownership Unknown" for subsidiaries where percentage unavailable
- System allows changing filter and re-running search

**Verification**

- Integration test: Search conglomerate with ownership filter "100%" and verify only wholly-owned subsidiaries returned
- Integration test: Test custom threshold (e.g., 25%) and verify filtering accuracy
- UI test: Verify ownership filter dropdown and custom input field
- UI test: Verify ownership percentage displayed for each subsidiary
- Unit test: Verify filtering logic with test cases for edge cases (exactly 50%, 100%, 0%)

---

### US-2.3: Multiple Conglomerate Data Sources

**Type**: Functional
**Priority**: Must Have
**Status**: ✅ Implemented in v2.1.0

**User Story**

As a financial investigator
I want the system to search SEC EDGAR, OpenCorporates, Wikipedia, and web search for subsidiaries
So that I get comprehensive corporate structure data from authoritative and public sources.

**Acceptance Criteria**

- System queries data sources in priority order:
  1. SEC EDGAR (10-K, 20-F filings) - highest reliability
  2. OpenCorporates API (if API key provided) - global coverage
  3. Wikipedia - major corporations
  4. DuckDuckGo - fallback
- System continues to next source if previous source returns no results
- System aggregates subsidiaries from all sources (de-duplicates by name similarity)
- System shows source indicator for each subsidiary (SEC/OpenCorp/Wikipedia/Web)
- System preferences allow disabling specific sources

**Verification**

- Integration test: Search US-listed company and verify SEC EDGAR used first
- Integration test: Search non-US company without SEC filings and verify OpenCorporates/Wikipedia used
- Integration test: Verify de-duplication when same subsidiary found in multiple sources
- UI test: Verify source indicator displayed for each subsidiary
- UI test: Verify settings allow enabling/disabling data sources

---

### US-2.4: Reverse Search - Parent Company Discovery

**Type**: Functional
**Priority**: Must Have
**Status**: ✅ Implemented in v2.1.0

**User Story**

As a risk analyst
I want to search for a subsidiary and find its parent company
So that I can understand ownership structure when starting from a lower-level entity.

**Acceptance Criteria**

- System provides "SEARCH FOR PARENT & SISTERS" toggle (mutually exclusive with conglomerate search)
- System queries multiple sources to identify parent company of given entity
- System displays parent company information (name, country, ownership relationship)
- System automatically discovers sister companies (other subsidiaries of same parent)
- System allows user to add parent and sisters to analysis with checkboxes
- System runs sanctions screening on selected parent and sisters

**Verification**

- Integration test: Search known subsidiary (e.g., "Lazada") and verify parent company ("Alibaba") discovered
- Integration test: Verify sister companies listed
- UI test: Verify "SEARCH FOR PARENT & SISTERS" toggle functional
- UI test: Verify parent company information displayed
- UI test: Verify checkboxes allow adding parent/sisters to analysis
- Integration test: Verify sanctions screening runs on selected entities

---

### US-2.5: Selective Subsidiary Processing

**Type**: Functional
**Priority**: Must Have
**Status**: ✅ Implemented in v2.1.0

**User Story**

As an international relations staff member
I want to choose which subsidiaries to analyze at each level of conglomerate search
So that I can control scope and time investment based on risk assessment needs.

**Acceptance Criteria**

- System displays all discovered subsidiaries with checkboxes
- System allows user to select/deselect subsidiaries before processing
- System provides "Select All" and "Deselect All" buttons
- System shows estimated processing time based on number selected
- System only runs sanctions screening and financial extraction for selected subsidiaries
- System displays processing progress with count (e.g., "Processing 5 of 20 subsidiaries")

**Verification**

- UI test: Verify checkboxes functional for subsidiary selection
- UI test: Verify "Select All" and "Deselect All" buttons
- Integration test: Select subset of subsidiaries and verify only selected ones processed
- UI test: Verify progress indicator shows count
- Manual verification: Confirm unselected subsidiaries not in final results

---

### US-2.6: Sister Company Discovery

**Type**: Functional
**Priority**: Must Have
**Status**: ✅ Implemented in v2.1.0

**User Story**

As a due diligence analyst
I want to see all sister companies (entities owned by the same parent) when searching a subsidiary
So that I can assess risk exposure across the full corporate family.

**Acceptance Criteria**

- During reverse search, system identifies parent company
- System queries parent company's subsidiaries to find sister companies
- System displays sister companies in list with ownership percentages
- System excludes the original search entity from sister list
- System allows selective addition of sisters to analysis
- System includes sister company relationships in relationship graph

**Verification**

- Integration test: Search subsidiary and verify sister companies discovered
- Integration test: Verify original search entity not in sister list
- UI test: Verify sister companies displayed with ownership info
- UI test: Verify checkboxes for adding sisters to analysis
- UI test: Verify sister relationships shown in graph visualization

---

### US-2.7: Batch Entity Processing

**Type**: Functional
**Priority**: Should Have
**Status**: 📋 Planned

**User Story**

As a compliance officer
I want to submit multiple entity names in a single session for batch screening
So that I can efficiently process a list of entities from a stakeholder request.

**Acceptance Criteria**

- System provides text area for entering multiple entity names (one per line)
- System accepts CSV file upload with columns: entity name, country, search type
- System processes entities sequentially with progress indicator
- System generates summary report showing all entities with risk levels
- System allows exporting batch results as single Excel file with one entity per sheet
- System saves batch session for later retrieval

**Verification**

- UI test: Verify multi-line text input and CSV upload functional
- Integration test: Submit 10 entity batch and verify all processed
- Performance test: Verify batch of 50 entities completes within 30 minutes
- UI test: Verify progress indicator during batch processing
- UI test: Verify summary report with all entities
- Manual verification: Review Excel export format for batch results

---

### US-2.8: Side-by-Side Search Comparison

**Type**: Functional
**Priority**: Should Have
**Status**: 📋 Planned

**User Story**

As a risk analyst
I want to compare two saved searches side-by-side (e.g., same entity at different times, or two related entities)
So that I can identify changes in sanctions status or compare risk profiles.

**Acceptance Criteria**

- System provides "Compare" button in search history
- User selects two saved searches to compare
- System displays comparison view with side-by-side columns
- System highlights differences: new sanctions matches, changed risk levels, new subsidiaries
- System shows delta indicators (added, removed, unchanged)
- System allows exporting comparison report as PDF

**Verification**

- UI test: Verify "Compare" button in search history
- UI test: Verify side-by-side comparison view displays
- Integration test: Compare two searches of same entity and verify differences highlighted
- UI test: Verify delta indicators displayed
- Manual verification: Review comparison accuracy for sample searches
- UI test: Verify PDF export of comparison

---

## Category 3: Financial Intelligence and SEC Analysis

### US-3.1: SEC EDGAR Director and Officer Extraction

**Type**: Functional
**Priority**: Must Have
**Status**: ✅ Implemented in v2.1.0

**User Story**

As a financial investigator
I want to automatically extract directors and officers from SEC filings
So that I can identify key personnel without manually reading 10-K, 20-F, and proxy statements.

**Acceptance Criteria**

- System retrieves SEC filings (10-K, 20-F, DEF 14A) for entities with SEC registration
- System extracts: full names, titles/positions, nationalities (if available), biographies
- System displays extracted data in "👔 DIRECTORS & OFFICERS" tab with table format
- System includes accession number and filing type for traceability
- System handles multiple directors/officers per entity (supports 20+ personnel)
- System stores extracted data in database for saved searches

**Verification**

- Integration test: Query US-listed company (e.g., "Tesla") and verify directors extracted from SEC filings
- Integration test: Verify 10-K, 20-F, and DEF 14A filings all processed
- UI test: Verify directors displayed in table with all fields (name, title, nationality)
- UI test: Verify filing type and accession number shown for traceability
- Integration test: Verify data persists in saved search restore

---

### US-3.2: Major Shareholder Extraction

**Type**: Functional
**Priority**: Must Have
**Status**: ✅ Implemented in v2.1.0

**User Story**

As a compliance officer
I want to identify major shareholders and their ownership percentages from SEC filings
So that I can understand ownership structure and control relationships.

**Acceptance Criteria**

- System extracts major shareholders (typically > 5% ownership) from SEC filings
- System captures: shareholder name, ownership percentage, voting rights, jurisdiction
- System displays in "💼 MAJOR SHAREHOLDERS" tab with sortable table
- System handles both individual and institutional shareholders
- System includes shareholder type indicator (Individual/Institution/Government)
- System shows data source (filing type and accession number)

**Verification**

- Integration test: Query US-listed company and verify major shareholders extracted
- UI test: Verify shareholders displayed with ownership % and jurisdiction
- UI test: Verify table sortable by ownership percentage
- Integration test: Verify both individual and institutional shareholders captured
- Manual verification: Spot-check shareholder data accuracy against actual SEC filings

---

### US-3.3: Automatic Personnel Sanctions Cross-Check

**Type**: Functional
**Priority**: Must Have
**Status**: ✅ Implemented in v2.1.0

**User Story**

As a due diligence analyst
I want the system to automatically check all extracted directors and shareholders against sanctions lists
So that I can identify if key personnel are sanctioned without manual lookups.

**Acceptance Criteria**

- System automatically queries sanctions databases for every extracted director and shareholder
- System uses fuzzy matching for personnel names
- System flags matches in dedicated "Sanctions Status" column (CLEAR/FLAGGED)
- System includes match details: database source, match score, entity type
- System highlights sanctioned personnel in red for visibility
- System includes personnel sanctions in overall entity risk assessment

**Verification**

- Integration test: Test entity with known sanctioned director and verify flagged
- Integration test: Verify all extracted personnel checked against sanctions lists
- UI test: Verify "Sanctions Status" column in directors/shareholders tables
- UI test: Verify flagged personnel highlighted in red
- Unit test: Verify flagged personnel contribute to risk score calculation

---

### US-3.4: Related Party Transaction Extraction

**Type**: Functional
**Priority**: Must Have
**Status**: ✅ Implemented in v2.1.0

**User Story**

As a financial investigator
I want to see related party transactions from SEC filings (loans, guarantees, purchases)
So that I can trace financial relationships and potential conflicts of interest.

**Acceptance Criteria**

- System extracts related party transactions from SEC filings (typically from notes to financial statements)
- System captures: counterparty name, transaction amount, transaction type (loan/guarantee/purchase), relationship description
- System displays in "🔄 RELATED PARTY TRANSACTIONS" tab with table format
- System converts amounts to USD for consistency
- System sorts transactions by amount (largest first)
- System includes counterparty in relationship graph as node

**Verification**

- Integration test: Query entity with known related party transactions and verify extraction
- UI test: Verify transactions displayed with all fields (counterparty, amount, type, relationship)
- UI test: Verify transactions sortable by amount
- Integration test: Verify amounts converted to USD
- UI test: Verify counterparties appear in relationship graph

---

### US-3.5: Enhanced Transaction Analysis

**Type**: Functional
**Priority**: Should Have
**Status**: 📋 Planned

**User Story**

As a financial investigator
I want the system to analyze patterns in related party transactions (frequency, amounts, counterparty concentration)
So that I can identify unusual financial flows or potential risks.

**Acceptance Criteria**

- System calculates transaction summary statistics: total volume, average amount, frequency
- System identifies top counterparties by transaction volume
- System flags unusual patterns: single counterparty > 50% of volume, large one-time transactions
- System provides time series visualization of transaction volumes
- System includes transaction analysis in intelligence report

**Verification**

- Unit test: Verify summary statistics calculated correctly
- Integration test: Test entity with concentrated counterparty and verify flag
- UI test: Verify transaction analysis section displayed
- Manual verification: Review transaction analysis for sample entities
- Manual verification: Confirm analysis included in intelligence report

---

### Sub-Category 3A: Global Trade Intelligence

### US-3.6: Import/Export Trade Data Extraction (ImportYeti Integration)

**Type**: Functional
**Priority**: Should Have
**Status**: 📋 Planned

**User Story**

As a financial investigator
I want to extract Bills of Lading from ImportYeti (US sea shipments) to identify foreign suppliers
So that I can trace operational capital outflows to entities the company is paying for goods.

**Acceptance Criteria**

- System queries ImportYeti API for entity's import/export shipments (US customs data)
- System extracts: supplier/shipper names, consignee information, product descriptions, HS codes, shipment dates, estimated values
- System calculates estimated annual capital outflows to each supplier
- System displays trade data in "🚢 TRADE DATA" tab with sortable table
- System runs sanctions screening on all identified suppliers
- System stores trade data in database for saved searches

**Verification**

- Integration test: Query entity with known import activity (e.g., retail company) and verify BOL data extracted
- UI test: Verify trade data displayed with all fields (supplier, HS code, value, date)
- Unit test: Verify capital outflow calculations (sum of shipment values per supplier)
- Integration test: Verify suppliers screened against sanctions lists
- UI test: Verify sanctions status column for suppliers

---

### US-3.7: Trade-Based Money Laundering (TBML) Detection

**Type**: Functional
**Priority**: Should Have
**Status**: 📋 Planned

**User Story**

As a compliance officer
I want the system to detect trade-based money laundering indicators (over-invoicing, under-invoicing, HS code mismatches)
So that I can flag suspicious trade patterns for further investigation.

**Acceptance Criteria**

- System analyzes pricing anomalies by comparing shipment values to market rates for commodities
- System flags over-invoicing (declared price > 150% market rate) and under-invoicing (declared price < 50% market rate)
- System detects HS code mismatches (product description inconsistent with HS code classification)
- System flags high-risk jurisdictions known for TBML activity
- System includes TBML indicators in Financial Flow Risk Score calculation
- System displays TBML flags in trade data tab with warning icons

**Verification**

- Unit test: Test TBML detection algorithm with synthetic trade data (known over/under-invoiced shipments)
- Integration test: Test with entity having pricing anomalies and verify flags displayed
- UI test: Verify TBML indicators highlighted in red with warning icons
- Unit test: Verify TBML indicators contribute to risk score (15% weight)
- Manual verification: Review TBML detection accuracy for sample entities

---

### US-3.8: Multi-Country Trade Intelligence (ImportGenius/Panjiva)

**Type**: Functional
**Priority**: Could Have
**Status**: 📋 Planned

**User Story**

As a financial investigator
I want to access global trade data beyond US customs (Latin America, Asia, Europe)
So that I can map complete international supply chains for entities operating globally.

**Acceptance Criteria**

- System integrates ImportGenius API (100+ countries) for global trade data
- System integrates Panjiva/TradeInt API (enterprise tier) if configured
- System provides historical trend analysis (shipment volume changes over time)
- System supports country-specific queries (e.g., China imports, Vietnam exports)
- System enables competitive intelligence (compare entity's trade patterns to industry benchmarks)
- System consolidates multi-country data in unified trade data tab

**Verification**

- Integration test: Query global entity with operations in multiple countries and verify trade data from all regions
- UI test: Verify historical trend charts displayed (shipment volumes over time)
- Integration test: Test ImportGenius API integration with sample query
- Manual verification: Verify trade data accuracy for sample entities in non-US countries
- UI test: Verify country filter functionality in trade data tab

---

### US-3.9: Supplier Network Relationship Mapping

**Type**: Functional
**Priority**: Should Have
**Status**: 📋 Planned

**User Story**

As a risk analyst
I want to visualize supplier relationships in the network graph with trade values as edge weights
So that I can quickly identify the entity's most critical financial dependencies.

**Acceptance Criteria**

- System adds supplier entities to relationship graph with "SUPPLIES" edge type
- System displays trade value as edge weight (thicker lines = higher dollar volume)
- System enables supplier path tracing (entity → supplier → supplier's suppliers for nested dependencies)
- System highlights sanctioned suppliers in red on graph
- System supports filtering graph to show only trade relationships
- System displays supplier node details on hover (total trade value, sanctions status, jurisdiction)

**Verification**

- UI test: Verify suppliers appear as nodes on relationship graph
- UI test: Verify edge thickness correlates with trade value
- Integration test: Test graph with entity having 20+ suppliers and verify performance
- UI test: Verify sanctioned suppliers highlighted in red
- Manual verification: Verify graph layout is readable with large supplier networks

---

### Sub-Category 3B: Government Procurement & B2B Intelligence

### US-3.10: Federal Procurement Data Extraction (USAspending.gov)

**Type**: Functional
**Priority**: Should Have
**Status**: 📋 Planned

**User Story**

As a compliance officer
I want to extract federal contract data from USAspending.gov showing prime contracts and sub-awards
So that I can identify the entity's B2B vendor network and government revenue sources.

**Acceptance Criteria**

- System queries USAspending.gov API for federal contracts where entity is prime contractor
- System extracts: contract award amount, contracting agency, period of performance, place of performance
- System extracts sub-award data showing all subcontractors with payment amounts
- System calculates federal revenue (inbound) and subcontractor payments (outbound)
- System displays in "🏛️ GOVERNMENT CONTRACTS" tab with expandable sub-award sections
- System stores procurement data in database for saved searches

**Verification**

- Integration test: Query known government contractor (e.g., defense company) and verify contracts extracted
- UI test: Verify contracts displayed with all fields (amount, agency, subcontractors)
- Integration test: Verify sub-award data extracted and linked to prime contracts
- Unit test: Verify revenue and payment calculations accurate
- UI test: Verify expandable sub-award sections functional

---

### US-3.11: Subcontractor Sanctions Screening

**Type**: Functional
**Priority**: Should Have
**Status**: 📋 Planned

**User Story**

As a compliance officer
I want the system to automatically screen all discovered subcontractors against sanctions lists
So that I can detect if the entity is paying sanctioned B2B vendors (critical compliance violation).

**Acceptance Criteria**

- System automatically screens all subcontractors extracted from USAspending.gov against sanctions databases
- System flags sanctioned subcontractors with critical warning indicator
- System calculates percentage of subcontracting spend going to high-risk jurisdictions
- System includes subcontractor sanctions in overall entity risk score
- System displays subcontractor sanctions status in government contracts tab
- System alerts staff if any subcontractor is sanctioned

**Verification**

- Integration test: Test with entity having known sanctioned subcontractor and verify flagged
- UI test: Verify sanctions status column displayed for all subcontractors
- Unit test: Verify risk score includes subcontractor sanctions (factored into Financial Flow Risk Score)
- Integration test: Verify high-risk jurisdiction percentage calculated correctly
- UI test: Verify critical warning displayed for sanctioned subcontractors

---

### US-3.12: European Union Public Procurement (OpenTender/TED)

**Type**: Functional
**Priority**: Could Have
**Status**: 📋 Planned

**User Story**

As a financial investigator
I want to access EU public procurement data from OpenTender.eu and TED (Tenders Electronic Daily)
So that I can map B2B relationships for entities operating in European markets.

**Acceptance Criteria**

- System queries OpenTender.eu for EU public tenders involving entity
- System queries TED (Tenders Electronic Daily) for EU procurement notices
- System extracts consortia members and joint venture partners from tender data
- System identifies B2B relationships through EU procurement patterns
- System displays EU tender history with award amounts and contracting authorities
- System consolidates US and EU procurement data in unified government contracts tab

**Verification**

- Integration test: Query EU-based entity and verify tender data extracted from OpenTender/TED
- UI test: Verify EU tenders displayed with contracting authority and award amounts
- Integration test: Test API integration with sample EU procurement query
- Manual verification: Verify consortia members accurately extracted
- UI test: Verify US/EU data displayed in unified format

---

### US-3.13: Procurement Network Visualization

**Type**: Functional
**Priority**: Should Have
**Status**: 📋 Planned

**User Story**

As a risk analyst
I want to visualize government contracts and subcontractor relationships in the network graph
So that I can understand the entity's position in federal supply chains.

**Acceptance Criteria**

- System adds government agency nodes connected to entity (prime contractor relationship)
- System adds subcontractor nodes connected from entity with "SUBCONTRACTOR" edge type
- System displays contract values as edge labels
- System colors government nodes distinctly (e.g., blue) to differentiate from private entities
- System enables filtering graph to show only procurement relationships
- System supports drill-down on subcontractor nodes to show their downstream vendors

**Verification**

- UI test: Verify government agency nodes appear on relationship graph
- UI test: Verify subcontractor nodes connected from entity
- UI test: Verify contract values displayed as edge labels
- Integration test: Test graph with entity having 10+ subcontractors and verify performance
- Manual verification: Verify graph colors distinguish government vs. private entities

---

### Sub-Category 3C: Marketing & Technology Infrastructure Analysis

### US-3.14: Digital Advertising Spend Tracking (Pathmatics Integration)

**Type**: Functional
**Priority**: Could Have
**Status**: 📋 Planned

**User Story**

As a financial investigator
I want to track the entity's digital advertising spend across platforms (Facebook, YouTube, Instagram)
So that I can identify major marketing capital outflows to tech platforms.

**Acceptance Criteria**

- System queries Pathmatics API for entity's digital ad spend (requires paid access)
- System extracts estimated monthly spend by platform: Facebook, YouTube, Instagram, Display, Snapchat, TikTok
- System shows ad creatives and campaign themes
- System calculates annual marketing capital outflow to tech platforms
- System displays in "📱 MARKETING INTELLIGENCE" tab with spend breakdown charts
- System stores ad spend data in database for historical comparison

**Verification**

- Integration test: Query known advertiser (e.g., consumer brand) and verify ad spend extracted
- UI test: Verify spend breakdown displayed by platform with bar charts
- Unit test: Verify annual marketing spend calculation (sum of monthly estimates)
- UI test: Verify ad creatives displayed with thumbnails
- Manual verification: Verify ad spend estimates reasonable compared to public disclosures

---

### US-3.15: Technology Stack Financial Analysis

**Type**: Functional
**Priority**: Could Have
**Status**: 📋 Planned

**User Story**

As a risk analyst
I want to analyze the entity's technology infrastructure to estimate recurring technology costs
So that I can understand capital deployed in cloud, SaaS, and MarTech vendors.

**Acceptance Criteria**

- System analyzes DNS records, Shodan scans, SecurityTrails data to identify technology stack
- System identifies cloud providers (AWS, Azure, GCP) and estimates hosting costs based on infrastructure size
- System identifies SaaS platforms (Salesforce, HubSpot, Stripe) and estimates subscription costs
- System identifies MarTech vendors from advertising analysis
- System calculates estimated annual technology infrastructure spend
- System flags use of offshore/privacy-centric hosting (potential red flag for obfuscation)

**Verification**

- Integration test: Query entity with known technology stack and verify identified correctly
- Unit test: Verify cost estimation algorithm (cloud costs based on infrastructure indicators)
- UI test: Verify technology stack displayed in marketing intelligence tab
- Integration test: Test Shodan API integration for infrastructure scanning
- Manual verification: Verify offshore hosting flags for entities using privacy-focused providers

---

### US-3.16: Marketing Vendor Sanctions Screening

**Type**: Functional
**Priority**: Could Have
**Status**: 📋 Planned

**User Story**

As a compliance officer
I want to screen advertising agencies and technology vendors identified from infrastructure analysis
So that I can detect if the entity is using sanctioned tech providers or platforms.

**Acceptance Criteria**

- System screens advertising agencies identified from ad creatives against sanctions lists
- System screens technology vendors identified from DNS/infrastructure analysis
- System flags if entity using sanctioned tech providers or platforms
- System includes marketing vendor sanctions in relationship graph
- System displays sanctions status for all identified vendors in marketing intelligence tab
- System includes vendor sanctions in Financial Flow Risk Score

**Verification**

- Integration test: Test with entity using known sanctioned technology vendor and verify flagged
- UI test: Verify sanctions status displayed for all marketing/tech vendors
- Integration test: Verify vendors added to relationship graph with sanctions indicators
- Unit test: Verify vendor sanctions contribute to risk score
- Manual verification: Review vendor sanctions accuracy for sample entities

---

### Sub-Category 3D: Offshore & Tax Haven Analysis

### US-3.17: Tax Haven Subsidiary Detection

**Type**: Functional
**Priority**: Should Have
**Status**: 📋 Planned

**User Story**

As a financial investigator
I want to automatically detect subsidiaries in tax haven jurisdictions (Cayman, BVI, Bermuda, etc.)
So that I can identify potential offshore capital flows and money laundering risk.

**Acceptance Criteria**

- During conglomerate search, system flags subsidiaries in known tax havens (Cayman Islands, British Virgin Islands, Bermuda, Luxembourg, Panama, Seychelles, Malta, etc.)
- System queries OpenCorporates for beneficial ownership disclosure in offshore jurisdictions
- System flags entities with opaque ownership structures (no disclosed beneficial owners)
- System estimates capital flows to offshore jurisdictions based on subsidiary financial data
- System calculates "Offshore Opacity Score" (0-100, higher = more opaque)
- System displays offshore entities in dedicated section with opacity indicators

**Verification**

- Integration test: Query entity with known offshore subsidiaries and verify flagged
- Unit test: Verify tax haven jurisdiction list comprehensive (20+ jurisdictions)
- Integration test: Test OpenCorporates API for beneficial ownership queries
- Unit test: Verify Offshore Opacity Score calculation algorithm
- UI test: Verify offshore entities highlighted with warning indicators

---

### US-3.18: Beneficial Ownership Tracing

**Type**: Functional
**Priority**: Should Have
**Status**: 📋 Planned

**User Story**

As a compliance officer
I want to trace ultimate beneficial owners (UBOs) through offshore entity structures
So that I can identify if sanctioned individuals control entities through shell companies.

**Acceptance Criteria**

- System attempts to trace ultimate beneficial owners (UBOs) for offshore entities
- System queries beneficial ownership registries (UK PSC Register, EU registries) where available
- System flags shell companies with nominee directors or bearer shares
- System highlights if UBOs are sanctioned individuals
- System displays UBO chains in relationship graph (entity → holding company → UBO)
- System calculates ownership path length as opacity indicator (longer chains = higher risk)

**Verification**

- Integration test: Query entity with multi-layered offshore structure and verify UBO tracing
- Integration test: Test UK PSC Register API integration for beneficial ownership
- UI test: Verify UBO chains displayed in relationship graph
- Integration test: Verify sanctioned UBOs flagged with critical warning
- Manual verification: Verify UBO tracing accuracy for sample offshore entities

---

### US-3.19: Money Laundering Risk Indicators

**Type**: Functional
**Priority**: Should Have
**Status**: 📋 Planned

**User Story**

As a compliance officer
I want the system to detect money laundering risk patterns (offshore structures + high-risk trade + opaque ownership)
So that I can prioritize entities for enhanced due diligence.

**Acceptance Criteria**

- System combines offshore analysis + TBML indicators + procurement patterns to detect ML risk
- System flags high-risk patterns:
  - Complex offshore structures + trade with high-risk jurisdictions
  - Offshore entities + no clear business purpose
  - Rapid capital movement through multiple jurisdictions
- System calculates **Money Laundering Risk Score** (0-100, weighted composite)
- System displays ML risk indicators in dedicated risk assessment section
- System includes ML risk assessment in intelligence report with detailed explanation

**Verification**

- Unit test: Verify ML Risk Score calculation (composite of offshore opacity, TBML, jurisdiction risk)
- Integration test: Test with entity having known ML red flags and verify high score
- UI test: Verify ML risk indicators displayed with explanations
- Manual verification: Review ML risk assessments for sample entities for false positives
- Integration test: Verify ML risk assessment included in LLM intelligence report

---

### Sub-Category 3E: Comprehensive Financial Flow Reporting

### US-3.20: Financial Flow Summary Dashboard

**Type**: Functional
**Priority**: Should Have
**Status**: 📋 Planned

**User Story**

As a financial investigator
I want a comprehensive financial flow dashboard summarizing capital outflows by category
So that I can quickly understand where the entity's money is going and sanctions exposure.

**Acceptance Criteria**

- System generates financial flow dashboard in "💰 FINANCIAL FLOWS" tab
- Dashboard displays:
  - Total outbound capital flows by category (suppliers $X, subcontractors $Y, marketing $Z, offshore $W)
  - Top 10 recipient entities by dollar volume with bar chart
  - Geographic heatmap of capital flows (which countries receiving money)
  - Sanctions exposure across financial network (% of flows to high-risk entities)
- Dashboard includes interactive charts (Plotly or similar) with drill-down capability
- Dashboard shows data freshness timestamp

**Verification**

- UI test: Verify financial flow dashboard displays all sections (categories, top recipients, heatmap, sanctions exposure)
- Unit test: Verify capital flow aggregation calculations accurate
- Integration test: Test with entity having diverse financial flows and verify dashboard completeness
- UI test: Verify interactive charts functional (hover, click, zoom)
- Manual verification: Verify geographic heatmap accuracy for sample entities

---

### US-3.21: Enhanced Intelligence Report with Financial Flows

**Type**: Functional
**Priority**: Should Have
**Status**: 📋 Planned

**User Story**

As an international relations staff member
I want the LLM intelligence report to include a comprehensive financial flow analysis section
So that I can provide stakeholders with actionable insights on where money is flowing and associated risks.

**Acceptance Criteria**

- LLM intelligence report includes new section: **"Financial Flow Analysis"**
- Section synthesizes trade data, procurement, marketing, offshore findings into narrative
- Report highlights critical insights: "Entity is paying $X annually to suppliers in sanctioned jurisdictions"
- Report provides financial flow-based risk assessment with specific examples
- Report includes visualizations: Sankey diagram of capital flows (entity → categories → recipients)
- Report exportable as PDF with all financial flow data and charts

**Verification**

- Integration test: Generate report for entity with financial flow data and verify section included
- Manual verification: Review report quality for narrative clarity and actionable insights
- UI test: Verify Sankey diagram displays correctly in report
- Integration test: Test PDF export with financial flow visualizations
- Manual verification: Verify report provides stakeholder-ready insights (non-technical language)

---

## Category 4: Visualization and Relationship Mapping

### US-4.1: Interactive Network Graph Visualization

**Type**: UI
**Priority**: Must Have
**Status**: ✅ Implemented in v2.1.0

**User Story**

As a risk analyst
I want to visualize entity relationships in an interactive network graph (Neo4j-style)
So that I can understand complex corporate structures and connections at a glance.

**Acceptance Criteria**

- System builds network graph with nodes (entities, directors, shareholders) and edges (relationships)
- Graph supports drag-and-drop, zoom, and pan interactions
- Node types distinguished by color: parent (blue), subsidiary (green), director (orange), shareholder (purple)
- Edge types show relationship: ownership %, director role, shareholder stake, transaction
- Graph provides filter controls: show/hide directors, shareholders, transactions
- Graph uses physics simulation for automatic layout
- Graph displays entity names on nodes with hover tooltips for details

**Verification**

- UI test: Verify graph renders for conglomerate search results
- UI test: Verify drag-and-drop, zoom, pan interactions functional
- UI test: Verify node colors match entity types
- UI test: Verify edge labels show relationship information
- UI test: Verify filter toggles show/hide node categories
- Manual verification: Review graph layout for complex conglomerate (20+ nodes)

---

### US-4.2: Geographic Entity Mapping

**Type**: UI
**Priority**: Must Have
**Status**: ✅ Implemented in v2.1.0

**User Story**

As an international relations staff member
I want to see entity locations on an interactive map
So that I can understand geographic distribution and jurisdictional exposure.

**Acceptance Criteria**

- System geocodes entity jurisdictions to latitude/longitude coordinates
- System displays entities on interactive world map (using Folium/Plotly)
- Map markers color-coded by risk level (green=SAFE, red=VERY HIGH)
- Clicking marker shows entity details: name, country, risk level, sanctions matches
- Map supports zoom and pan
- Map legend explains color coding

**Verification**

- UI test: Verify map renders with entity markers
- Integration test: Verify geocoding accuracy for sample countries
- UI test: Verify marker colors match risk levels
- UI test: Verify clicking marker shows entity details popup
- UI test: Verify map zoom and pan functional
- Manual verification: Review map for conglomerate with global subsidiary presence

---

### US-4.3: Graph Path Finder

**Type**: Functional
**Priority**: Must Have
**Status**: ✅ Implemented in v2.1.0

**User Story**

As a due diligence analyst
I want to find connection paths between any two entities in the relationship graph
So that I can trace how entities are related through intermediaries.

**Acceptance Criteria**

- System provides "Graph Explorer" tool with entity search
- User selects two entities from dropdown (source and target)
- System calculates shortest path(s) between entities using graph algorithms
- System displays path as node sequence with relationship descriptions
- System highlights path nodes in graph visualization
- System handles cases where no path exists (disconnected graph)

**Verification**

- UI test: Verify Graph Explorer tool accessible
- Integration test: Query path between parent and 3rd-level subsidiary and verify path found
- Integration test: Verify path description includes relationship types (owns, director of, shareholder of)
- UI test: Verify path nodes highlighted in graph
- Integration test: Test disconnected entities and verify "No path found" message
- Unit test: Verify path finding algorithm correctness with test graph

---

### US-4.4: Risk Heatmap Visualization

**Type**: UI
**Priority**: Should Have
**Status**: 📋 Planned

**User Story**

As a risk analyst
I want to see a heatmap of entity risk levels by geography
So that I can quickly identify high-risk jurisdictions and concentration.

**Acceptance Criteria**

- System generates choropleth map with countries color-coded by risk level
- Color intensity represents risk: light green (SAFE) to dark red (VERY HIGH)
- Clicking country shows list of entities in that jurisdiction with risk details
- Map legend shows risk level color scale
- Map supports export as PNG image

**Verification**

- UI test: Verify heatmap renders for conglomerate with multi-country presence
- UI test: Verify color intensity matches risk levels
- UI test: Verify clicking country displays entity list
- UI test: Verify legend displayed
- UI test: Verify PNG export functional

---

### US-4.5: Timeline Visualization for Transaction History

**Type**: UI
**Priority**: Could Have
**Status**: 📋 Planned

**User Story**

As a financial investigator
I want to see related party transactions plotted on a timeline
So that I can identify patterns and temporal relationships in financial flows.

**Acceptance Criteria**

- System creates timeline visualization with transaction dates on x-axis
- Transaction amounts shown as bubble size
- Counterparties distinguished by color
- Hovering bubble shows transaction details
- Timeline supports zoom to date ranges
- Timeline includes major corporate events (acquisitions, sanctions designations) as markers

**Verification**

- UI test: Verify timeline renders for entity with transactions
- UI test: Verify bubble size proportional to amount
- UI test: Verify hover tooltip displays transaction details
- UI test: Verify timeline zoom functional
- Manual verification: Review timeline clarity for entity with 20+ transactions

---

## Category 5: Save/Restore and Data Management

### US-5.1: Auto-Save All Searches

**Type**: Functional
**Priority**: Must Have
**Status**: ✅ Implemented in v2.1.0

**User Story**

As an international relations staff member
I want every search automatically saved to the database
So that I never lose research work and can retrieve it later without manual save actions.

**Acceptance Criteria**

- System provides "Auto-save all searches" toggle in Settings (enabled by default)
- When enabled, system automatically saves every completed search to database
- Save includes: all sanctions matches, media hits, intelligence report, conglomerate data, financial intelligence, diagrams, search parameters
- Save completes in < 5 seconds even for complex conglomerate searches (100+ subsidiaries)
- System assigns unique ID to each saved search
- System stores timestamp of search execution
- System shows confirmation message "Search automatically saved" after completion

**Verification**

- UI test: Verify auto-save toggle in Settings panel
- Integration test: Run search with auto-save enabled and verify entry appears in search history
- Performance test: Verify save time < 5 seconds for search with 100 subsidiaries
- Integration test: Verify all data types saved (sanctions, media, conglomerate, financial, diagrams)
- UI test: Verify confirmation message displayed
- Unit test: Verify unique ID generation for saved searches

---

### US-5.2: One-Click Search Restore

**Type**: Functional
**Priority**: Must Have
**Status**: ✅ Implemented in v2.1.0

**User Story**

As a compliance officer
I want to restore a previous search with one click in under 2 seconds
So that I can retrieve research without re-running expensive API calls.

**Acceptance Criteria**

- System provides "📂 Restore" button for each saved search in history
- Clicking restore loads complete search results in < 2 seconds
- Restore makes zero external API calls (all data from database)
- System displays banner: "📂 Displaying Restored Search - No API calls were made"
- Restored search shows all tabs: sanctions, media, conglomerate, financial, diagrams, intelligence report
- System shows original search timestamp prominently
- Restored search is read-only (cannot modify, but can export)

**Verification**

- Performance test: Measure restore time < 2 seconds for search with 50 subsidiaries
- Integration test: Verify no API calls made during restore (mock external APIs)
- UI test: Verify banner displayed indicating restored search
- UI test: Verify all tabs populated with restored data
- UI test: Verify timestamp displayed
- Manual verification: Compare restored results to original search for accuracy

---

### US-5.3: Search History with Filtering and Sorting

**Type**: UI
**Priority**: Must Have
**Status**: ✅ Implemented in v2.1.0

**User Story**

As an international relations staff member
I want to filter and sort saved searches by entity name, tags, risk level, or date
So that I can quickly find relevant previous research.

**Acceptance Criteria**

- System displays saved searches in "📜 SAVED SEARCH HISTORY" expander
- System provides filter inputs:
  - Entity name (text search)
  - Tags (dropdown or text search)
  - Risk level (dropdown: All/SAFE/LOW/MID/HIGH/VERY HIGH)
  - Date range (start date, end date)
- System provides sort options: Date (newest first), Date (oldest first), Entity name (A-Z), Risk level (highest first)
- Filters and sorts apply in real-time (no submit button needed)
- System shows count: "Showing X of Y saved searches"
- System paginates results if > 20 searches

**Verification**

- UI test: Verify filter inputs functional for entity name, tags, risk level, date range
- UI test: Verify sort dropdown changes order
- Integration test: Test filtering with database containing 50+ saved searches
- UI test: Verify "Showing X of Y" count updates with filters
- UI test: Verify pagination if > 20 results
- Manual verification: Confirm filters produce expected results

---

### US-5.4: Notes and Tags for Search Organization

**Type**: Functional
**Priority**: Must Have
**Status**: ✅ Implemented in v2.1.0

**User Story**

As a due diligence analyst
I want to add custom notes and tags to saved searches
So that I can organize research by project, stakeholder, or purpose.

**Acceptance Criteria**

- System provides "Notes" text area for each saved search (up to 500 characters)
- System provides "Tags" input field accepting comma-separated tags
- Notes and tags editable after save using "✏️ Edit" button
- Tags used in search history filtering (can filter by tag)
- Common tags suggested: stakeholder names, project codes, risk classifications
- System displays tags as chips/badges in search history list
- System shows note preview (first 50 characters) in search history, with "Read more" to expand

**Verification**

- UI test: Verify notes and tags input fields on save dialog
- UI test: Verify "✏️ Edit" button allows updating notes/tags
- Integration test: Verify notes and tags persisted to database
- UI test: Verify tags used in filtering
- UI test: Verify tags displayed as chips in history
- UI test: Verify note preview with expand functionality

---

### US-5.5: Multi-Format Export from Search History

**Type**: Functional
**Priority**: Must Have
**Status**: ✅ Implemented in v2.1.0

**User Story**

As a legal department reviewer
I want to export saved searches as JSON, Excel, or PDF directly from search history
So that I can share findings without restoring the full search.

**Acceptance Criteria**

- Each saved search in history has "📤 Export" button with format dropdown
- JSON export: Complete search data structure (for data integration)
- Excel export: Multi-sheet workbook with tabs for Summary, Sanctions, Subsidiaries, Directors, Shareholders, Transactions, Intelligence Report
- PDF export: Intelligence report formatted for formal documentation
- Export filename includes entity name and date (e.g., "Huawei_2026-03-11_report.pdf")
- Export downloads immediately without page refresh
- System logs export action for audit trail

**Verification**

- UI test: Verify "📤 Export" button with format dropdown for each saved search
- Integration test: Export as JSON and verify complete data structure
- Integration test: Export as Excel and verify all sheets present with correct data
- Integration test: Export as PDF and verify formatting and content
- UI test: Verify filename format
- Manual verification: Open exported files in respective applications (Excel, PDF reader)
- Integration test: Verify export action logged in database

---

### US-5.6: Search Deletion with Confirmation

**Type**: Functional
**Priority**: Must Have
**Status**: ✅ Implemented in v2.1.0

**User Story**

As an international relations staff member
I want to delete saved searches I no longer need
So that I can keep my search history organized and manage database size.

**Acceptance Criteria**

- Each saved search has "🗑️ Delete" button
- Clicking delete shows confirmation dialog: "Are you sure you want to delete this search? This action cannot be undone."
- Confirmation dialog has "Cancel" and "Delete" buttons
- Deleting removes search from database permanently
- System shows success message: "Search deleted successfully"
- Deleted search immediately removed from search history list
- System logs deletion action with timestamp and user ID (if applicable)

**Verification**

- UI test: Verify "🗑️ Delete" button present for each saved search
- UI test: Verify confirmation dialog appears with correct message
- Integration test: Verify search deleted from database after confirmation
- Integration test: Verify canceled deletion does not remove search
- UI test: Verify success message displayed
- UI test: Verify search removed from history list
- Integration test: Verify deletion logged

---

### US-5.7: Periodic Re-Screening for Monitoring

**Type**: Functional
**Priority**: Should Have
**Status**: 📋 Planned

**User Story**

As a compliance officer
I want to schedule periodic re-screening of saved entities (weekly, monthly)
So that I can monitor for changes in sanctions status over time.

**Acceptance Criteria**

- System provides "Monitor" button for each saved search
- User selects re-screening frequency: Weekly, Bi-weekly, Monthly
- System automatically re-runs search at specified intervals
- System compares new results to previous results and flags differences
- System sends notification (email or in-app) if sanctions status changes
- System displays monitoring status in search history: "Last checked: 2026-03-10, Next check: 2026-04-10"
- User can pause or cancel monitoring for an entity

**Verification**

- UI test: Verify "Monitor" button and frequency selection
- Integration test: Verify scheduled search runs at specified interval (use short interval for testing)
- Integration test: Verify comparison logic detects new sanctions matches
- Integration test: Verify notification sent when status changes
- UI test: Verify monitoring status displayed in history
- UI test: Verify pause/cancel monitoring functional

---

### US-5.8: Audit Trail and Compliance Reporting

**Type**: Functional
**Priority**: Should Have
**Status**: 📋 Planned

**User Story**

As a compliance officer
I want to generate audit trail reports showing all searches, exports, and deletions
So that I can demonstrate due diligence to regulators.

**Acceptance Criteria**

- System logs all user actions: searches performed, searches restored, exports, deletions, note edits
- Each log entry includes: timestamp, user ID, action type, entity name, IP address
- System provides "Audit Trail" report page accessible from settings
- Audit report filterable by: date range, user, action type, entity
- System exports audit trail as CSV for external review
- Audit trail immutable (cannot be edited or deleted)
- System retains audit logs for minimum 3 years

**Verification**

- Integration test: Verify all user actions logged to database
- UI test: Verify "Audit Trail" page accessible
- UI test: Verify filters functional
- Integration test: Export audit trail as CSV and verify completeness
- Unit test: Verify log entries include all required fields
- Integration test: Verify logs retained for 3+ years (test with backdated entries)
- Integration test: Verify logs cannot be modified or deleted via application

---

## Category 6: Reporting and Intelligence Analysis

### US-6.1: LLM-Generated Intelligence Report

**Type**: Functional
**Priority**: Must Have
**Status**: ✅ Implemented in v2.1.0

**User Story**

As an international relations staff member
I want an AI-generated intelligence report synthesizing all findings
So that I can provide stakeholders with actionable insights without manually writing reports.

**Acceptance Criteria**

- System sends all search results (sanctions, media, financial) to LLM (OpenAI GPT-4 or Anthropic Claude)
- LLM generates report with sections:
  - Executive Summary (2-3 paragraphs with risk assessment)
  - Sanctions Analysis (details of matches, jurisdictions, list types)
  - Media Intelligence (synthesis of official and general sources)
  - Financial Intelligence (directors, shareholders, transactions analysis)
  - Geopolitical Context (relevant international relations considerations)
  - Recommendations (suggested next steps, further investigation areas)
- Report length: 1000-2000 words
- Report displayed in "📊 INTELLIGENCE REPORT" tab
- Report includes "Generated by AI" disclaimer
- Report available for PDF export

**Verification**

- Integration test: Run search and verify intelligence report generated
- Manual verification: Review report quality for sample entities (coherence, accuracy, relevance)
- Manual verification: Verify all required sections present
- UI test: Verify report displayed in dedicated tab
- UI test: Verify AI disclaimer present
- Integration test: Verify report included in PDF export

---

### US-6.2: PDF Report Export with Formatting

**Type**: Functional
**Priority**: Must Have
**Status**: ✅ Implemented in v2.1.0

**User Story**

As a legal department reviewer
I want to export the intelligence report as a professionally formatted PDF
So that I can share it with stakeholders and archive it for compliance.

**Acceptance Criteria**

- System converts intelligence report to PDF format
- PDF includes: cover page with entity name and date, table of contents, formatted report sections, source citations
- PDF uses consistent formatting: headers, body text, lists
- PDF includes footer with page numbers and generation date
- PDF filename format: "{entity_name}_{date}_intelligence_report.pdf"
- PDF file size < 5 MB for typical report
- PDF downloadable via "Download Report" button

**Verification**

- Integration test: Generate PDF and verify file created
- Manual verification: Open PDF and review formatting, completeness, readability
- Manual verification: Verify cover page, table of contents, citations present
- UI test: Verify "Download Report" button functional
- Integration test: Verify filename format correct
- Performance test: Verify PDF generation < 10 seconds

---

### US-6.3: Excel Multi-Sheet Export

**Type**: Functional
**Priority**: Must Have
**Status**: ✅ Implemented in v2.1.0

**User Story**

As a risk analyst
I want to export search results as an Excel file with multiple sheets
So that I can perform custom analysis and share structured data with my team.

**Acceptance Criteria**

- System generates Excel workbook (.xlsx) with sheets:
  - Summary: Entity name, country, risk level, search date, sanctions count, subsidiary count
  - Sanctions Matches: Database, entity name, match score, entity type, address, list type
  - Media Coverage: Source type, title, URL, snippet
  - Subsidiaries: Name, country, ownership %, level, sanctions status
  - Sisters: Name, country, parent company, sanctions status
  - Directors & Officers: Name, title, nationality, sanctions status, source filing
  - Major Shareholders: Name, ownership %, voting rights, jurisdiction, sanctions status
  - Related Party Transactions: Counterparty, amount, transaction type, relationship
  - Intelligence Report: Full text of LLM-generated report
- Excel includes formatting: headers bold, risk levels color-coded, numbers formatted as percentages/currency
- Excel filename format: "{entity_name}_{date}_data.xlsx"
- Excel downloadable via "Export as Excel" button

**Verification**

- Integration test: Generate Excel export and verify file created
- Manual verification: Open Excel and verify all sheets present with correct data
- Manual verification: Verify formatting (bold headers, color coding, number formats)
- UI test: Verify "Export as Excel" button functional
- Integration test: Verify filename format correct
- Integration test: Test export with large dataset (100+ subsidiaries, 50+ directors)

---

### US-6.4: Email/Notification System for Search Completion

**Type**: System
**Priority**: Should Have
**Status**: 📋 Planned

**User Story**

As an international relations staff member
I want to receive an email notification when a long-running search completes
So that I can work on other tasks without monitoring the application.

**Acceptance Criteria**

- System provides email notification toggle in Settings
- User enters email address for notifications
- System sends email when search completes (typically for conglomerate searches > 5 minutes)
- Email includes: entity name, completion time, risk level, link to results
- Email subject: "Search Complete: {entity_name} - Risk Level: {risk_level}"
- System provides in-app notification icon with count of unread notifications
- Notifications dismissable by user

**Verification**

- UI test: Verify email toggle and input in Settings
- Integration test: Run long search and verify email sent upon completion
- Manual verification: Review email formatting and content
- UI test: Verify in-app notification icon displays count
- UI test: Verify clicking notification navigates to results
- UI test: Verify notification dismissal functional

---

### US-6.5: Enhanced Analytics Dashboard

**Type**: UI
**Priority**: Could Have
**Status**: 📋 Planned

**User Story**

As a compliance officer
I want a dashboard showing analytics on all searches (total searches, risk level distribution, top searched entities, trends over time)
So that I can understand patterns and reporting needs across the organization.

**Acceptance Criteria**

- System provides "Analytics" page accessible from sidebar
- Dashboard displays metrics:
  - Total searches (all-time and last 30 days)
  - Risk level distribution (pie chart: SAFE, LOW, MID, HIGH, VERY HIGH)
  - Top 10 most searched entities
  - Search volume over time (line chart by month)
  - Average search duration
  - Most common tags
  - Database usage (count by sanctions database, data source)
- Dashboard filterable by date range
- Dashboard exportable as PDF summary report

**Verification**

- UI test: Verify "Analytics" page accessible
- UI test: Verify all metrics displayed with correct calculations
- Integration test: Test with database containing 100+ searches spanning 6 months
- UI test: Verify charts render correctly
- UI test: Verify date range filter updates metrics
- UI test: Verify PDF export functional

---

## Category 7: System Configuration and Settings

### US-7.1: Settings Panel for Configuration

**Type**: UI
**Priority**: Must Have
**Status**: ✅ Implemented in v2.1.0

**User Story**

As a user
I want a settings panel to configure auto-save, fuzzy matching thresholds, and data source preferences
So that I can customize the system to my workflow needs.

**Acceptance Criteria**

- System provides "⚙️ SETTINGS" expander accessible from main interface
- Settings include:
  - Auto-save toggle (on/off)
  - Fuzzy matching threshold slider (0-100%, default 80%)
  - Data source toggles: SEC EDGAR, OpenCorporates, Wikipedia, DuckDuckGo
  - LLM provider selection: OpenAI GPT-4, Anthropic Claude
  - Email notification toggle and email address input
- Settings persist across sessions (stored in database or local storage)
- Settings apply immediately (no restart required)
- Settings show "Saved" confirmation message after changes

**Verification**

- UI test: Verify "⚙️ SETTINGS" expander accessible
- UI test: Verify all settings controls functional (toggles, slider, dropdowns)
- Integration test: Change settings and verify they persist after page refresh
- Integration test: Verify settings applied immediately (e.g., change fuzzy threshold and verify next search uses new value)
- UI test: Verify "Saved" confirmation message

---

### US-7.2: API Key Management

**Type**: System
**Priority**: Must Have
**Status**: ✅ Implemented in v2.1.0

**User Story**

As a system administrator
I want to manage API keys securely via environment variables
So that credentials are not hardcoded in the application.

**Acceptance Criteria**

- System reads API keys from .env file: OPENAI_API_KEY, ANTHROPIC_API_KEY, OPENCORPORATES_API_KEY
- System provides clear error messages if required API keys missing (e.g., "OpenAI API key not found. Please set OPENAI_API_KEY in .env file.")
- System never logs or displays API keys in plaintext
- System handles API key rotation without code changes (just update .env and restart)
- README includes .env.example template with all required keys

**Verification**

- Integration test: Remove API key from .env and verify error message displayed
- Manual verification: Review code to ensure API keys not hardcoded
- Manual verification: Check logs to ensure API keys not logged
- Integration test: Verify .env.example template exists and includes all keys
- Manual verification: Verify API keys used correctly for external API calls

---

### US-7.3: Database Backup and Restore

**Type**: System
**Priority**: Should Have
**Status**: 📋 Planned

**User Story**

As a system administrator
I want to backup and restore the SQLite database
So that I can prevent data loss and migrate to new systems.

**Acceptance Criteria**

- System provides "Backup Database" button in Settings
- Backup creates .db file copy with timestamp: "sanctions_backup_2026-03-11.db"
- Backup downloadable to user's machine
- System provides "Restore Database" button accepting .db file upload
- Restore replaces current database with uploaded file (with confirmation dialog)
- System displays database size and last backup date in Settings
- System recommends weekly backups for databases > 100 MB

**Verification**

- UI test: Verify "Backup Database" button functional
- Integration test: Create backup and verify file downloaded with correct filename
- Integration test: Upload backup file and verify database restored correctly
- UI test: Verify confirmation dialog for restore
- UI test: Verify database size and last backup date displayed
- Manual verification: Test backup/restore cycle with sample database

---

## Category 8: Individual Background Screening

### US-8.1: Multi-Country Criminal Records Database Integration

**Type**: Functional
**Priority**: Must Have
**Status**: 📋 Planned

**User Story**

As an international relations staff member
I want to screen individuals against criminal databases across multiple jurisdictions
So that I can identify criminal backgrounds that could pose risks to entity engagement.

**Acceptance Criteria**

- System queries criminal records databases for multiple countries:
  - **US**: FBI Criminal Justice Information Services (CJIS) via authorized channels, state criminal records APIs where available
  - **UK**: Police National Computer (PNC) equivalent public records
  - **EU**: European Criminal Records Information System (ECRIS) where accessible via member state systems
  - **Singapore**: Singapore Police Force public records (where accessible)
  - **China**: Public criminal records databases (limited availability)
  - **International**: Interpol Red Notices (public dataset)
- System returns criminal records with: jurisdiction, offense type, conviction date, sentence, case ID
- System classifies severity: felonies (high risk), misdemeanors (medium risk), pending charges, arrests without conviction
- System handles API failures gracefully with clear error messages per data source
- System displays match confidence scores (exact name match, DOB match, address match)

**Verification**

- Integration test: Query individual with known criminal record in each jurisdiction and verify match returned
- Integration test: Verify all configured data sources queried
- Unit test: Verify fallback behavior when API unavailable
- UI test: Verify criminal records display jurisdiction, offense type, and severity classification
- Manual verification: Test with sample individuals across multiple countries

---

### US-8.2: Sex Offender Registry Screening

**Type**: Functional
**Priority**: Must Have
**Status**: 📋 Planned

**User Story**

As a compliance officer
I want to check individuals against national sex offender registries
So that I can identify registered sex offenders and assess reputational risk.

**Acceptance Criteria**

- System queries sex offender registries for multiple countries:
  - **US**: National Sex Offender Public Website (NSOPW) API integration
  - **UK**: ViSOR (Violent and Sex Offender Register) public access equivalents
  - **Other jurisdictions**: Equivalent national registries where available
- System prominently flags any sex offender registry matches as VERY HIGH RISK
- System returns registry data: offense type, conviction date, registration status, risk level
- System displays photo and physical description if available in public records
- System provides source citation with registry name and record ID

**Verification**

- Integration test: Query known registered offenders and verify matches returned
- UI test: Verify VERY HIGH RISK flag displayed prominently for registry matches
- Manual verification: Verify ethical handling of sensitive data
- Integration test: Test NSOPW API integration with sample queries
- UI test: Verify registry match details display correctly

---

### US-8.3: Automatic Country Detection for Individual Screening

**Type**: Functional
**Priority**: Must Have
**Status**: 📋 Planned

**User Story**

As an international relations staff member
I want the system to automatically determine which countries to screen for each individual
So that I don't have to manually research jurisdictions for every person.

**Acceptance Criteria**

- System automatically extracts individuals from entity searches:
  - Directors and officers from SEC EDGAR DEF 14A filings
  - Ultimate Beneficial Owners from OpenCorporates/Open Ownership Register
  - Key executives from corporate registry data
- System infers countries to check based on:
  - Individual's address in SEC filings (extract country from DEF 14A)
  - Entity's jurisdiction (e.g., UK company → check UK records for directors)
  - Entity's subsidiary locations (presence in country = potential individual activity)
- System displays country selection interface with checkboxes for each individual
- Staff can manually add/remove countries (e.g., add US if director has prior US employment)
- System defaults to checking individual's primary country + entity's jurisdiction

**Verification**

- Integration test: Extract individuals from sample SEC DEF 14A filing and verify country inference
- Unit test: Verify country inference logic for various entity structures
- UI test: Verify country selection checkboxes displayed correctly
- Integration test: Test manual country override functionality
- Manual verification: Review country inference accuracy for sample entities

---

### US-8.4: Role-Specific Financial Crimes Screening

**Type**: Functional
**Priority**: Should Have
**Status**: 📋 Planned

**User Story**

As a risk analyst
I want to check individuals in financial positions for industry-specific violations
So that I can identify financial crimes, regulatory actions, and securities violations.

**Acceptance Criteria**

- System infers individual's role from job title in SEC filings (CFO, treasurer, controller, VP Finance)
- For individuals in financial roles, system queries:
  - **FinCEN Enforcement Actions**: Money laundering, Bank Secrecy Act violations
  - **SEC Enforcement Actions**: Securities fraud, insider trading, officer/director bars
  - **FINRA BrokerCheck**: Broker-dealer disciplinary history, customer complaints, regulatory actions
  - **CFTC Enforcement Actions**: Commodity trading violations, fraud
- System flags individuals with regulatory actions prominently in risk assessment
- System displays: violation type, enforcement date, penalty amount, bar duration
- System provides source links to enforcement action documents

**Verification**

- Integration test: Query individual with known SEC enforcement action and verify match
- Integration test: Test FINRA BrokerCheck API integration
- UI test: Verify enforcement actions displayed with violation details
- Manual verification: Test with known financial crime cases
- Unit test: Verify role inference logic from job titles

---

### US-8.5: Professional Licensing and Sanctions Screening

**Type**: Functional
**Priority**: Should Have
**Status**: 📋 Planned

**User Story**

As a compliance officer
I want to check if individuals are barred from professional practice
So that I can identify license suspensions, disbarments, and professional sanctions.

**Acceptance Criteria**

- System infers professional role from job title (physician, attorney, CPA, engineer)
- System queries role-specific licensing databases:
  - **Medical roles**: OIG Exclusions Database (healthcare fraud, barred from Medicare/Medicaid programs)
  - **Legal roles**: State bar disciplinary records and disbarment notices (all 50 US states + UK, EU equivalents)
  - **Accounting roles**: AICPA disciplinary actions and state board sanctions
  - **Engineering roles**: Professional engineering board disciplinary actions
- System flags barred professionals prominently as HIGH RISK
- System displays: sanction type, effective date, jurisdiction, reason for discipline
- System provides links to disciplinary documents where available

**Verification**

- Integration test: Query individual with known OIG exclusion and verify match
- Integration test: Test state bar API integration for multiple states
- UI test: Verify professional sanctions displayed with discipline details
- Manual verification: Test with known disbarred professionals
- Unit test: Verify professional role inference from job titles

---

### US-8.6: Government Debarment List Screening

**Type**: Functional
**Priority**: Should Have
**Status**: 📋 Planned

**User Story**

As a government relations staff member
I want to check if individuals are excluded from government contracts
So that I can identify debarred individuals and assess contract eligibility risk.

**Acceptance Criteria**

- System queries government debarment databases:
  - **SAM.gov**: System for Award Management exclusions database (US federal contracts)
  - **UN Procurement**: UN vendor debarment list
  - **World Bank**: World Bank debarment list
  - **Cross-reference**: USAspending.gov for past contract violations
- System flags debarred individuals prominently as HIGH RISK
- System displays: debarment reason, effective date, expiration date, procuring agency
- System indicates impact: which government agencies/programs individual barred from
- System provides source links to debarment notices

**Verification**

- Integration test: Query individual with known SAM.gov exclusion and verify match
- Integration test: Test SAM.gov API integration
- UI test: Verify debarment details displayed correctly
- Manual verification: Test with known debarred individuals
- Integration test: Verify UN and World Bank debarment list queries

---

### US-8.7: Integrated Individual Risk Reporting

**Type**: Functional
**Priority**: Must Have
**Status**: 📋 Planned

**User Story**

As an international relations staff member
I want to view consolidated individual screening results in the entity intelligence report
So that I can assess personnel risks alongside entity-level risks in a single document.

**Acceptance Criteria**

- System generates new section in intelligence report: "Personnel Risk Assessment"
- Personnel section includes:
  - List of all screened individuals with names, roles, jurisdictions
  - Risk score for each individual (SAFE, LOW, MID, HIGH, VERY HIGH)
  - Criminal records summary with jurisdiction and offense type
  - Sanctions matches, role-specific violations, debarment status
  - High-risk individuals highlighted prominently with red flags
  - Source citations for all findings (database name, record ID, query date)
- System displays personnel risk summary in executive summary section
- System integrates personnel risks into overall entity risk score calculation
- Personnel section exportable as part of PDF and Excel reports

**Verification**

- Manual verification: Review report format and completeness for sample entities
- UI test: Verify personnel risk section displays correctly in intelligence report
- Integration test: Verify personnel risks integrated into overall entity risk score
- UI test: Verify high-risk individuals highlighted prominently
- Integration test: Test PDF and Excel export with personnel section

---

### US-8.8: Standalone Individual Search Mode

**Type**: Functional
**Priority**: Should Have
**Status**: 📋 Planned

**User Story**

As an international relations staff member
I want to search for an individual directly (not through an entity search)
So that I can assess individuals when entity context is not available or relevant.

**Acceptance Criteria**

- System provides "Individual Search" mode option in UI (separate from entity search)
- Individual search input fields:
  - Full name (required)
  - Date of birth (optional, improves match accuracy)
  - Nationality (optional)
  - Countries of residence (checkboxes: US, UK, EU, Singapore, China, Other)
  - Professional role (optional, enables role-specific screening)
- System performs all background checks for specified individual:
  - Criminal records across selected countries
  - Sex offender registries
  - Role-specific screening (if role provided)
  - Government debarment lists
- System generates individual-focused risk report with all findings
- Individual report exportable as PDF with all source citations

**Verification**

- UI test: Verify "Individual Search" mode accessible from main interface
- UI test: Verify all input fields functional and validated correctly
- Integration test: Test individual search with sample data across multiple countries
- Manual verification: Review individual-focused report format and completeness
- Integration test: Test PDF export for individual reports

---

---

## Category 9: API Layer & Front-End Integration

### US-9.1: RESTful API Endpoint Structure

**Type**: System
**Priority**: Must Have
**Status**: 📋 Planned

**User Story**

As a front-end developer
I want a well-structured RESTful API with clear endpoints
So that I can build the React UI efficiently with predictable request/response patterns.

**Acceptance Criteria**

- API follows REST conventions with resource-based URLs:
  - `POST /api/v1/search/entity` - Create basic entity search
  - `POST /api/v1/search/conglomerate` - Create conglomerate search
  - `POST /api/v1/search/reverse` - Create reverse search
  - `POST /api/v1/search/individual` - Create individual background check
  - `GET /api/v1/history/searches` - List all saved searches
  - `GET /api/v1/history/searches/{id}` - Get specific search by ID
  - `POST /api/v1/history/searches/{id}/restore` - Restore saved search
  - `DELETE /api/v1/history/searches/{id}` - Delete search
  - `GET /api/v1/export/{id}/pdf` - Export as PDF
  - `GET /api/v1/export/{id}/excel` - Export as Excel
  - `GET /api/v1/export/{id}/json` - Export as JSON
- All endpoints return JSON (except export endpoints which return file streams)
- HTTP status codes follow standards: 200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 404 Not Found, 500 Internal Server Error
- Error responses follow consistent format: `{"error": "message", "detail": {...}}`
- API versioned in URL path (`/api/v1/`) for future compatibility

**Verification**

- Integration test: Call each endpoint and verify correct HTTP status codes
- Integration test: Verify JSON response structure matches API documentation
- Manual verification: Review OpenAPI documentation at `/docs` endpoint
- Integration test: Test error scenarios return proper error format

---

### US-9.2: Request/Response Validation with Pydantic

**Type**: System
**Priority**: Must Have
**Status**: 📋 Planned

**User Story**

As a back-end developer
I want automatic request validation using Pydantic models
So that invalid requests are rejected before reaching business logic.

**Acceptance Criteria**

- All API endpoints use Pydantic models for request validation
- Example search request model:
  ```python
  class EntitySearchRequest(BaseModel):
      entity_name: str = Field(..., min_length=1, max_length=500)
      country: Optional[str] = Field(None, max_length=100)
      fuzzy_enabled: bool = True
      fuzzy_threshold: int = Field(80, ge=0, le=100)
  ```
- Invalid requests return 422 Unprocessable Entity with validation errors
- Response models ensure consistent JSON structure:
  ```python
  class EntitySearchResponse(BaseModel):
      search_id: str
      timestamp: datetime
      entity_name: str
      risk_level: RiskLevel
      matches: List[SanctionMatch]
      intelligence_report: str
  ```
- Pydantic models auto-generate JSON Schema for OpenAPI docs

**Verification**

- Unit test: Verify Pydantic models reject invalid data types
- Integration test: Send invalid request (missing required field) and verify 422 error
- Integration test: Verify response structure matches Pydantic model
- Manual verification: Review generated JSON Schema in OpenAPI docs

---

### US-9.3: Async API Endpoints for Concurrent External API Calls

**Type**: System
**Priority**: Must Have
**Status**: 📋 Planned

**User Story**

As a system architect
I want all I/O operations to use async/await
So that external API calls (OFAC, SEC, OpenCorporates) can run concurrently without blocking.

**Acceptance Criteria**

- All route handlers declared with `async def`
- External API calls use `httpx.AsyncClient` (not `requests`)
- Multiple API calls run concurrently with `asyncio.gather()`:
  ```python
  results = await asyncio.gather(
      usa_agent.search_async(params),
      sec_edgar.extract_async(cik),
      opencorporates.query_async(name),
      osint.research_async(entity)
  )
  ```
- Database operations use `aiosqlite` or SQLAlchemy async session
- Performance requirement: 10+ concurrent API calls complete within 30 seconds (not sequential 5-10 minutes)

**Verification**

- Performance test: Measure total time for conglomerate search with 10 subsidiaries
- Unit test: Verify `asyncio.gather()` used for concurrent operations
- Integration test: Verify all route handlers are async
- Load test: 10 concurrent API requests should not cause timeout

---

### US-9.4: WebSocket Support for Real-Time Search Progress

**Type**: System
**Priority**: Should Have
**Status**: 📋 Planned

**User Story**

As a user
I want to see real-time progress updates during long-running conglomerate searches
So that I know the system is working and can estimate completion time.

**Acceptance Criteria**

- WebSocket endpoint at `ws://api/v1/ws/search/{job_id}`
- When conglomerate search initiated, API returns job ID immediately:
  ```json
  {"job_id": "abc123", "status": "processing"}
  ```
- Server sends progress updates via WebSocket:
  ```json
  {"progress": 25, "message": "Searching level 2 subsidiaries (5/20 complete)"}
  ```
- Progress includes: percentage (0-100), current step, estimated time remaining
- On completion, send final message: `{"status": "completed", "result_id": "xyz789"}`
- React client displays progress bar updating in real-time

**Verification**

- Integration test: Connect WebSocket client and verify progress messages received
- Manual verification: Initiate conglomerate search and observe real-time progress bar in UI
- Performance test: Verify WebSocket messages sent within 500ms of progress update
- Integration test: Verify WebSocket closes cleanly on completion

---

### US-9.5: Automatic OpenAPI Documentation Generation

**Type**: System
**Priority**: Must Have
**Status**: 📋 Planned

**User Story**

As a front-end developer
I want interactive API documentation auto-generated from code
So that I can test endpoints without Postman and understand request/response formats.

**Acceptance Criteria**

- FastAPI auto-generates OpenAPI 3.0 specification from code
- Swagger UI accessible at `/docs` endpoint (interactive documentation)
- ReDoc alternative documentation accessible at `/redoc` endpoint
- All endpoints documented with:
  - Description of what endpoint does
  - Request body schema (auto-generated from Pydantic models)
  - Response body schema
  - Possible HTTP status codes
  - Example requests and responses
- "Try it out" functionality allows testing endpoints directly from browser

**Verification**

- Manual verification: Navigate to `/docs` and verify all endpoints listed
- Manual verification: Test "Try it out" feature for sample entity search
- Integration test: Verify OpenAPI spec available at `/openapi.json`
- Manual verification: Check ReDoc at `/redoc` for clean documentation view

---

### US-9.6: CORS Configuration for React Front-End

**Type**: System
**Priority**: Must Have
**Status**: 📋 Planned

**User Story**

As a system administrator
I want CORS properly configured to allow React front-end to access FastAPI back-end
So that cross-origin API calls work in production.

**Acceptance Criteria**

- FastAPI CORS middleware configured with allowed origins:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["http://localhost:3000", "https://app.example.com"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"]
  )
  ```
- Environment variable `CORS_ORIGINS` controls allowed origins
- Development: Allow `localhost:3000` (React dev server)
- Production: Allow only production front-end domain
- Preflight OPTIONS requests handled correctly

**Verification**

- Integration test: Make API call from React dev server (localhost:3000) and verify no CORS error
- Integration test: Make API call from unauthorized origin and verify blocked
- Manual verification: Check browser console for CORS errors during development
- Security test: Verify production allows only configured domain

---

### US-9.7: JWT Authentication and Authorization

**Type**: System
**Priority**: Should Have
**Status**: 📋 Planned

**User Story**

As a compliance officer
I want user authentication to control access to the system
So that only authorized staff can perform sanctions screening and view sensitive data.

**Acceptance Criteria**

- User registration endpoint: `POST /api/v1/auth/register`
- User login endpoint: `POST /api/v1/auth/login` returns JWT access token
- Protected endpoints require `Authorization: Bearer <token>` header
- JWT tokens include: user ID, email, role, expiration (24 hours)
- Token refresh endpoint: `POST /api/v1/auth/refresh` for token renewal
- Password hashing using `passlib` with bcrypt
- Unauthorized requests return 401 Unauthorized

**Verification**

- Integration test: Register user, login, and verify JWT token returned
- Integration test: Call protected endpoint without token and verify 401 error
- Integration test: Call protected endpoint with valid token and verify access granted
- Security test: Verify passwords stored as hashed (not plaintext)
- Integration test: Verify expired tokens rejected

---

### US-9.8: API Rate Limiting and Throttling

**Type**: System
**Priority**: Should Have
**Status**: 📋 Planned

**User Story**

As a system administrator
I want API rate limiting to prevent abuse and ensure fair resource usage
So that a single user cannot overwhelm the system with excessive requests.

**Acceptance Criteria**

- Rate limiting applied using `slowapi` library
- Limits per endpoint:
  - Search endpoints: 60 requests/minute per user
  - Export endpoints: 20 requests/minute per user
  - History endpoints: 100 requests/minute per user
- Rate limit exceeded returns 429 Too Many Requests with `Retry-After` header
- Rate limit headers included in responses:
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Requests remaining in window
  - `X-RateLimit-Reset`: When limit resets (Unix timestamp)

**Verification**

- Integration test: Make 61 requests in 1 minute and verify 429 on 61st request
- Integration test: Verify rate limit headers present in response
- Manual verification: Test `Retry-After` header value matches expected reset time
- Load test: Multiple users should have independent rate limit counters

---

---

# 4. System-wide Non-Functional Requirements

## 4.1 Performance

**Requirement**: System must provide responsive user experience and handle large datasets efficiently.

**Specific Metrics**:

- **Restore Time**: < 2 seconds for any saved search (including 100+ subsidiary conglomerates)
- **Fresh Search Time**:
  - Basic sanctions screening: < 30 seconds
  - Conglomerate search (10 subsidiaries): < 5 minutes
  - Conglomerate search (100+ subsidiaries): < 15 minutes
- **Save Time**: < 5 seconds for complete search serialization
- **API Response Time**: External API calls complete within configured timeouts (30 seconds typical)
- **Database Query Time**: < 500ms for search history filtering and sorting queries
- **LLM Report Generation**: < 60 seconds for intelligence report synthesis
- **PDF Export**: < 10 seconds for report generation
- **Excel Export**: < 15 seconds for multi-sheet workbook with 100+ rows per sheet
- **Graph Rendering**: < 3 seconds to render network graph with 50 nodes
- **Page Load Time**: < 2 seconds for initial application load
- **API Response Time**:
  - GET requests: < 100ms (cached data)
  - POST search requests: < 30 seconds (basic), < 5 minutes (conglomerate)
  - WebSocket message latency: < 500ms
- **Concurrent Users**: Support 50+ simultaneous users without performance degradation
- **Front-End Load Time**:
  - Initial page load: < 3 seconds (including bundle download)
  - Route navigation: < 500ms (client-side routing)
  - Component render: < 100ms for UI interactions
- **Trade Data Queries**: < 30 seconds for entity with < 100 shipments/year (ImportYeti/ImportGenius)
- **Procurement Queries**: < 15 seconds via USAspending.gov API for entity with < 50 contracts
- **Offshore Analysis**: < 10 seconds using existing conglomerate data + jurisdiction matching
- **Financial Flow Dashboard**: < 5 seconds to render comprehensive dashboard with charts
- **Director Pivot Queries**: < 15 seconds per director via OpenCorporates officer search
- **WHOIS/Reverse WHOIS**: < 10 seconds via Whoxy API (freemium)
- **Technology Stack Analysis**: < 20 seconds via BuiltWith API (paid)
- **OCCRP Aleph Queries**: < 30 seconds (free for journalists, requires account)
- **LittleSis Queries**: < 10 seconds (completely free, open API)
- **Google Dorking**: < 30 seconds for 5 advanced queries
- **SpiderFoot Scan**: < 2 minutes for full domain footprint (open source)

**Verification**:
- Performance test: Measure all operations with timer and verify meet targets
- Load test: Test with maximum expected data volumes (1000 saved searches, 100 subsidiary conglomerate)
- Stress test: Concurrent usage simulation (10 simultaneous searches)
- Performance test: Measure trade data query time for high-volume importers (100+ shipments)

---

## 4.2 Security

**Requirement**: System must protect sensitive data and prevent unauthorized access.

**Specific Metrics**:

- **API Key Protection**: All API keys stored in .env file (never hardcoded or logged)
  - Trade Intelligence API Keys: ImportGenius, Panjiva, TradeInt (paid subscriptions)
  - Procurement Data: USAspending.gov (public API, no authentication required)
  - Marketing Intelligence: Pathmatics API key (commercial license, ~$10K+/year)
  - OSINT API Keys:
    - `WHOXY_API_KEY` - Reverse WHOIS queries (freemium, $49/month for advanced)
    - `BUILTWITH_API_KEY` - Technology stack analysis (paid, ~$295/month)
    - `OCCRP_ALEPH_API_KEY` - Leak database access (free for journalists with approval)
    - `WHALEWISDOM_API_KEY` - 13F institutional tracking (freemium, $300/year for premium)
    - `CRUNCHBASE_API_KEY` - VC/startup data (freemium, $49/month for Pro)
  - Publicly Available APIs (no auth required):
    - LittleSis API (completely free)
    - Open Ownership Register (completely free)
    - Companies House UK PSC API (completely free)
    - SpiderFoot (open source, self-hosted)
- **Data Encryption**: SQLite database uses encryption at rest (via SQLCipher or file system encryption)
- **HTTPS Communication**: All external API calls use HTTPS (no plain HTTP)
- **Input Sanitization**: All user inputs sanitized to prevent SQL injection, XSS attacks
- **No Hardcoded Secrets**: No passwords, tokens, or keys in source code
- **Audit Logging**: All user actions logged with timestamp for security review
- **Session Management**: User sessions expire after 24 hours of inactivity (if authentication added)
- **Error Messages**: Error messages do not expose sensitive system information (API keys, file paths)

**Verification**:
- Security audit: Review code for hardcoded secrets
- Penetration test: Test SQL injection, XSS attacks
- Manual verification: Verify .env usage for all API keys
- Integration test: Verify HTTPS used for all external calls
- Code review: Verify input sanitization on all user inputs

---

## 4.3 Reliability

**Requirement**: System must handle failures gracefully and maintain data integrity.

**Specific Metrics**:

- **API Failure Handling**: External API failures do not crash application (fallback to cached data or error message)
- **Data Integrity**: Save/restore operations maintain referential integrity (no orphaned records)
- **Error Recovery**: User can retry failed operations without data loss
- **Database Corruption Protection**: Database transactions rolled back on failure
- **Partial Results**: If some subsidiaries fail, system returns results for successful ones
- **Timeout Handling**: Long-running operations timeout after reasonable period (10 minutes) with user notification
- **Graceful Degradation**: Missing optional data sources (e.g., OpenCorporates API key) do not prevent core functionality

**Verification**:
- Integration test: Mock API failures and verify application continues
- Integration test: Simulate database write failure and verify rollback
- Integration test: Test partial subsidiary processing with some failures
- Manual verification: Review error handling for all external API calls
- Integration test: Test timeout behavior for long operations

---

## 4.4 Scalability

**Requirement**: System must handle growing data volumes and complexity without degradation.

**Specific Metrics**:

- **Database Size**: Support 1000+ saved searches (up to 5 GB database size)
- **Conglomerate Size**: Handle conglomerates with 100+ subsidiaries across 3 levels
- **Search History**: Filter and sort 1000+ searches in < 2 seconds
- **Graph Complexity**: Render network graphs with 100+ nodes and 200+ edges
- **Concurrent Users**: Support 10 simultaneous users without performance degradation (if multi-user deployment)
- **Data Growth**: Database performance remains consistent as size grows (indexing on key columns)

**Verification**:
- Load test: Populate database with 1000 saved searches and verify performance
- Integration test: Test conglomerate with 100+ subsidiaries
- Performance test: Measure query time for search history with 1000+ entries
- Stress test: Simulate 10 concurrent searches
- Manual verification: Review database schema for appropriate indexes

---

## 4.5 Usability

**Requirement**: System must be intuitive and accessible to users with varying technical expertise.

**Specific Metrics**:

- **Single Interface**: All data sources accessible from one interface (no separate logins)
- **Clear Risk Indicators**: Risk levels use color coding and plain language (SAFE, LOW, MID, HIGH, VERY HIGH)
- **Inline Help**: Tooltips and help text for complex features (fuzzy matching, ownership thresholds)
- **Progress Feedback**: Progress bars and status messages for long operations
- **Error Messages**: User-friendly error messages with actionable guidance (e.g., "OpenCorporates API key not found. Add OPENCORPORATES_API_KEY to .env file.")
- **Export Accessibility**: One-click export in multiple formats (JSON, Excel, PDF)
- **Mobile Compatibility**: Interface responsive and usable on tablet devices (laptop/desktop primary)
- **Keyboard Shortcuts**: Common actions accessible via keyboard (Enter to execute search, Esc to close dialogs)

**Verification**:
- Usability test: Observe new users performing common tasks (measure time to complete, error rate)
- UI test: Verify tooltips display on hover
- UI test: Verify progress indicators for long operations
- Manual verification: Review error messages for clarity
- UI test: Test interface on tablet device (iPad, Surface)
- UI test: Verify keyboard shortcuts functional

---

## 4.6 Data Quality

**Requirement**: System must provide accurate and trustworthy data with clear provenance.

**Specific Metrics**:

- **Fuzzy Matching Accuracy**: Configurable threshold (default 80%) balances recall and precision
- **Multi-Source Validation**: Sanctions matches verified across multiple databases when possible
- **Timestamp Tracking**: All searches and restored results show timestamp of data collection
- **Source Attribution**: Every data point shows source (database, filing, URL)
- **Data Freshness Indicator**: Restored searches display "Data as of {timestamp}" banner
- **Sanctions Database Coverage**: 10+ USA sanctions sources integrated
- **SEC Filing Currency**: SEC EDGAR queries use most recent available filings (within 1 year)
- **Geocoding Accuracy**: Entity locations geocoded to country level (city level if available)
- **Trade Data Accuracy**: Trade intelligence platforms (ImportYeti, Panjiva) provide Bills of Lading from official customs records; accuracy dependent on customs data quality (typically 95%+ for major ports)
- **Procurement Data Completeness**: USAspending.gov covers federal contracts > $10K; state/local contracts not included unless separately integrated
- **Ad Spend Estimation**: Pathmatics estimates are algorithmic (not official platform data); typically ±20% accuracy
- **Offshore Ownership Transparency**: Beneficial ownership data depends on jurisdiction disclosure laws; tax havens often have limited/zero disclosure
- **Director Network Accuracy**: OpenCorporates officer data typically 90%+ accurate for major jurisdictions; may be incomplete for smaller jurisdictions
- **WHOIS Data Completeness**: Many domains use WHOIS privacy services (registrant hidden); reverse WHOIS effective only when registrant details are public (~40% of corporate domains)
- **Technology Stack Detection**: BuiltWith accuracy ~85% for client-side technologies (JavaScript, analytics); may miss server-side infrastructure
- **Leak Database Coverage**: OCCRP Aleph covers major leaks (Panama Papers, Pandora Papers) but not all offshore entities are in leaks; absence from Aleph ≠ no offshore activity
- **Beneficial Ownership Transparency**: UBO data quality depends on jurisdiction; tax havens often have zero disclosure (Cayman, BVI); UK PSC data is reliable but may list intermediaries not ultimate individuals

**Verification**:
- Unit test: Verify fuzzy matching algorithm with known test cases (precision/recall metrics)
- Integration test: Cross-check sanctions matches across multiple databases for consistency
- UI test: Verify timestamps displayed on all searches
- UI test: Verify source attribution displayed for all data elements
- Manual verification: Spot-check 20 random sanctions matches for accuracy against official government websites
- Manual verification: Verify SEC filing recency for sample queries

---

## 4.7 Observability

**Requirement**: System must provide visibility into operations for debugging and monitoring.

**Specific Metrics**:

- **Application Logging**: All errors logged with timestamp, operation, error message, stack trace
- **User Action Logging**: All user actions logged for audit trail (search, restore, export, delete)
- **Performance Metrics**: Log search duration, API call duration, database query duration
- **API Call Tracking**: Log all external API calls (URL, status code, response time)
- **Database Operations**: Log all database writes (save, delete, update)
- **Error Reporting**: Errors displayed to user with unique error ID for support reference
- **Log Retention**: Logs retained for minimum 90 days
- **Log Export**: Logs exportable as CSV for analysis

**Verification**:
- Manual verification: Review log files for completeness
- Integration test: Trigger error and verify logged with all required fields
- Integration test: Perform user actions and verify logged
- UI test: Verify error ID displayed to user
- Manual verification: Verify log export functional

---

## 4.8 Maintainability

**Requirement**: System must be easy to understand, modify, and extend.

**Specific Metrics**:

- **Code Documentation**: All functions have docstrings describing purpose, parameters, return values
- **Modular Architecture**: Clear separation of concerns (agents, database, visualizations, export)
- **Configuration Externalization**: All configuration in .env or config files (not hardcoded)
- **Dependency Management**: requirements.txt maintained and up-to-date
- **Version Control**: Code in git repository with meaningful commit messages
- **Code Style**: PEP 8 compliant, formatted with Black
- **Type Hints**: Strict type hints enforced with Mypy (per CLAUDE.md project guidelines)
- **README Completeness**: Comprehensive README with installation, usage, troubleshooting

**Verification**:
- Code review: Verify docstrings present on all functions
- Static analysis: Run Black formatter and verify no changes needed
- Static analysis: Run Mypy and verify no type errors
- Static analysis: Run Ruff linter and verify no violations
- Manual verification: Review requirements.txt for accuracy
- Manual verification: Review README for completeness

---

# 5. Application Architecture

## 5.1 System Architecture Overview

The Entity Background Research Agent follows a **modern three-tier architecture** separating presentation, business logic, and data layers:

**Architecture Diagram**:
```
┌─────────────────────────────────────────┐
│         React Front-End (Client)        │
│  - Component-based UI (Material-UI)    │
│  - State management (Redux/Context)     │
│  - Real-time updates (WebSocket)        │
│  - Interactive visualizations (D3.js)   │
└──────────────┬──────────────────────────┘
               │ HTTPS/WSS
               │ REST API + WebSocket
┌──────────────▼──────────────────────────┐
│       FastAPI Back-End (Server)         │
│  - RESTful API endpoints                │
│  - Business logic orchestration         │
│  - External API integrations            │
│  - LLM report generation                │
│  - Authentication & authorization       │
└──────────────┬──────────────────────────┘
               │
               │ SQL Queries
┌──────────────▼──────────────────────────┐
│        SQLite Database (Data)           │
│  - Saved searches                       │
│  - Analysis history                     │
│  - Local entity caches                  │
│  - User preferences                     │
└─────────────────────────────────────────┘
```

## 5.2 Front-End Architecture

**Framework**: **React 18+** (TypeScript recommended)

**Key Design Principles**:
- **Component-Based**: Reusable UI components (SearchForm, ResultsTable, EntityGraph, RiskBadge)
- **Responsive Design**: Mobile-first approach supporting desktop, tablet, mobile
- **Progressive Enhancement**: Core functionality works without JavaScript (graceful degradation)
- **Accessibility**: WCAG 2.1 AA compliance for screen readers and keyboard navigation

**Technology Stack**:
- **UI Framework**: React 18+ with TypeScript
- **State Management**: Redux Toolkit or React Context API (for global state like search results, user settings)
- **Component Library**: Material-UI (MUI) or Ant Design for consistent defense/cyber theme styling
- **Data Visualization**:
  - **D3.js** for network graphs (replacing current Plotly/PyVis)
  - **Recharts** or **Victory** for charts and treemaps
  - **React Flow** for interactive conglomerate structure diagrams
- **HTTP Client**: Axios for API calls with interceptors for auth/error handling
- **Real-time Communication**: Socket.IO client for WebSocket connections
- **Build Tool**: Vite or Create React App with Webpack
- **Testing**: Jest + React Testing Library

**Folder Structure**:
```
frontend/
├── src/
│   ├── components/        # Reusable UI components
│   │   ├── SearchForm/
│   │   ├── ResultsTable/
│   │   ├── EntityGraph/
│   │   ├── RiskBadge/
│   │   └── IntelReport/
│   ├── pages/             # Route-level components
│   │   ├── Search.tsx
│   │   ├── ConglomerateSearch.tsx
│   │   ├── History.tsx
│   │   └── Settings.tsx
│   ├── hooks/             # Custom React hooks
│   ├── services/          # API client functions
│   ├── store/             # Redux store (if using Redux)
│   ├── types/             # TypeScript interfaces
│   └── utils/             # Helper functions
├── public/
└── package.json
```

## 5.3 Back-End Architecture

**Framework**: **FastAPI** (Python 3.10+)

**Key Design Principles**:
- **RESTful API Design**: Resource-based endpoints following REST conventions
- **Async-First**: All I/O operations (database, external APIs) use async/await
- **Layered Architecture**: Clear separation of routes, services, and data access
- **Dependency Injection**: FastAPI's dependency injection for database connections, auth
- **Type Safety**: Pydantic models for request/response validation

**Technology Stack**:
- **Web Framework**: FastAPI 0.100+
- **ASGI Server**: Uvicorn with Gunicorn for production
- **Database ORM**: SQLAlchemy 2.0 with async support (or continue raw SQLite)
- **Authentication**: JWT tokens with `python-jose` and `passlib` for password hashing
- **Task Queue**: Celery with Redis for background jobs (optional, for long-running searches)
- **WebSocket**: FastAPI native WebSocket support
- **Testing**: pytest + httpx (async client)
- **API Documentation**: Auto-generated OpenAPI/Swagger (built into FastAPI)

**API Endpoint Structure**:
```
/api/v1/
├── /search
│   ├── POST   /entity          # Basic entity search
│   ├── POST   /conglomerate    # Conglomerate search with depth
│   ├── POST   /reverse         # Reverse search (subsidiary → parent)
│   ├── POST   /individual      # Individual background check
│   └── GET    /status/{job_id} # Check async search status
├── /history
│   ├── GET    /searches        # List saved searches
│   ├── GET    /searches/{id}   # Get specific search
│   ├── POST   /searches/{id}/restore  # Restore saved search
│   └── DELETE /searches/{id}   # Delete search
├── /export
│   ├── GET    /{id}/pdf        # Export report as PDF
│   ├── GET    /{id}/excel      # Export as Excel
│   └── GET    /{id}/json       # Export as JSON
├── /settings
│   ├── GET    /                # Get user settings
│   └── PUT    /                # Update settings
└── /ws
    └── /search/{job_id}        # WebSocket for real-time updates
```

**Folder Structure**:
```
backend/
├── app/
│   ├── api/
│   │   ├── routes/         # API route handlers
│   │   │   ├── search.py
│   │   │   ├── history.py
│   │   │   ├── export.py
│   │   │   └── settings.py
│   │   └── dependencies.py # Dependency injection
│   ├── core/
│   │   ├── config.py       # Configuration management
│   │   ├── security.py     # Auth/JWT utilities
│   │   └── database.py     # Database connection
│   ├── services/           # Business logic layer
│   │   ├── usa_agent.py    # Existing USA sanctions agent
│   │   ├── research_agent.py
│   │   ├── graph_builder.py
│   │   └── export_service.py
│   ├── models/             # Pydantic models + SQLAlchemy models
│   │   ├── requests.py     # API request models
│   │   ├── responses.py    # API response models
│   │   └── database.py     # Database ORM models
│   └── utils/              # Utility functions
│       ├── serialization.py
│       ├── matching.py
│       └── export.py
├── tests/
├── main.py                 # FastAPI app entry point
└── requirements.txt
```

## 5.4 Data Flow

### Typical Search Request Flow:

1. **User Action**: User enters entity name in React UI and clicks "Execute Query"
2. **API Request**: React calls `POST /api/v1/search/entity` with JSON payload
3. **FastAPI Route**: Route handler validates request using Pydantic model
4. **Service Layer**: Business logic service orchestrates:
   - Query USA Sanctions API (async)
   - Query SEC EDGAR (async)
   - Query OpenCorporates (async)
   - Run OSINT research (async)
   - All 4 operations run concurrently using `asyncio.gather()`
5. **LLM Analysis**: Generate intelligence report using LLM
6. **Database Save**: Auto-save search results to SQLite
7. **API Response**: Return JSON response with results
8. **UI Update**: React receives response, updates state, renders results

### WebSocket Flow (for long-running searches):

1. User initiates conglomerate search (3-level depth, 100+ subsidiaries)
2. API returns job ID immediately: `{"job_id": "abc123", "status": "processing"}`
3. React opens WebSocket connection: `ws://api/v1/ws/search/abc123`
4. FastAPI sends progress updates: `{"progress": 25, "message": "Searching level 2 subsidiaries..."}`
5. React displays real-time progress bar
6. On completion, WebSocket sends: `{"status": "completed", "result_id": "xyz789"}`
7. React fetches full results: `GET /api/v1/history/searches/xyz789`

## 5.5 Migration Strategy

**Phase 1: API Development (Weeks 1-2)**
- Set up FastAPI project structure
- Implement core API endpoints (`/search/entity`, `/history/searches`)
- Migrate business logic from Streamlit to FastAPI services
- Add API documentation

**Phase 2: React Foundation (Weeks 3-4)**
- Set up React project with TypeScript
- Create core components (SearchForm, ResultsTable)
- Implement basic search workflow
- Connect to FastAPI endpoints

**Phase 3: Feature Parity (Weeks 5-8)**
- Migrate all Streamlit features to React
- Implement visualizations with D3.js/React Flow
- Add save/restore functionality
- Implement export features (PDF, Excel)

**Phase 4: Enhancement (Weeks 9-10)**
- Add WebSocket support for real-time updates
- Implement authentication/authorization
- Performance optimization
- Comprehensive testing

**Phase 5: Deployment (Week 11)**
- Deploy FastAPI to production (Docker + AWS/GCP)
- Deploy React build to CDN or static hosting
- Database migration
- User acceptance testing

## 5.6 Technology Justification

### Why React?
- **Industry Standard**: Largest ecosystem, extensive community support, abundant talent pool
- **Component Reusability**: Build once, use everywhere (SearchForm, RiskBadge across pages)
- **Performance**: Virtual DOM for efficient updates, code splitting for faster loads
- **Developer Experience**: Hot module replacement, React DevTools, extensive documentation
- **Ecosystem**: Rich library support (D3.js, Material-UI, Redux, React Testing Library)

### Why FastAPI?
- **Async Native**: Critical for concurrent external API calls (10+ databases queried simultaneously)
- **Type Safety**: Pydantic validation aligns with project's Mypy requirements
- **Performance**: Fastest Python framework, meets sub-2-second restore requirement
- **Documentation**: Auto-generated OpenAPI docs reduce documentation burden
- **Python Compatibility**: Reuse existing 26 Python modules with minimal refactor

### Why Not Alternatives?

| Alternative | Reason Not Chosen |
|------------|-------------------|
| Vue.js | Smaller ecosystem than React, less D3.js integration examples |
| Angular | Steeper learning curve, heavier framework, over-engineered for this use case |
| Flask | No native async support, slower than FastAPI, requires more boilerplate |
| Django | Too heavyweight, includes ORM (already using SQLite), admin panel not needed |
| Node.js/Express | Would require rewriting all Python business logic, losing existing investment |

---

# 6. Constraints and Dependencies

## 6.1 Technical Constraints

### Front-End Technology Stack
- **Framework**: React 18+ with TypeScript 5+
- **Build Tool**: Vite 4+ or Create React App
- **Component Library**: Material-UI (MUI) v5+ or Ant Design v5+
- **State Management**: Redux Toolkit or React Context API
- **Data Visualization**: D3.js v7+, Recharts v2+, React Flow v11+
- **HTTP Client**: Axios v1+
- **WebSocket Client**: Socket.IO client v4+
- **Browser Support**: Modern browsers (Chrome, Firefox, Safari, Edge) - last 2 versions

### Back-End Technology Stack
- **Framework**: FastAPI 0.100+ (Python 3.10+)
- **ASGI Server**: Uvicorn 0.23+ with Gunicorn for production
- **Database**: SQLite 3.35+ (single-file database, no separate database server)
- **Database Access**: SQLAlchemy 2.0+ with async support (optional) or raw SQL
- **Authentication**: JWT tokens with python-jose and passlib
- **Task Queue**: Celery + Redis (optional, for background jobs)
- **Testing**: pytest 7+ with httpx for async API testing

### Shared Constraints
- **External API Dependencies**: USA Sanctions API, SEC EDGAR, OpenCorporates (optional), DuckDuckGo Search
- **LLM Dependency**: OpenAI GPT-4 or Anthropic Claude API access required
- **Internet Connectivity**: Required for external API calls
- **Operating System**: Cross-platform (Windows, macOS, Linux)

### Deployment Architecture
- **Front-End Deployment**: Static hosting (Vercel, Netlify, AWS S3 + CloudFront, or Nginx)
- **Back-End Deployment**: Docker container on AWS ECS/EC2, GCP Cloud Run, or Azure App Service
- **Database**: SQLite file stored in persistent volume (or migrate to PostgreSQL for production scale)
- **CORS**: Configured to allow front-end domain to access back-end API

## 6.2 Assumptions

(From value_proposition.md Section 5)

1. **Data Availability**: Sanctioned entities and corporate relationships are sufficiently documented in public databases
2. **Name Consistency**: Entity names can be matched with reasonable accuracy using fuzzy matching
3. **Internet Access**: Users have reliable internet connectivity
4. **API Reliability**: External data sources remain accessible and stable
5. **User Capability**: Users can interpret risk assessments and validate AI-generated reports
6. **Scope Sufficiency**: USA-centric sanctions perspective is sufficient for organizational needs
7. **Timeliness Trade-off**: Users accept restored searches show historical data with timestamps
8. **LLM Access**: Organization maintains API access to OpenAI or Anthropic
9. **Public Source Quality**: Public data sources provide reasonably accurate information
10. **Regulatory Stability**: USA sanctions lists remain relevant over system's operational lifetime
11. **Database Infrastructure**: SQLite performance adequate for requirements
12. **Sanctions Centrality**: Sanctions screening is primary risk indicator
13. **Automation Acceptability**: Stakeholders trust system-generated reports with appropriate review
14. **English Language**: Most source data available in English (system can translate entity names)
15. **Single-User Focus**: Designed for individual analyst use (not collaborative multi-user workflows)

## 6.3 Regulatory and Compliance

- **Data Privacy**: System does not collect personal data (only entity/company information)
- **Export Control**: System output may be subject to export control regulations (user responsibility)
- **Sanctions Compliance**: System aids compliance but does not constitute legal advice
- **Audit Trail**: System provides audit trail for compliance review
- **Data Retention**: Configurable retention policy for saved searches (default: indefinite)

---

# 7. Verification Strategy Summary

## 7.1 Test Types

**Unit Tests**:
- Fuzzy matching algorithm accuracy
- Risk scoring calculation
- Data serialization/deserialization
- Utility functions (geocoding, text parsing)

**Integration Tests**:
- External API interactions (USA Sanctions, SEC EDGAR, OpenCorporates, DuckDuckGo)
- Database operations (save, restore, delete, query)
- LLM report generation
- Export functionality (JSON, Excel, PDF)
- Multi-source data aggregation
- Personnel sanctions cross-checking

**UI Tests**:
- User workflows (basic search, conglomerate search, reverse search, save/restore)
- Interactive visualizations (graph, map)
- Filter and sort functionality
- Button clicks and form submissions
- Error message display
- Settings panel functionality

**Performance Tests**:
- Restore time (target < 2 seconds)
- Save time (target < 5 seconds)
- Fresh search time (target < 30 seconds basic, < 15 minutes large conglomerate)
- Database query time (target < 500ms)
- Graph rendering (target < 3 seconds)

**Manual Verification**:
- LLM report quality (coherence, accuracy, relevance)
- Export format quality (PDF formatting, Excel layout)
- Fuzzy match accuracy review
- Source attribution completeness
- Error message clarity
- Documentation completeness (README, docstrings)

## 7.2 Test Coverage Goals

- **Code Coverage**: > 80% for core modules (agents, database, serialization)
- **API Integration**: All external APIs mocked for testing
- **User Workflows**: All 6 user journeys covered by end-to-end tests
- **Error Scenarios**: All error paths tested (API failures, invalid inputs, database errors)

---

# 8. Future Enhancements (Out of Current Scope)

## Won't Have (❌ Out of Scope)

The following features are explicitly out of scope and not planned:

1. **Real-time Monitoring/Streaming**: Live monitoring of sanctions list updates (system uses API queries, not real-time streams)
2. **Proprietary Intelligence Sources**: Integration with paid/proprietary intelligence databases (system focuses on public data)
3. **Multi-Tenancy**: Organization isolation and multi-tenant architecture (single-user or single-organization deployment)
4. **Blockchain Audit Trails**: Blockchain-based immutable audit logs (traditional database logging sufficient)
5. **Mobile Native Applications**: iOS/Android apps (web interface optimized for laptop/desktop/tablet)
6. **On-Premise Deployment Support**: Enterprise on-premise installation and support (cloud/local deployment only)
7. **Custom Sanctions Lists**: User-defined/custom sanctions lists management (system uses official government sources)
8. **Advanced User Management**: Role-based access control, approval workflows, team collaboration features

---

# 9. Glossary

**ASN (Autonomous System Number)**: Unique identifier for a block of IP addresses under single administrative control; used to find all network infrastructure owned by a corporation

**ASGI**: Asynchronous Server Gateway Interface - Python standard for async web servers and applications

**Bearer Shares**: Stock certificates with no registered owner; facilitates anonymous ownership

**BIS**: Bureau of Industry and Security (US Department of Commerce)

**BOL (Bill of Lading)**: Maritime shipping document identifying shipper, consignee, goods, and shipment details

**BODS (Beneficial Ownership Data Standard)**: Structured data standard for representing beneficial ownership information, used by Open Ownership Register

**BRIS (Business Register Interconnection System)**: EU system interconnecting national business registers across member states

**Conglomerate**: Parent company with multiple subsidiaries forming a corporate group

**CORS**: Cross-Origin Resource Sharing - mechanism allowing front-end to make requests to API on different domain

**Criminal Records Database**: National and local law enforcement databases containing arrest and conviction records for background screening purposes

**DEF 14A**: SEC proxy statement filing containing director and governance information

**DOD Section 1260H**: US Department of Defense designation of Chinese Military Companies

**ECRIS**: European Criminal Records Information System - EU system for exchanging criminal conviction information between member states

**FCC Covered List**: Federal Communications Commission list of communications equipment posing national security risk

**FinCEN**: Financial Crimes Enforcement Network - US Treasury bureau combating money laundering and financial crimes

**FINRA BrokerCheck**: Public database of broker-dealer disciplinary history, customer complaints, and regulatory actions maintained by the Financial Industry Regulatory Authority

**Fuzzy Matching**: Algorithm to find approximate string matches using similarity scores (Levenshtein distance)

**Google Dorking**: Use of advanced search operators to find exposed files, directories, and sensitive documents indexed by search engines

**HS Code (Harmonized System Code)**: International standardized system of product classification for customs

**Interlocking Directorate**: Board members who serve on boards of multiple companies simultaneously; indicates potential coordination or common control

**JWT**: JSON Web Token - compact URL-safe token format for authentication and information exchange

**Legal Entity Identifier (LEI)**: ISO 17442 standard identifier for entities engaged in financial transactions; used for cross-border entity resolution

**Nominee Director**: Individual listed as director but acting on behalf of undisclosed beneficial owner

**NSOPW**: National Sex Offender Public Website - US nationwide registry integrating state sex offender registries for public access

**OFAC**: Office of Foreign Assets Control (US Department of Treasury)

**Officer Pivot**: OSINT technique of searching for all companies where a specific individual holds director/officer positions; used to discover sister companies and hidden networks

**OSINT**: Open Source Intelligence (publicly available information)

**OIG Exclusions Database**: Office of Inspector General list of individuals and entities barred from participating in federal healthcare programs (Medicare, Medicaid) due to fraud or abuse

**PSC (Persons with Significant Control)**: UK Companies House registry of individuals/entities owning >25% of company or exercising significant influence

**Pydantic**: Python library for data validation using type hints; core component of FastAPI

**Registered Agent Address**: Professional service address used by multiple companies for official correspondence; companies at same registered agent address may be part of same corporate group or may be unrelated

**Related Party Transaction**: Financial transaction between entity and related parties (directors, shareholders, subsidiaries)

**REST**: Representational State Transfer - architectural style for designing networked applications using HTTP

**Reverse DNS**: Technique of looking up domain names associated with an IP address; used to discover sister company websites on shared hosting

**Reverse WHOIS**: Search technique to find all domains registered with the same email address, phone number, or registrant name; reveals hidden sister companies

**Role-Specific Screening**: Background checks tailored to an individual's professional position (finance, medical, legal, etc.) checking relevant licensing boards and industry regulators

**SAM.gov Exclusions**: System for Award Management database of individuals and entities barred from receiving federal contracts or assistance due to fraud, debarment, or suspension

**SEC EDGAR**: Electronic Data Gathering, Analysis, and Retrieval system (US Securities and Exchange Commission)

**Sister Company**: Entities owned by the same parent company (sibling subsidiaries)

**Sub-Award**: Federal contract payment from prime contractor to subcontractor (disclosed via USAspending.gov)

**Tax Haven**: Jurisdiction with low/zero taxation and high financial secrecy (e.g., Cayman Islands, BVI)

**TBML (Trade-Based Money Laundering)**: Money laundering method using trade transactions (over/under-invoicing, misclassification)

**Technology Stack Correlation**: Matching companies via shared digital infrastructure (Google Analytics tracking codes, AdSense IDs, tag managers); high-confidence indicator of common ownership

**UBO (Ultimate Beneficial Owner)**: Natural person who ultimately owns or controls entity

**Virtual Office**: Rented business address used by multiple companies; high concentration of companies at one address may indicate shell companies or registered agent service

**ViSOR**: Violent and Sex Offender Register - UK national database managed by police forces tracking registered sex offenders and violent offenders

**WebSocket**: Communication protocol providing full-duplex communication over single TCP connection for real-time updates

**10-K**: Annual report filed by US public companies with SEC

**20-F**: Annual report filed by foreign issuers with SEC

---

# Document Control

**Version History**:

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.2 | 2026-03-11 | IMDA Team | Added Section 5: Application Architecture; documented React front-end and FastAPI back-end migration; added Category 9: API Layer requirements (8 new functional requirements); updated technical constraints and performance metrics; system version 3.0.0 |
| 1.1 | 2026-03-11 | IMDA Team | Added Journey 6 and Category 8 for individual criminal background screening; system version 2.1.0 |
| 1.0 | 2026-03-11 | IMDA Team | Initial requirements document based on v2.1.0 implementation |

**Approval**:

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Owner | | | |
| Technical Lead | | | |
| Compliance Officer | | | |

**Next Review Date**: 2026-06-11 (Quarterly review)

---

**End of Requirements Document**
