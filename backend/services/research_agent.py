import os
import time
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from openai import OpenAI
from fpdf import FPDF

# Handle DDGS import
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

# Handle googlesearch import
try:
    from googlesearch import search as google_search
    GOOGLE_SEARCH_AVAILABLE = True
except ImportError:
    GOOGLE_SEARCH_AVAILABLE = False

try:
    from config import settings
    MAX_LEVEL_2_SEARCHES = settings.MAX_LEVEL_2_SEARCHES
    MAX_LEVEL_3_SEARCHES = settings.MAX_LEVEL_3_SEARCHES
except ImportError:
    MAX_LEVEL_2_SEARCHES = 20
    MAX_LEVEL_3_SEARCHES = 10

class SanctionsResearchAgent:
    def __init__(self):
        # Connect to local Ollama
        self.client = OpenAI(
            base_url='http://localhost:11434/v1',
            api_key='ollama',
        )
        self.model_id = "llama3.1"
        self.ddgs = DDGS()

        # OpenCorporates API setup
        self.opencorporates_api_key = os.getenv('OPENCORPORATES_API_KEY')
        self.opencorporates_base_url = "https://api.opencorporates.com/v0.4"

        # SEC EDGAR API setup
        self.sec_api_base = "https://www.sec.gov"
        self.sec_headers = {
            'User-Agent': 'Research Tool; faith_tan@imda.gov.sg)',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'www.sec.gov'
        }

        # Progress callback for UI updates
        self.progress_callback = None

    def _log(self, message, level="INFO"):
        """Internal logging that can optionally send to UI callback."""
        print(f"[{level}] {message}")
        if self.progress_callback:
            self.progress_callback(message, level)

    def _verify_relevance(self, entity_name, title, snippet):
        """
        INTERNAL: Uses Local LLM to strictly validate if a search result 
        is actually about the target entity. Returns (bool, reasoning).
        """
        # 1. Fast fail: If entity name isn't in title or snippet, discard immediately.
        # Normalize for case-insensitive check
        name_parts = entity_name.lower().split()
        text_content = (title + " " + snippet).lower()
        
        # Check if at least the main part of the name is present
        # (Heuristic: at least one significant word from the name must be there)
        if not any(part in text_content for part in name_parts if len(part) > 2):
            return False, "Entity name not found in text."

        # 2. LLM Verification
        prompt = f"""
        Review this search result snippet.
        Target Entity: "{entity_name}"
        Title: {title}
        Snippet: {snippet}

        Task: Determine if this link is RELEVANT to the entity being sanctioned, investigated, or added to a trade blacklist.
        
        Rules:
        1. If the snippet explicitly mentions "{entity_name}" in the context of sanctions, trade bans, or legal action, answer YES.
        2. If "{entity_name}" is missing or the text is a generic index/home page, answer NO.
        3. If it is a different company with a similar name, answer NO.

        Format: YES/NO || Reason
        Example: YES || Designated by OFAC.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=50
            )
            content = response.choices[0].message.content.strip()
            
            if content.upper().startswith("YES"):
                # Extract reason after "||" if present
                parts = content.split("||")
                reason = parts[1].strip() if len(parts) > 1 else "Confirmed relevant by AI."
                # Reject ambiguous YES where the reason admits the entity is not mentioned
                irrelevant_phrases = ["not explicitly mention", "is not explicitly mentioned", "does not explicitly mention"]
                if any(phrase in reason.lower() for phrase in irrelevant_phrases):
                    return False, "AI deemed irrelevant."
                return True, reason
            else:
                return False, "AI deemed irrelevant."
                
        except Exception:
            # Fallback to loose acceptance if LLM fails, but rely on string match
            return True, "AI verification skipped (Error)."

    def get_sanction_news(self, entity_name):
        """
        Search for CONFIRMED press releases with LLM Verification.
        """
        # Expanded sources including BIS (Commerce Dept) which is key for tech entities
        query = f'"{entity_name}" (sanction OR designation OR "entity list" OR "trade blacklist") site:treasury.gov OR site:state.gov OR site:justice.gov OR site:bis.doc.gov'
        
        try:
            # Fetch more candidates because we will filter aggressively
            results = self.ddgs.text(query, max_results=20)
            
            if not results:
                return []

            # Generic garbage filters
            ignored_substrings = [
                "/news/press-releases", "/press-releases/all", 
                "/policy-issues/financial-sanctions", "search.treasury.gov", 
                "search.bis.doc.gov", "/bureau-of-industry-and-security",
                "page not found", "index of"
            ]

            verified_hits = []
            seen_titles = set()

            for r in results:
                url = r.get('href', '')
                title = r.get('title', '')
                snippet = r.get('body', '')

                # Basic Deduplication
                if title in seen_titles: continue
                seen_titles.add(title)
                
                # Filter short/garbage URLs
                if len(url) < 30: continue
                
                # Clean URL checks
                is_generic = False
                clean_url = url.split('?')[0].rstrip('/') # Remove query params for checking
                
                if clean_url.endswith("/press-releases") or clean_url.endswith("/news"):
                    continue

                for ignored in ignored_substrings:
                    if ignored in url.lower():
                        is_generic = True
                        break
                
                if is_generic:
                    continue

                # --- STEP: VERIFICATION ---
                is_valid, relevance_reason = self._verify_relevance(entity_name, title, snippet)
                
                if is_valid:
                    verified_hits.append({
                        "title": title,
                        "url": url,
                        "relevance": relevance_reason,
                        "snippet": snippet,
                        "source_type": "official"  # Tag as official government source
                    })

                # Stop after finding 10 verified links (increased from 3)
                if len(verified_hits) >= 10:
                    break
            
            return verified_hits
                
        except Exception as e:
            print(f"Sanction news search failed: {e}")
            return []

    def get_general_media(self, entity_name):
        """
        Search for general media coverage from broader sources including
        news outlets, law firms, consultancies, and analysis providers.
        Returns up to 10 verified results tagged as 'general' sources.
        """
        # Query broader media sources (not limited to .gov sites)
        query = f'"{entity_name}" (sanctions OR "trade restrictions" OR "export controls")'

        try:
            # Fetch more candidates for filtering
            results = self.ddgs.text(query, max_results=25)

            if not results:
                return []

            # Filter out known generic/garbage pages
            ignored_substrings = [
                "wikipedia.org", "linkedin.com/in/",
                "facebook.com", "twitter.com", "instagram.com",
                "page not found", "index of", "/search?", "/tag/"
            ]

            verified_hits = []
            seen_titles = set()

            for r in results:
                url = r.get('href', '')
                title = r.get('title', '')
                snippet = r.get('body', '')

                # Basic Deduplication
                if title in seen_titles:
                    continue
                seen_titles.add(title)

                # Filter short/garbage URLs
                if len(url) < 30:
                    continue

                # Check against ignored patterns
                is_generic = False
                for ignored in ignored_substrings:
                    if ignored in url.lower():
                        is_generic = True
                        break

                if is_generic:
                    continue

                # Verify relevance using existing LLM verification
                is_valid, relevance_reason = self._verify_relevance(entity_name, title, snippet)

                if is_valid:
                    # Classify as official (.gov) or general
                    source_type = "official" if ".gov" in url else "general"

                    verified_hits.append({
                        "title": title,
                        "url": url,
                        "relevance": relevance_reason,
                        "snippet": snippet,
                        "source_type": source_type
                    })

                # Stop after finding 10 verified links
                if len(verified_hits) >= 10:
                    break

            return verified_hits

        except Exception as e:
            print(f"General media search failed: {e}")
            return []

    def _search_web(self, queries, max_results=2):
        """Helper: Performs searches and aggregates results."""
        aggregated_context = []
        seen_urls = set()

        for query in queries:
            try:
                time.sleep(0.5) 
                results = self.ddgs.text(query, max_results=max_results)
                
                if results:
                    for r in results:
                        url = r.get('href')
                        if url not in seen_urls:
                            seen_urls.add(url)
                            aggregated_context.append(
                                f"SOURCE: {r.get('title')} ({url})\nCONTENT: {r.get('body')}\n"
                            )
            except Exception as e:
                print(f"Search warning for '{query}': {e}")
                continue
        
        return "\n".join(aggregated_context) if aggregated_context else "No external information found."

    def generate_intelligence_report(self, entity_name):
        """Generates the detailed Markdown report."""
        search_queries = [
            f"{entity_name} US sanctions investigation lawsuit",
            f"{entity_name} lobbying activity US congress",
            f"{entity_name} official press release in recent years",
            f"{entity_name} major business partners collaborations",
            f"{entity_name} analysis reports by law firms and consultancies"
        ]
        
        evidence_text = self._search_web(search_queries)

        prompt = f"""
You are a Senior Intelligence Analyst. Produce a formal, COMPREHENSIVE "Due Diligence Intelligence Report" on the entity: "{entity_name}".

Use the following retrieved information as your ONLY source of evidence:
{evidence_text}

---
REPORT REQUIREMENTS:

1. **Tone**: Professional, objective, formal, and analytical.

2. **Length & Detail**: This must be a COMPREHENSIVE report, not a brief summary.
   - Each section should contain MULTIPLE PARAGRAPHS with in-depth analysis
   - Aim for 2-4 paragraphs per major section
   - Provide context, implications, and nuanced analysis
   - Total report should be 800-1200 words minimum

3. **Structure** (with detailed requirements for each section):

   **Executive Summary** (2-3 paragraphs)
   - **CRITICAL REQUIREMENT:** Start with explicit risk classification using this scoring rubric:

     **Risk Assessment Framework - Calculate total score (0-100):**

     1. **Regulatory & Legal Indicators (0-50 points)** — take the HIGHEST applicable item only (not additive):
        - Active sanctions listings: 50 points
        - Criminal investigations/charges: 40 points
        - Civil enforcement actions: 30 points
        - Regulatory violations/fines: 25 points
        - Pending investigations: 15 points
        - Past resolved issues (>3 years): 5 points

     2. **Media Signal Strength (0-20 points)** — ADDITIVE up to category max of 20, count each qualifying source:
        - Official government sources (treasury.gov, justice.gov, state.gov): 10 points each (max 20)
        - Major credible news (Reuters, Bloomberg, WSJ, AP): 3 points each (max 15)
        - General media/blogs: 1 point each (max 5)

     3. **Severity Factors (0-30 points)** — take the HIGHEST applicable item only (not additive):
        - National security concerns: 30 points
        - Financial crimes (money laundering, fraud): 15 points
        - Export control violations: 15 points
        - Corruption/bribery: 12 points
        - Environmental/labor violations: 8 points
        - Civil disputes: 5 points

     4. **Temporal Relevance (0-10 points)** — take the HIGHEST applicable item only (not additive):
        - Issues within last 6 months: 10 points
        - Issues within last 1 year: 8 points
        - Issues within last 3 years: 5 points
        - Older than 3 years: 2 points

     **Risk Level Thresholds:**
     - **Low (0-35 points)**: Limited concerns, minor historical issues, sparse media coverage
     - **Medium (36-65 points)**: Moderate regulatory concerns, ongoing investigations, notable media attention
     - **High (66-100 points)**: Active sanctions/enforcement, serious violations, extensive official documentation
     NOTE: If the raw sum of all 4 categories exceeds 100, cap the displayed score at 100.

     **Required Output Format:**
     Line 1: "Risk Level: [High/Medium/Low] (Score: XX/100)"
     Line 2: "Scoring Breakdown: [Category]: [Highest item] (+pts) | [Category]: [Highest item] (+pts) | ... | RAW: XX → SCORE: XX"

     Rules:
     - For each category, state the single highest-scoring item that applies and its point value in (+pts) notation
     - If multiple items apply in a category, note the top one and mention others in brackets, e.g. "Active sanctions (+50) [criminal charges also present]"
     - For Media Signal Strength, list each source type that contributed and its subtotal since it is additive, e.g. "2 Reuters (+6) + 1 gov source (+10) = 16"
     - Omit a category entirely if no items in it apply (score = 0)
     - RAW is the arithmetic sum of all category scores before capping; SCORE is min(RAW, 100)
     - Always end the breakdown line with "| RAW: XX → SCORE: XX"

     Example (score capped at 100):
     "Risk Level: High (Score: 100/100)
     Scoring Breakdown: Regulatory & Legal: Active sanctions (+50) [criminal charges also present] | Severity: National security (+30) | Media: 1 gov source (+10) = 10 | Temporal: Last 6 months (+10) | RAW: 100 → SCORE: 100"

     Example (score not capped):
     "Risk Level: High (Score: 69/100)
     Scoring Breakdown: Regulatory & Legal: Civil enforcement actions (+30) | Severity: Financial crimes (+15) | Media: 2 Reuters (+6) + 1 gov source (+10) = 16 | Temporal: Last 1 year (+8) | RAW: 69 → SCORE: 69"

   - Follow with 2-3 paragraphs explaining:
     * Summary of most significant findings
     * Nature and severity of key risk factors
     * Overall assessment and business implications

   **Regulatory & Legal Status** (2-4 paragraphs)
   - Detail any investigations, lawsuits, sanctions, or regulatory actions (US focus)
   - Discuss the nature, severity, and current status of legal issues
   - Analyze implications for business operations and compliance
   - Include historical context if relevant

   **Political Activity** (2-3 paragraphs)
   - Describe lobbying efforts, political contributions, or legislative scrutiny
   - Identify key political relationships and affiliations
   - Analyze potential political risks or controversies
   - Discuss government contracts or political influence

   **Recent Developments** (2-3 paragraphs)
   - Summarize major news, press releases, or announcements from the last 2 years
   - Highlight strategic changes, leadership changes, or significant events
   - Analyze how recent developments impact risk profile
   - Include both positive and negative developments

   **Collaborations & Business Relationships** (2-3 paragraphs)
   - Identify known partners, suppliers, customers, or joint ventures
   - Assess second-order risks from business relationships
   - Evaluate supply chain exposure and dependency risks
   - Discuss any controversial or high-risk partnerships

4. **Citations**: You MUST cite the source URL for EVERY factual claim using inline citations in this format: [Source: example.com]
   - Place citations immediately after each claim
   - Be specific about which source supports which claim
   - Every paragraph should have at least one citation

5. **MANDATORY: References Section**
   - At the very END of the report, you MUST include a "## References" section
   - List ALL unique source URLs cited in the report as a numbered APA-style list
   - Use APA 7th edition web citation format for each entry:
     * With known author: Author, A. A. (Year, Month Day). Title of article. *Website Name*. URL
     * Without known author: Title of article. (Year, Month Day). *Website Name*. URL
     * When date is unknown, use (n.d.) in place of the year
     * Infer the website name from the domain (e.g. treasury.gov → U.S. Department of the Treasury)
     * Use title-case for article titles
   - Example: U.S. Department of Justice. (2024, March 15). *Entity X added to sanctions list*. justice.gov. https://www.justice.gov/...
   - This section is REQUIRED even if you have inline citations

6. **Writing Quality**:
   - Use clear, professional language
   - Provide analysis, not just facts - explain "so what?"
   - Connect findings to risk implications
   - Be thorough but avoid unnecessary repetition

7. **Output Format**:
   - Start directly with "# Due Diligence Intelligence Report: {entity_name}"
   - Use Markdown formatting (##, ###, **, bullets)
   - No preambles or meta-commentary
   - End with the References section

REMEMBER: This is a COMPREHENSIVE intelligence report, not a brief summary. Provide detailed analysis with multiple paragraphs per section and ALWAYS include a References section at the end.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": "You are a professional intelligence analyst. Output in Markdown."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=4000  # Allows for longer, more detailed reports
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"**Error Generating Report:** {str(e)}"

    def translate_name(self, original_name):
        """
        Translates non-English entity name to English and SANITIZES the output.
        """
        prompt = f"""
        Task: Analyze the entity name '{original_name}'. 
        If it is not in English, translate it to its official English business name.
        If it is already in English, return it exactly as is.
        Output ONLY the final English name.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            raw_text = response.choices[0].message.content.strip()
            
            # --- SANITIZATION LAYER ---
            # 1. Remove Markdown bold/italic (* or _)
            clean_text = raw_text.replace("*", "").replace("_", "")
            
            # 2. Remove Quotes (" or ')
            clean_text = clean_text.replace('"', '').replace("'", "")
            
            # 3. Remove trailing punctuation (periods)
            clean_text = clean_text.rstrip(".")
            
            # 4. Handle "Translation: Name" format hallucinations
            if ":" in clean_text:
                clean_text = clean_text.split(":")[-1].strip()
                
            return clean_text
            
        except Exception as e:
            print(f"Translation Error: {e}")
            return original_name

    def export_report_to_pdf(self, entity_name, report_text):
        """
        Converts the Markdown report text to a simple PDF.
        """
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # --- FIX STARTS HERE ---
        # 1. Sanitize the Entity Name for the Title (This was causing the crash)
        safe_title_name = entity_name.encode('latin-1', 'replace').decode('latin-1')

        # Title
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, f"Due Diligence Report: {safe_title_name}", ln=True, align="C")
        # --- FIX ENDS HERE ---

        pdf.ln(10)

        # Content - Clean markdown for plain text PDF
        pdf.set_font("Arial", size=11)

        clean_text = report_text.replace("**", "").replace("### ", "").replace("## ", "").replace("`", "")

        for line in clean_text.split('\n'):
            # Replace unsupported characters (simple fallback)
            encoded_line = line.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 6, encoded_line)

        return pdf.output(dest='S').encode('latin-1')

    def search_sec_edgar_cik(self, company_name):
        """
        Search SEC EDGAR for a company's CIK (Central Index Key).
        Uses two methods:
        1. company_tickers.json (fast, but limited to ticker symbols)
        2. SEC EDGAR full-text search (slower, but comprehensive)

        Args:
            company_name (str): Company name to search

        Returns:
            str or None: CIK number if found, None otherwise
        """
        # Method 1: Try company_tickers.json first (fast)
        cik = self._search_cik_from_tickers(company_name)
        if cik:
            return cik

        # Method 2: Fallback to SEC EDGAR full-text search (comprehensive)
        self._log(f"Company not found in tickers file, trying SEC EDGAR search...", "INFO")
        cik = self._search_cik_from_edgar(company_name)
        return cik

    def _search_cik_from_tickers(self, company_name):
        """
        Search for CIK using SEC's company_tickers.json file.
        Fast but limited to companies with ticker symbols.

        Args:
            company_name (str): Company name to search

        Returns:
            str or None: CIK number if found, None otherwise
        """
        try:
            time.sleep(0.1)  # Rate limit: max 10 requests/second

            url = "https://www.sec.gov/files/company_tickers.json"
            response = requests.get(url, headers=self.sec_headers, timeout=10)
            response.raise_for_status()

            companies = response.json()

            # Search for company by name (case-insensitive)
            company_lower = company_name.lower()
            best_match = None
            best_match_score = 0

            for company_data in companies.values():
                company_title = company_data.get('title', '').lower()

                # Exact match
                if company_lower == company_title:
                    cik = str(company_data.get('cik_str')).zfill(10)
                    self._log(f"Found exact match - CIK: {cik} for {company_data.get('title')}", "SUCCESS")
                    return cik

                # Partial match (company name contains or is contained in title)
                if company_lower in company_title or company_title in company_lower:
                    # Score by length of match
                    score = len(company_lower) if company_lower in company_title else len(company_title)
                    if score > best_match_score:
                        best_match_score = score
                        best_match = company_data

            if best_match:
                cik = str(best_match.get('cik_str')).zfill(10)
                self._log(f"Found CIK: {cik} for {best_match.get('title')}", "SUCCESS")
                return cik

            return None

        except Exception as e:
            self._log(f"Error searching company_tickers.json: {e}", "ERROR")
            return None

    def _search_cik_from_edgar(self, company_name):
        """
        Search for CIK using SEC EDGAR's full-text search.
        More comprehensive but slower than tickers file.
        This method works for all companies registered with SEC, including foreign issuers.

        Args:
            company_name (str): Company name to search

        Returns:
            str or None: CIK number if found, None otherwise
        """
        try:
            time.sleep(0.2)  # Rate limiting

            # Use SEC's EDGAR company search
            # This searches across ALL SEC registrants, not just ticker symbols
            import urllib.parse
            encoded_name = urllib.parse.quote(company_name)
            search_url = f"https://www.sec.gov/cgi-bin/browse-edgar?company={encoded_name}&owner=exclude&action=getcompany"

            self._log(f"Searching SEC EDGAR for '{company_name}'...", "INFO")
            response = requests.get(search_url, headers=self.sec_headers, timeout=15)
            response.raise_for_status()

            html_content = response.text

            # Parse the HTML to find CIK
            import re
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html_content, 'html.parser')

            # Look for CIK in the page
            # Format: "CIK: 0001577552" or in meta tags
            cik_match = re.search(r'CIK=(\d{10})', html_content)
            if not cik_match:
                cik_match = re.search(r'CIK:\s*(\d{1,10})', html_content)

            if cik_match:
                cik = cik_match.group(1).zfill(10)  # Ensure 10 digits with leading zeros

                # Try to extract company name from the page for confirmation
                company_info = soup.find('span', {'class': 'companyName'})
                if company_info:
                    found_name = company_info.get_text().strip()
                    # Remove CIK from the name if present
                    found_name = re.sub(r'CIK#:\s*\d+', '', found_name).strip()
                    self._log(f"Found CIK: {cik} for '{found_name}'", "SUCCESS")
                else:
                    self._log(f"Found CIK: {cik}", "SUCCESS")

                return cik

            self._log(f"No CIK found for '{company_name}' in SEC EDGAR", "WARN")
            return None

        except Exception as e:
            self._log(f"Error searching SEC EDGAR: {e}", "ERROR")
            return None

    def _search_sec_filing_by_type(self, cik, filing_type):
        """
        Helper function to search for a specific SEC filing type.

        Args:
            cik (str): Company's CIK number (10 digits with leading zeros)
            filing_type (str): Filing type to search for ('10-K' or '20-F')

        Returns:
            dict or None: Filing data with accession number and filing URL
        """
        try:
            # Rate limit - SEC recommends max 10 requests/second
            time.sleep(0.2)  # Increased from 0.1 to be more conservative

            # Remove leading zeros for CIK integer
            cik_int = str(int(cik))

            # Search for filings using SEC EDGAR full-text search
            search_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik_int}&type={filing_type}&dateb=&owner=exclude&count=10&search_text="

            self._log(f"Searching for {filing_type} filings...", "INFO")

            # Retry logic for 503 errors (rate limiting / server overload)
            max_retries = 3
            retry_delay = 2  # Start with 2 seconds

            for attempt in range(max_retries):
                try:
                    response = requests.get(search_url, headers=self.sec_headers, timeout=15)
                    response.raise_for_status()
                    html_content = response.text
                    break  # Success - exit retry loop

                except requests.exceptions.HTTPError as e:
                    if response.status_code == 503 and attempt < max_retries - 1:
                        # 503 Service Unavailable - retry with exponential backoff
                        self._log(f"SEC server unavailable (503), retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})", "WARN")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        # Other error or max retries reached
                        raise
            else:
                # This should not be reached, but just in case
                raise Exception(f"Failed to fetch {filing_type} filing after {max_retries} attempts")

            # Parse HTML to find filings
            import re

            # Look for document viewer links in the format:
            # /cgi-bin/viewer?action=view&cik=XXXXX&accession_number=XXXXXXXXXX-XX-XXXXXX&xbrl_type=v
            pattern = r'documentsbutton.*?href="([^"]+)"'
            doc_matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)

            if not doc_matches:
                self._log(f"No {filing_type} filings found for CIK {cik}", "WARN")
                return None

            # Get the first (most recent) filing
            first_link = doc_matches[0]

            # Extract accession number from the link
            # Format: accession_number=0000320193-25-000079
            acc_pattern = r'accession_number=(\d+-\d+-\d+)'
            acc_match = re.search(acc_pattern, first_link)

            if not acc_match:
                self._log(f"Could not extract accession number", "ERROR")
                return None

            accession_with_hyphens = acc_match.group(1)
            accession_no_hyphens = accession_with_hyphens.replace('-', '')

            # Also extract the filing date (look for the date in the row)
            date_pattern = r'<td.*?>(\d{4}-\d{2}-\d{2})</td>'
            date_matches = re.findall(date_pattern, html_content)
            filing_date = date_matches[0] if date_matches else "Unknown"

            self._log(f"Found {filing_type} filing from {filing_date}", "SUCCESS")

            return {
                'accession': accession_no_hyphens,
                'accession_formatted': accession_with_hyphens,
                'filing_date': filing_date,
                'cik': cik,
                'filing_type': filing_type
            }

        except Exception as e:
            self._log(f"Error getting {filing_type} filing: {e}", "ERROR")
            return None

    def get_latest_sec_filing(self, cik):
        """
        Get the latest SEC filing for a company (10-K for US companies, 20-F for foreign issuers).

        Args:
            cik (str): Company's CIK number (10 digits with leading zeros)

        Returns:
            dict or None: Filing data with accession number, filing URL, and filing_type
        """
        # Try 10-K first (US domestic companies)
        filing = self._search_sec_filing_by_type(cik, '10-K')
        if filing:
            return filing

        # Try 20-F (foreign private issuers)
        self._log("No 10-K found, trying 20-F (foreign issuer)...", "INFO")
        filing = self._search_sec_filing_by_type(cik, '20-F')
        if filing:
            return filing

        return None

    def extract_subsidiaries_from_sec_filing(self, filing_data):
        """
        Extract subsidiaries from SEC filing (Exhibit 21 for 10-K, Exhibit 8.1 for 20-F).

        Args:
            filing_data (dict): Filing data from get_latest_sec_filing()

        Returns:
            dict: Dictionary with subsidiaries list, exhibit URL, and filing date
        """
        subsidiaries = []
        filing_type = filing_data.get('filing_type', '10-K')

        try:
            # Remove leading zeros from CIK for URL
            cik = filing_data['cik']
            cik_int = str(int(cik))
            accession = filing_data['accession']
            accession_formatted = filing_data['accession_formatted']

            # Rate limit - SEC recommends max 10 requests/second
            time.sleep(0.2)

            # Access the filing index page directly from Archives
            # Format: https://www.sec.gov/Archives/edgar/data/CIK/ACCESSION_NO_HYPHENS/ACCESSION-WITH-HYPHENS-index.htm
            index_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession}/{accession_formatted}-index.htm"
            self._log(f"Accessing filing index...", "INFO")

            response = requests.get(index_url, headers=self.sec_headers, timeout=15)

            if response.status_code != 200:
                self._log(f"Could not access filing index (status {response.status_code}), trying .html extension...", "WARN")
                # Try with .html extension
                index_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession}/{accession_formatted}-index.html"
                response = requests.get(index_url, headers=self.sec_headers, timeout=15)

                if response.status_code != 200:
                    self._log(f"Could not access filing index", "ERROR")
                    return {'subsidiaries': [], 'exhibit_url': None, 'filing_date': None}

            # Look for the appropriate exhibit based on filing type
            content = response.text
            exhibit_doc = None
            import re

            # Determine which exhibit to search for based on filing type
            if filing_type == '10-K':
                # Search for Exhibit 21 (US domestic companies)
                exhibit_patterns = [
                    r'href="([^"]*ex-?21[^"]*\.htm[l]?)"',
                    r'href="([^"]*ex-?21[^"]*)"',
                    r'href="([^"]*exhibit-?21[^"]*)"'
                ]
                exhibit_name = "Exhibit 21"
            elif filing_type == '20-F':
                # Search for Exhibit 8.1 (foreign private issuers)
                # Handles various naming conventions: ex-8.1, ex-8-1, ex8.1, ex8-1, ex8_1, etc.
                exhibit_patterns = [
                    r'href="([^"]*ex-?8[-._]1[^"]*\.htm[l]?)"',  # ex-8.1, ex-8_1, ex-8-1
                    r'href="([^"]*ex-?8[-._]1[^"]*)"',
                    r'href="([^"]*exhibit-?8[-._]1[^"]*)"',
                    r'href="([^"]*ex8[-._]1[^"]*\.htm[l]?)"',  # ex8.1, ex8_1, ex8-1
                    r'href="([^"]*ex8[-._]1[^"]*)"'
                ]
                exhibit_name = "Exhibit 8.1"
            else:
                self._log(f"Unknown filing type: {filing_type}", "ERROR")
                return {'subsidiaries': [], 'exhibit_url': None, 'filing_date': None}

            for pattern in exhibit_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    exhibit_doc = match.group(1)
                    break

            if not exhibit_doc:
                self._log(f"Could not find {exhibit_name} in filing", "WARN")
                return {'subsidiaries': [], 'exhibit_url': None, 'filing_date': None}

            # Fetch exhibit document
            if exhibit_doc.startswith('http'):
                exhibit_url = exhibit_doc
            else:
                exhibit_url = f"https://www.sec.gov{exhibit_doc}" if exhibit_doc.startswith('/') else f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession}/{exhibit_doc}"

            self._log(f"Found {exhibit_name}, downloading document...", "SUCCESS")

            time.sleep(0.2)  # Rate limit
            exhibit_response = requests.get(exhibit_url, headers=self.sec_headers, timeout=15)
            exhibit_response.raise_for_status()

            exhibit_text = exhibit_response.text

            # Strip HTML tags to get cleaner text for LLM
            # Remove HTML tags but keep the text content
            text_only = re.sub(r'<[^>]+>', ' ', exhibit_text)
            # Remove extra whitespace
            text_only = re.sub(r'\s+', ' ', text_only)
            # Remove common HTML entities
            text_only = text_only.replace('&nbsp;', ' ').replace('&amp;', '&')

            # For very long documents, we'll process in chunks
            # Most exhibits have 50-500 subsidiaries
            max_chars = 50000  # Increased from 8000 to handle large companies
            text_chunk = text_only[:max_chars]

            self._log(f"Parsing {exhibit_name} with LLM ({len(text_only)} chars)...", "INFO")

            prompt = f"""
Extract ALL subsidiary companies from this SEC {exhibit_name} document.

{exhibit_name} lists subsidiaries of a company. Extract each subsidiary with:
- Company name (full legal name)
- Jurisdiction of incorporation (state/country)
- Ownership percentage (if mentioned, otherwise use "Unknown")

IMPORTANT: This may be a long list. Extract EVERY subsidiary mentioned, even if there are hundreds.

{"Note: For 10-K filings, subsidiaries are in Exhibit 21. For 20-F filings (foreign issuers), they are in Exhibit 8.1. The format is similar." if filing_type == '20-F' else ""}

Document content:
{text_chunk}

Output format (one per line):
COMPANY_NAME | JURISDICTION | OWNERSHIP_PERCENTAGE

Example (format only - these are NOT real companies):
XYZ Holdings, LLC | Delaware | 100
ABC International | Ireland | Unknown
Tech Japan Inc. | Japan | 51.5

If no clear subsidiaries are listed, respond with "NO_SUBSIDIARIES_FOUND".
Extract ALL entities listed as subsidiaries. Continue until you've extracted everything.
"""

            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=8000  # Increased from 2000 to handle many subsidiaries
            )

            content = response.choices[0].message.content.strip()

            if "NO_SUBSIDIARIES_FOUND" in content:
                self._log(f"No subsidiaries found in {exhibit_name}", "WARN")
                return {'subsidiaries': [], 'exhibit_url': None, 'filing_date': None}

            # Parse LLM response
            for line in content.split('\n'):
                line = line.strip()
                if not line or '|' not in line:
                    continue

                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 2:
                    # Parse ownership percentage if provided
                    ownership_pct = None
                    if len(parts) >= 3:
                        ownership_str = parts[2].lower()
                        if ownership_str != 'unknown' and ownership_str != '':
                            try:
                                # Remove % sign if present and convert to float
                                ownership_pct = float(ownership_str.replace('%', '').strip())
                            except ValueError:
                                pass  # Keep as None if can't parse

                    subsidiaries.append({
                        'name': parts[0],
                        'jurisdiction': parts[1],
                        'status': 'Active',
                        'relationship': 'subsidiary',
                        'level': 1,
                        'source': 'sec_edgar',
                        'ownership_percentage': ownership_pct
                    })

            self._log(f"Extracted {len(subsidiaries)} subsidiaries from {exhibit_name}", "SUCCESS")

            # Return both subsidiaries and the source URL
            return {
                'subsidiaries': subsidiaries,
                'exhibit_url': exhibit_url,
                'filing_date': filing_data.get('filing_date', 'Unknown'),
                'filing_type': filing_type
            }

        except Exception as e:
            self._log(f"Error extracting subsidiaries: {e}", "ERROR")
            return {'subsidiaries': [], 'exhibit_url': None, 'filing_date': None, 'filing_type': filing_type}

    def find_subsidiaries_sec_edgar(self, company_name):
        """
        Find subsidiaries and financial intelligence using SEC EDGAR filings.
        For US companies: extracts from 10-K + DEF 14A
        For foreign issuers: extracts from 20-F

        Args:
            company_name (str): Company name to search

        Returns:
            dict: {
                'subsidiaries': [list of subsidiary dicts],
                'sisters': [],  # SEC doesn't provide sister companies
                'parent': None,
                'method': 'sec_edgar_10k' or 'sec_edgar_20f',
                'directors': [list of director dicts],
                'shareholders': [list of shareholder dicts],
                'transactions': [list of transaction dicts]
            }
        """
        print(f"[SEC EDGAR] Searching for {company_name}...")

        # Step 1: Find CIK
        cik = self.search_sec_edgar_cik(company_name)
        if not cik:
            return {
                'subsidiaries': [], 'sisters': [], 'parent': None, 'method': 'none',
                'source_url': None, 'filing_date': None,
                'directors': [], 'shareholders': [], 'transactions': []
            }

        # Step 2: Get latest SEC filing (tries 10-K first, then 20-F)
        filing_data = self.get_latest_sec_filing(cik)
        if not filing_data:
            return {
                'subsidiaries': [], 'sisters': [], 'parent': None, 'method': 'none',
                'source_url': None, 'filing_date': None,
                'directors': [], 'shareholders': [], 'transactions': []
            }

        # Step 3: Extract subsidiaries from appropriate exhibit
        extraction_result = self.extract_subsidiaries_from_sec_filing(filing_data)

        subsidiaries = extraction_result.get('subsidiaries', [])
        exhibit_url = extraction_result.get('exhibit_url')
        filing_date = extraction_result.get('filing_date')
        filing_type = extraction_result.get('filing_type', '10-K')

        # Step 4: Extract financial intelligence
        directors = []
        shareholders = []
        transactions = []
        fin_intel_url = None

        if filing_type == '20-F':
            # For foreign issuers, extract from 20-F Items 6 & 7
            self._log("Extracting financial intelligence from 20-F (Items 6 & 7)...", "INFO")
            fin_intel = self.extract_financial_intelligence_from_20f(filing_data)
            directors = fin_intel.get('directors', [])
            shareholders = fin_intel.get('shareholders', [])
            transactions = fin_intel.get('transactions', [])
            fin_intel_url = fin_intel.get('source_url')

        elif filing_type == '10-K':
            # For US companies, extract from proxy statement (DEF 14A)
            self._log("Searching for proxy statement (DEF 14A) for financial intelligence...", "INFO")
            proxy_data = self.get_latest_proxy_statement(cik)
            if proxy_data:
                self._log("Found proxy statement, extracting financial intelligence...", "INFO")
                fin_intel = self.extract_financial_intelligence_from_proxy(proxy_data)
                directors = fin_intel.get('directors', [])
                shareholders = fin_intel.get('shareholders', [])
                transactions = fin_intel.get('transactions', [])
                fin_intel_url = fin_intel.get('source_url')
            else:
                self._log("No proxy statement found", "WARN")

        # Step 5: Extract loan agreements from Exhibits 4.3 and 4.5
        loan_agreements = []
        loan_source_urls = []

        self._log("Extracting loan agreements from Exhibits 4.3 and 4.5...", "INFO")
        loan_result = self.extract_loan_agreements_from_sec_filing(filing_data)
        loan_agreements = loan_result.get('loan_agreements', [])
        loan_source_urls = loan_result.get('source_urls', [])

        # Save loan agreements to database
        if loan_agreements:
            import database as db
            count = db.insert_loan_agreements(
                company_name=company_name,
                cik=cik,
                loan_agreements_list=loan_agreements,
                filing_type=filing_type,
                filing_date=filing_date,
                source_url=exhibit_url if exhibit_url else ''
            )
            self._log(f"Saved {count} loan agreements to database", "SUCCESS")

        if not subsidiaries:
            return {
                'subsidiaries': [], 'sisters': [], 'parent': None, 'method': 'none',
                'source_url': None, 'filing_date': None,
                'directors': directors, 'shareholders': shareholders, 'transactions': transactions,
                'loan_agreements': loan_agreements, 'loan_source_urls': loan_source_urls
            }

        # Set method based on filing type
        method = 'sec_edgar_10k' if filing_type == '10-K' else 'sec_edgar_20f'

        return {
            'subsidiaries': subsidiaries,
            'sisters': [],  # SEC EDGAR doesn't provide sister companies
            'parent': None,
            'method': method,
            'source_url': exhibit_url,
            'filing_date': filing_date,
            'directors': directors,
            'shareholders': shareholders,
            'transactions': transactions,
            'loan_agreements': loan_agreements,
            'loan_source_urls': loan_source_urls,
            'fin_intel_url': fin_intel_url,
            'cik': cik,
            'company_name': company_name
        }

    def get_latest_proxy_statement(self, cik):
        """
        Get the latest DEF 14A (proxy statement) for a US company.

        Args:
            cik (str): Company's CIK number

        Returns:
            dict or None: Proxy filing data
        """
        filing = self._search_sec_filing_by_type(cik, 'DEF 14A')
        return filing

    def extract_financial_intelligence_from_20f(self, filing_data):
        """
        Extract directors, shareholders, and related party transactions from 20-F filing.

        Args:
            filing_data (dict): Filing data from get_latest_sec_filing()

        Returns:
            dict: {
                'directors': [...],
                'shareholders': [...],
                'transactions': [...]
            }
        """
        try:
            cik = filing_data['cik']
            cik_int = str(int(cik))
            accession = filing_data['accession']
            accession_formatted = filing_data['accession_formatted']

            # Rate limit
            time.sleep(0.1)

            # Get the main 20-F document (not exhibits)
            index_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession}/{accession_formatted}-index.htm"
            self._log(f"Accessing 20-F filing for financial intelligence...", "INFO")

            response = requests.get(index_url, headers=self.sec_headers, timeout=15)
            if response.status_code != 200:
                index_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession}/{accession_formatted}-index.html"
                response = requests.get(index_url, headers=self.sec_headers, timeout=15)

            content = response.text

            # Find the main 20-F document (usually the first .htm file)
            import re
            # Look for the main document (20-F)
            doc_pattern = r'href="([^"]*20f[^"]*\.htm[l]?)"'
            match = re.search(doc_pattern, content, re.IGNORECASE)

            if not match:
                # Try alternative pattern - just first htm file
                doc_pattern = r'href="([^"]*\.htm[l]?)"'
                matches = re.findall(doc_pattern, content, re.IGNORECASE)
                if matches:
                    main_doc = matches[0]
                else:
                    self._log("Could not find main 20-F document", "WARN")
                    return {'directors': [], 'shareholders': [], 'transactions': []}
            else:
                main_doc = match.group(1)

            # Fetch main 20-F document
            if main_doc.startswith('http'):
                doc_url = main_doc
            else:
                doc_url = f"https://www.sec.gov{main_doc}" if main_doc.startswith('/') else f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession}/{main_doc}"

            self._log(f"Downloading 20-F document for Items 6 & 7...", "INFO")
            time.sleep(0.1)
            doc_response = requests.get(doc_url, headers=self.sec_headers, timeout=30)
            doc_response.raise_for_status()

            doc_text = doc_response.text

            # Strip HTML
            text_only = re.sub(r'<[^>]+>', ' ', doc_text)
            text_only = re.sub(r'\s+', ' ', text_only)
            text_only = text_only.replace('&nbsp;', ' ').replace('&amp;', '&')

            # Extract sections (Items 6 and 7 are usually in specific sections)
            # We'll use LLM to find and extract this information

            self._log(f"Extracting Item 6 (Directors) and Item 7 (Shareholders/Transactions) with LLM...", "INFO")

            # Limit text size for LLM
            max_chars = 100000
            text_chunk = text_only[:max_chars]

            prompt = f"""
Extract financial intelligence from this 20-F filing. Find and extract ONLY real, verifiable information from the document.

CRITICAL RULES:
1. Extract ONLY information that is explicitly stated in the document
2. DO NOT generate placeholder names like "John Doe", "Jane Smith", or any example names
3. DO NOT use "Unknown", "N/A", "None", or "blank" as values - just skip that entry
4. If you cannot find real data for a section, respond with "NONE" for that section
5. DO NOT make up or infer information that is not explicitly stated

Extract the following:

1. **Item 6: Directors, Senior Management and Employees**
   - Names of directors and officers (REAL NAMES ONLY from the document)
   - Their titles/positions
   - Nationality (only if explicitly mentioned)
   - Other board positions (only if explicitly mentioned)

2. **Item 7A: Major Shareholders**
   - Names of major shareholders with 5%+ ownership (REAL NAMES ONLY)
   - Type (Individual/Corporate/Institutional/Government)
   - Ownership percentage (must be a number)
   - Jurisdiction/country (only if mentioned)

3. **Item 7B: Related Party Transactions**
   - Transaction type (Loan, Sale, Purchase, Guarantee, etc.)
   - Counterparty name (REAL NAME ONLY)
   - Relationship to company
   - Amount and currency (must be actual numbers, not "unknown")
   - Transaction date (if mentioned)
   - Purpose (if mentioned)

Document excerpt:
{text_chunk}

Output format (use three sections with headers):

===DIRECTORS===
NAME | TITLE | NATIONALITY | OTHER_POSITIONS
(one per line, REAL NAMES ONLY - no "John Doe", "Jane Smith", etc.)

===SHAREHOLDERS===
NAME | TYPE | OWNERSHIP_PERCENTAGE | JURISDICTION
(one per line, REAL NAMES ONLY - percentage must be a number)

===TRANSACTIONS===
TRANSACTION_TYPE | COUNTERPARTY | RELATIONSHIP | AMOUNT | CURRENCY | DATE | PURPOSE
(one per line, REAL NAMES ONLY - amount must be a number)

IMPORTANT:
- If you cannot find any real directors, write "NONE" under ===DIRECTORS===
- If you cannot find any real shareholders, write "NONE" under ===SHAREHOLDERS===
- If you cannot find any real transactions, write "NONE" under ===TRANSACTIONS===
- DO NOT generate example or placeholder data
- BE CONSERVATIVE - only extract information explicitly stated in the document
"""

            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=8000
            )

            content_response = response.choices[0].message.content.strip()

            # Parse the structured response
            directors = []
            shareholders = []
            transactions = []

            current_section = None
            for line in content_response.split('\n'):
                line = line.strip()
                if line.startswith('===DIRECTORS==='):
                    current_section = 'directors'
                    continue
                elif line.startswith('===SHAREHOLDERS==='):
                    current_section = 'shareholders'
                    continue
                elif line.startswith('===TRANSACTIONS==='):
                    current_section = 'transactions'
                    continue

                if not line or line == 'NONE' or not '|' in line:
                    continue

                parts = [p.strip() for p in line.split('|')]

                if current_section == 'directors' and len(parts) >= 2:
                    # Validate director name
                    if self._validate_person_name(parts[0]):
                        directors.append({
                            'name': parts[0],
                            'title': parts[1] if len(parts) > 1 else 'Unknown',
                            'nationality': parts[2] if len(parts) > 2 and parts[2].lower() not in ['unknown', 'n/a', 'none'] else 'Unknown',
                            'other_positions': parts[3] if len(parts) > 3 else ''
                        })
                    else:
                        self._log(f"Filtered out invalid director name: '{parts[0]}'", "INFO")

                elif current_section == 'shareholders' and len(parts) >= 2:
                    # Validate shareholder name
                    if not self._validate_person_name(parts[0]) and not self._validate_company_name(parts[0]):
                        self._log(f"Filtered out invalid shareholder name: '{parts[0]}'", "INFO")
                        continue

                    ownership = None
                    if len(parts) > 2 and parts[2].lower() not in ['unknown', 'n/a', 'none']:
                        try:
                            ownership = float(parts[2].replace('%', '').strip())
                        except ValueError:
                            pass

                    # Only add if we have valid ownership percentage
                    if ownership is not None:
                        shareholders.append({
                            'name': parts[0],
                            'type': parts[1] if len(parts) > 1 else 'Unknown',
                            'ownership_percentage': ownership,
                            'jurisdiction': parts[3] if len(parts) > 3 and parts[3].lower() not in ['unknown', 'n/a', 'none'] else 'Unknown'
                        })
                    else:
                        self._log(f"Skipped shareholder without valid ownership: '{parts[0]}'", "INFO")

                elif current_section == 'transactions' and len(parts) >= 2:
                    # Validate counterparty name
                    if not self._validate_person_name(parts[1]) and not self._validate_company_name(parts[1]):
                        self._log(f"Filtered out invalid counterparty name: '{parts[1]}'", "INFO")
                        continue

                    amount = None
                    if len(parts) > 3 and parts[3].lower() not in ['unknown', 'n/a', 'none']:
                        try:
                            amount = float(parts[3].replace(',', '').strip())
                        except ValueError:
                            pass

                    # Only add if we have a valid amount
                    if amount is not None:
                        transactions.append({
                            'transaction_type': parts[0],
                            'counterparty': parts[1],
                            'relationship': parts[2] if len(parts) > 2 else 'Unknown',
                            'amount': amount,
                            'currency': parts[4] if len(parts) > 4 else 'USD',
                            'transaction_date': parts[5] if len(parts) > 5 and parts[5].lower() not in ['unknown', 'n/a', 'none'] else 'Unknown',
                            'purpose': parts[6] if len(parts) > 6 else ''
                        })
                    else:
                        self._log(f"Skipped transaction without valid amount: '{parts[1]}'", "INFO")

            self._log(f"Extracted {len(directors)} directors, {len(shareholders)} shareholders, {len(transactions)} transactions", "SUCCESS")

            return {
                'directors': directors,
                'shareholders': shareholders,
                'transactions': transactions,
                'source_url': doc_url
            }

        except Exception as e:
            self._log(f"Error extracting financial intelligence from 20-F: {e}", "ERROR")
            return {'directors': [], 'shareholders': [], 'transactions': [], 'source_url': None}

    def extract_financial_intelligence_from_proxy(self, proxy_data):
        """
        Extract directors, shareholders, and related party transactions from DEF 14A (proxy statement).

        Args:
            proxy_data (dict): Proxy filing data from get_latest_proxy_statement()

        Returns:
            dict: {
                'directors': [...],
                'shareholders': [...],
                'transactions': [...]
            }
        """
        try:
            cik = proxy_data['cik']
            cik_int = str(int(cik))
            accession = proxy_data['accession']
            accession_formatted = proxy_data['accession_formatted']

            # Rate limit
            time.sleep(0.1)

            # Get the proxy statement index
            index_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession}/{accession_formatted}-index.htm"
            self._log(f"Accessing DEF 14A (proxy statement) for financial intelligence...", "INFO")

            response = requests.get(index_url, headers=self.sec_headers, timeout=15)
            if response.status_code != 200:
                index_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession}/{accession_formatted}-index.html"
                response = requests.get(index_url, headers=self.sec_headers, timeout=15)

            content = response.text

            # Find the main proxy document
            import re
            doc_pattern = r'href="([^"]*def[^"]*\.htm[l]?)"'
            match = re.search(doc_pattern, content, re.IGNORECASE)

            if not match:
                # Try alternative - first htm file
                doc_pattern = r'href="([^"]*\.htm[l]?)"'
                matches = re.findall(doc_pattern, content, re.IGNORECASE)
                if matches:
                    main_doc = matches[0]
                else:
                    self._log("Could not find main proxy document", "WARN")
                    return {'directors': [], 'shareholders': [], 'transactions': []}
            else:
                main_doc = match.group(1)

            # Fetch main proxy document
            if main_doc.startswith('http'):
                doc_url = main_doc
            else:
                doc_url = f"https://www.sec.gov{main_doc}" if main_doc.startswith('/') else f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession}/{main_doc}"

            self._log(f"Downloading proxy statement...", "INFO")
            time.sleep(0.1)
            doc_response = requests.get(doc_url, headers=self.sec_headers, timeout=30)
            doc_response.raise_for_status()

            doc_text = doc_response.text

            # Strip HTML
            text_only = re.sub(r'<[^>]+>', ' ', doc_text)
            text_only = re.sub(r'\s+', ' ', text_only)
            text_only = text_only.replace('&nbsp;', ' ').replace('&amp;', '&')

            self._log(f"Extracting directors, shareholders, and transactions with LLM...", "INFO")

            # Limit text size
            max_chars = 100000
            text_chunk = text_only[:max_chars]

            prompt = f"""
Extract financial intelligence from this DEF 14A (proxy statement). Find and extract ONLY real, verifiable information.

CRITICAL RULES:
1. Extract ONLY information explicitly stated in the document
2. DO NOT generate placeholder names like "John Doe", "Jane Smith", or any example names
3. DO NOT use "Unknown", "N/A", "None", or "blank" as values - just skip that entry
4. If you cannot find real data for a section, respond with "NONE" for that section
5. DO NOT make up or infer information

Extract the following:

1. **Directors and Executive Officers**
   - Names of directors and officers (REAL NAMES ONLY)
   - Their titles/positions
   - Other board positions (only if mentioned)

2. **Security Ownership of Certain Beneficial Owners and Management (5%+ shareholders)**
   - Names of major shareholders (REAL NAMES ONLY)
   - Type (Individual/Corporate/Institutional)
   - Ownership percentage (must be a number)
   - Jurisdiction/country (only if mentioned)

3. **Related Person Transactions**
   - Transaction type (Loan, Sale, Purchase, Guarantee, etc.)
   - Counterparty name (REAL NAME ONLY)
   - Relationship to company
   - Amount and currency (must be actual numbers)
   - Purpose (if mentioned)

Document excerpt:
{text_chunk}

Output format (use three sections with headers):

===DIRECTORS===
NAME | TITLE | OTHER_POSITIONS
(one per line, REAL NAMES ONLY - no placeholders)

===SHAREHOLDERS===
NAME | TYPE | OWNERSHIP_PERCENTAGE | JURISDICTION
(one per line, REAL NAMES ONLY - percentage must be a number)

===TRANSACTIONS===
TRANSACTION_TYPE | COUNTERPARTY | RELATIONSHIP | AMOUNT | CURRENCY | PURPOSE
(one per line, REAL NAMES ONLY - amount must be a number)

IMPORTANT:
- If you cannot find any real directors, write "NONE" under ===DIRECTORS===
- If you cannot find any real shareholders, write "NONE" under ===SHAREHOLDERS===
- If you cannot find any real transactions, write "NONE" under ===TRANSACTIONS===
- DO NOT generate example or placeholder data
- BE CONSERVATIVE - only extract information explicitly stated in the document
"""

            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=8000
            )

            content_response = response.choices[0].message.content.strip()

            # Parse the structured response
            directors = []
            shareholders = []
            transactions = []

            current_section = None
            for line in content_response.split('\n'):
                line = line.strip()
                if line.startswith('===DIRECTORS==='):
                    current_section = 'directors'
                    continue
                elif line.startswith('===SHAREHOLDERS==='):
                    current_section = 'shareholders'
                    continue
                elif line.startswith('===TRANSACTIONS==='):
                    current_section = 'transactions'
                    continue

                if not line or line == 'NONE' or not '|' in line:
                    continue

                parts = [p.strip() for p in line.split('|')]

                if current_section == 'directors' and len(parts) >= 2:
                    # Validate director name
                    if self._validate_person_name(parts[0]):
                        directors.append({
                            'name': parts[0],
                            'title': parts[1] if len(parts) > 1 else 'Unknown',
                            'nationality': 'United States',  # Assume US for DEF 14A
                            'other_positions': parts[2] if len(parts) > 2 else ''
                        })
                    else:
                        self._log(f"Filtered out invalid director name: '{parts[0]}'", "INFO")

                elif current_section == 'shareholders' and len(parts) >= 2:
                    # Validate shareholder name
                    if not self._validate_person_name(parts[0]) and not self._validate_company_name(parts[0]):
                        self._log(f"Filtered out invalid shareholder name: '{parts[0]}'", "INFO")
                        continue

                    ownership = None
                    if len(parts) > 2 and parts[2].lower() not in ['unknown', 'n/a', 'none']:
                        try:
                            ownership = float(parts[2].replace('%', '').strip())
                        except ValueError:
                            pass

                    # Only add if we have valid ownership percentage
                    if ownership is not None:
                        shareholders.append({
                            'name': parts[0],
                            'type': parts[1] if len(parts) > 1 else 'Unknown',
                            'ownership_percentage': ownership,
                            'jurisdiction': parts[3] if len(parts) > 3 and parts[3].lower() not in ['unknown', 'n/a', 'none'] else 'United States'
                        })
                    else:
                        self._log(f"Skipped shareholder without valid ownership: '{parts[0]}'", "INFO")

                elif current_section == 'transactions' and len(parts) >= 2:
                    # Validate counterparty name
                    if not self._validate_person_name(parts[1]) and not self._validate_company_name(parts[1]):
                        self._log(f"Filtered out invalid counterparty name: '{parts[1]}'", "INFO")
                        continue

                    amount = None
                    if len(parts) > 3 and parts[3].lower() not in ['unknown', 'n/a', 'none']:
                        try:
                            amount = float(parts[3].replace(',', '').strip())
                        except ValueError:
                            pass

                    # Only add if we have a valid amount
                    if amount is not None:
                        transactions.append({
                            'transaction_type': parts[0],
                            'counterparty': parts[1],
                            'relationship': parts[2] if len(parts) > 2 else 'Unknown',
                            'amount': amount,
                            'currency': parts[4] if len(parts) > 4 else 'USD',
                            'transaction_date': 'Unknown',
                            'purpose': parts[5] if len(parts) > 5 else ''
                        })
                    else:
                        self._log(f"Skipped transaction without valid amount: '{parts[1]}'", "INFO")

            self._log(f"Extracted {len(directors)} directors, {len(shareholders)} shareholders, {len(transactions)} transactions", "SUCCESS")

            return {
                'directors': directors,
                'shareholders': shareholders,
                'transactions': transactions,
                'source_url': doc_url
            }

        except Exception as e:
            self._log(f"Error extracting financial intelligence from proxy: {e}", "ERROR")
            return {'directors': [], 'shareholders': [], 'transactions': [], 'source_url': None}

    def extract_loan_agreements_from_sec_filing(self, filing_data):
        """
        Extract loan agreements from SEC filing Exhibits 4.3 and 4.5.

        Exhibit 4.3: Credit agreements, revolving facilities, term loans
        Exhibit 4.5: Indentures, notes, debt instruments

        Args:
            filing_data (dict): Filing metadata with CIK, accession, filing_type

        Returns:
            dict: {
                'loan_agreements': [list of loan dicts],
                'source_urls': [list of exhibit URL dicts],
                'filing_type': str
            }
        """
        try:
            cik = filing_data['cik']
            accession = filing_data['accession']
            filing_type = filing_data['filing_type']

            self._log(f"Extracting loan agreements from Exhibits 4.3 and 4.5...", "INFO")

            # Construct URL to filing index - handle both with and without dashes
            accession_clean = accession.replace('-', '')

            # Try to fetch the filing index page
            index_url = f"https://www.sec.gov/cgi-bin/viewer?action=view&cik={cik}&accession_number={accession}&xbrl_type=v"

            time.sleep(0.1)
            response = requests.get(index_url, headers=self.sec_headers, timeout=15)
            response.raise_for_status()
            index_html = response.text

            # Look for Exhibit 4.3 and 4.5 URLs
            exhibit_patterns = [
                (r'href="([^"]*ex-?4[-._]3[^"]*\.htm[l]?)"', '4.3', 'Credit Agreement'),
                (r'href="([^"]*ex-?4[-._]5[^"]*\.htm[l]?)"', '4.5', 'Indenture/Note')
            ]

            all_loan_agreements = []
            exhibit_urls = []

            for pattern, exhibit_num, exhibit_desc in exhibit_patterns:
                matches = re.findall(pattern, index_html, re.IGNORECASE)

                if matches:
                    # Get first match
                    relative_url = matches[0]

                    # Construct full URL
                    if relative_url.startswith('http'):
                        exhibit_url = relative_url
                    else:
                        # Build full URL from CIK and accession
                        exhibit_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{relative_url.lstrip('/')}"

                    self._log(f"Found Exhibit {exhibit_num} ({exhibit_desc}): {exhibit_url}", "SUCCESS")

                    # Fetch exhibit HTML
                    time.sleep(0.1)
                    exhibit_response = requests.get(exhibit_url, headers=self.sec_headers, timeout=15)
                    exhibit_response.raise_for_status()
                    exhibit_html = exhibit_response.text

                    # Strip HTML tags
                    clean_text = re.sub(r'<[^>]+>', ' ', exhibit_html)
                    clean_text = re.sub(r'\s+', ' ', clean_text)
                    clean_text = clean_text.replace('&nbsp;', ' ').replace('&amp;', '&')

                    # Truncate if too long (keep first 100,000 chars to stay within token limits)
                    if len(clean_text) > 100000:
                        clean_text = clean_text[:100000] + "\n\n[DOCUMENT TRUNCATED]"
                        self._log(f"Exhibit {exhibit_num} truncated to 100K chars", "WARN")

                    # Use LLM to extract structured loan data
                    loan_agreements = self._extract_loan_data_with_llm(clean_text, exhibit_num)

                    # Add exhibit metadata to each loan
                    for loan in loan_agreements:
                        loan['exhibit_type'] = exhibit_num
                        loan['source_url'] = exhibit_url

                    all_loan_agreements.extend(loan_agreements)
                    exhibit_urls.append({'exhibit': exhibit_num, 'url': exhibit_url})

            if not all_loan_agreements:
                self._log("No loan agreements found in Exhibits 4.3 or 4.5", "WARN")
                return {
                    'loan_agreements': [],
                    'source_urls': [],
                    'filing_type': filing_type
                }

            self._log(f"Extracted {len(all_loan_agreements)} loan agreements", "SUCCESS")

            return {
                'loan_agreements': all_loan_agreements,
                'source_urls': exhibit_urls,
                'filing_type': filing_type
            }

        except Exception as e:
            self._log(f"Error extracting loan agreements: {e}", "ERROR")
            return {
                'loan_agreements': [],
                'source_urls': [],
                'filing_type': filing_type
            }

    def _extract_loan_data_with_llm(self, text_content, exhibit_type):
        """
        Use LLM to extract structured loan data from exhibit text.

        Args:
            text_content (str): Clean text from exhibit
            exhibit_type (str): '4.3' or '4.5'

        Returns:
            list: List of loan agreement dicts
        """
        try:
            prompt = f"""You are analyzing a SEC filing Exhibit {exhibit_type} document containing loan/credit agreements.

Extract ALL loan agreements, credit facilities, notes, or debt instruments mentioned in this document.

For each loan/credit agreement, extract:

1. **Lender**: The entity providing the loan/credit (bank, financial institution, parent company)
2. **Borrower**: The entity receiving the loan/credit
3. **Guarantors**: Any entities guaranteeing the loan (if mentioned)
4. **Loan Type**: Type of agreement (e.g., "Revolving Credit Facility", "Term Loan", "Senior Notes", "Convertible Notes")
5. **Principal Amount**: The loan amount with currency
6. **Currency**: Currency code (USD, EUR, etc.)
7. **Interest Rate**: Interest rate terms (e.g., "LIBOR + 2.5%", "5.75% per annum")
8. **Maturity Date**: When the loan matures or expires
9. **Effective Date**: When the agreement became effective
10. **Purpose**: Purpose of the loan (e.g., "working capital", "acquisition financing", "general corporate purposes")
11. **Covenants**: Any important covenants or conditions (as list)
12. **Security/Collateral**: Any collateral or security mentioned
13. **Prepayment Terms**: Any prepayment or early termination terms

**IMPORTANT**:
- Return a JSON array of loan objects
- If a field is not mentioned, set it to null
- Extract ALL loans mentioned in the document
- Be precise with amounts and dates
- Preserve entity names exactly as written
- For amounts, extract only the numeric value (e.g., 8000000000 not "8 billion")

Return ONLY valid JSON in this format:
[
    {{
        "lender": "Bank of America",
        "borrower": "Alibaba Group Holding Limited",
        "guarantors": ["Alibaba.com Limited", "Taobao China Holding Limited"],
        "loan_type": "Revolving Credit Facility",
        "principal_amount": 8000000000,
        "currency": "USD",
        "interest_rate": "LIBOR + 1.75%",
        "maturity_date": "2027-07-28",
        "effective_date": "2022-07-28",
        "purpose": "General corporate purposes and working capital",
        "covenants": ["Maintain debt-to-equity ratio below 3.0", "Quarterly financial reporting"],
        "security_collateral": "Unsecured",
        "prepayment_terms": "Voluntary prepayment allowed without penalty"
    }}
]

Document text:
{text_content}
"""

            # Call LLM API
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": "You are a financial document analysis expert specializing in SEC filings and loan agreements. Extract information precisely and return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )

            result_text = response.choices[0].message.content.strip()

            # Parse JSON response
            # Remove markdown code blocks if present
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.startswith('```'):
                result_text = result_text[3:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            result_text = result_text.strip()

            import json
            loan_agreements = json.loads(result_text)

            # Validate structure
            if not isinstance(loan_agreements, list):
                self._log("LLM returned non-list format", "ERROR")
                return []

            return loan_agreements

        except json.JSONDecodeError as e:
            self._log(f"Failed to parse LLM response as JSON: {e}", "ERROR")
            self._log(f"LLM response: {result_text[:500] if 'result_text' in locals() else 'N/A'}...", "DEBUG")
            return []
        except Exception as e:
            self._log(f"Error in LLM extraction: {e}", "ERROR")
            return []

    def search_opencorporates_company(self, company_name):
        """
        Search OpenCorporates API for a company by name.

        Args:
            company_name (str): Company name to search

        Returns:
            dict or None: Company data with jurisdiction_code and company_number, or None if not found/error
        """
        if not self.opencorporates_api_key:
            return None

        url = f"{self.opencorporates_base_url}/companies/search"
        params = {
            'q': company_name,
            'api_token': self.opencorporates_api_key,
            'per_page': 1  # Get best match only
        }

        try:
            response = requests.get(url, params=params, timeout=30)

            # Handle rate limiting
            if response.status_code == 429:
                self._log("OpenCorporates API rate limit exceeded", "WARN")
                return None

            response.raise_for_status()
            data = response.json()

            if data.get('results', {}).get('companies'):
                company = data['results']['companies'][0]['company']
                return {
                    'name': company['name'],
                    'jurisdiction_code': company['jurisdiction_code'],
                    'company_number': company['company_number'],
                    'status': company.get('current_status', 'Unknown'),
                    'incorporation_date': company.get('incorporation_date', '')
                }
            return None

        except requests.exceptions.RequestException as e:
            self._log(f"OpenCorporates API error: {e}", "ERROR")
            return None

    def find_related_companies_api(self, company_name):
        """
        Find subsidiaries and sister companies using OpenCorporates API.

        Args:
            company_name (str): Company name to search

        Returns:
            dict: {
                'subsidiaries': [list of subsidiary dicts],
                'sisters': [list of sister company dicts],
                'parent': parent company dict or None,
                'method': 'api'
            }
        """
        # Step 1: Find the target company
        self._log(f"Looking up company in OpenCorporates API...", "INFO")
        company_data = self.search_opencorporates_company(company_name)
        if not company_data:
            self._log(f"Company not found in OpenCorporates API", "WARN")
            return {'subsidiaries': [], 'sisters': [], 'parent': None, 'method': 'none', 'source_url': None, 'filing_date': None}

        jurisdiction_code = company_data['jurisdiction_code']
        company_number = company_data['company_number']
        self._log(f"Found company: {company_data['name']} ({jurisdiction_code})", "SUCCESS")

        subsidiaries = []
        sisters = []
        parent_company = None

        # Step 2: Find subsidiaries (companies controlled by target company)
        self._log(f"Searching for subsidiaries via API...", "INFO")
        try:
            url = f"{self.opencorporates_base_url}/statements/control_statements/search"
            params = {
                'api_token': self.opencorporates_api_key,
                'controller_jurisdiction_code': jurisdiction_code,
                'controller_company_number': company_number,
                'per_page': 100
            }
            response = requests.get(url, params=params, timeout=30)

            if response.status_code != 429:  # Skip if rate limited
                response.raise_for_status()
                data = response.json()

                for statement in data.get('results', {}).get('statements', []):
                    stmt_data = statement.get('statement', {})
                    controlled = stmt_data.get('controlled_entity', {})
                    if controlled:
                        subsidiaries.append({
                            'name': controlled.get('name', 'Unknown'),
                            'jurisdiction': controlled.get('jurisdiction_code', 'Unknown'),
                            'status': 'Active',  # Default, could parse from API
                            'relationship': 'subsidiary',
                            'level': 1,
                            'source': 'opencorporates_api'
                        })
                if subsidiaries:
                    self._log(f"Found {len(subsidiaries)} subsidiaries via API", "SUCCESS")
        except Exception as e:
            self._log(f"Error finding subsidiaries via API: {e}", "ERROR")

        # Step 3: Find parent company (to enable finding sister companies)
        self._log(f"Looking for parent company...", "INFO")
        try:
            url = f"{self.opencorporates_base_url}/statements/control_statements/search"
            params = {
                'api_token': self.opencorporates_api_key,
                'controlled_jurisdiction_code': jurisdiction_code,
                'controlled_company_number': company_number,
                'per_page': 10
            }
            response = requests.get(url, params=params, timeout=30)

            if response.status_code != 429:
                response.raise_for_status()
                data = response.json()

                if data.get('results', {}).get('statements'):
                    statement = data['results']['statements'][0]
                    controller = statement.get('statement', {}).get('controller', {})
                    if controller:
                        parent_company = {
                            'name': controller.get('name', 'Unknown'),
                            'jurisdiction_code': controller.get('jurisdiction_code'),
                            'company_number': controller.get('company_number')
                        }
                        self._log(f"Found parent company: {parent_company['name']}", "SUCCESS")
        except Exception as e:
            self._log(f"Error finding parent via API: {e}", "ERROR")

        # Step 4: If parent found, find all its children (sister companies)
        if parent_company and parent_company.get('jurisdiction_code') and parent_company.get('company_number'):
            self._log(f"Searching for sister companies via API...", "INFO")
            try:
                url = f"{self.opencorporates_base_url}/statements/control_statements/search"
                params = {
                    'api_token': self.opencorporates_api_key,
                    'controller_jurisdiction_code': parent_company['jurisdiction_code'],
                    'controller_company_number': parent_company['company_number'],
                    'per_page': 100
                }
                response = requests.get(url, params=params, timeout=30)

                if response.status_code != 429:
                    response.raise_for_status()
                    data = response.json()

                    for statement in data.get('results', {}).get('statements', []):
                        stmt_data = statement.get('statement', {})
                        controlled = stmt_data.get('controlled_entity', {})
                        if controlled:
                            sister_name = controlled.get('name', 'Unknown')
                            # Skip the original company itself
                            if sister_name.lower() != company_name.lower():
                                sisters.append({
                                    'name': sister_name,
                                    'jurisdiction': controlled.get('jurisdiction_code', 'Unknown'),
                                    'status': 'Active',
                                    'relationship': 'sister',
                                    'level': 0,  # Same level as target company
                                    'source': 'opencorporates_api'
                                })
                if sisters:
                    self._log(f"Found {len(sisters)} sister companies via API", "SUCCESS")
            except Exception as e:
                self._log(f"Error finding sister companies via API: {e}", "ERROR")

        return {
            'subsidiaries': subsidiaries,
            'sisters': sisters,
            'parent': parent_company,
            'method': 'api',
            'source_url': None,  # OpenCorporates API doesn't have a single source document
            'filing_date': None
        }

    def _filter_by_ownership(self, subsidiaries, ownership_threshold):
        """
        Filter subsidiaries based on ownership threshold.

        Args:
            subsidiaries (list): List of subsidiary dictionaries
            ownership_threshold (int): Minimum ownership percentage (0-100)

        Returns:
            list: Filtered list of subsidiaries
        """
        if ownership_threshold == 0:
            return subsidiaries

        filtered = []
        for sub in subsidiaries:
            ownership_pct = sub.get('ownership_percentage')

            if ownership_pct is not None:
                # If we have ownership data, check against threshold
                if ownership_pct >= ownership_threshold:
                    filtered.append(sub)
            else:
                # If ownership is unknown
                # Include it only if threshold is not 100% (not requiring wholly-owned)
                if ownership_threshold < 100:
                    filtered.append(sub)

        return filtered

    def _validate_person_name(self, name):
        """
        Validate that a name looks like a real person's name, not a placeholder.

        Args:
            name (str): Person name to validate

        Returns:
            bool: True if name looks valid, False if it's a placeholder or invalid
        """
        if not name or not name.strip():
            return False

        name_lower = name.lower().strip()

        # List of common placeholder names to reject
        placeholder_names = [
            'john doe', 'jane doe', 'john smith', 'jane smith',
            'mr. smith', 'ms. jones', 'unknown', 'not available',
            'n/a', 'blank', 'none', 'example', 'placeholder',
            'director', 'officer', 'shareholder', 'name',
            'person a', 'person b', 'individual'
        ]

        # Check if it matches any placeholder
        for placeholder in placeholder_names:
            if name_lower == placeholder or placeholder in name_lower:
                return False

        # Reject if it's too short (less than 3 characters)
        if len(name.strip()) < 3:
            return False

        # Reject if it doesn't contain at least one letter
        if not any(c.isalpha() for c in name):
            return False

        return True

    def _validate_company_name(self, name):
        """
        Validate that a name looks like a legal entity name, not a description.

        Args:
            name (str): Company name to validate

        Returns:
            bool: True if name looks valid, False if it looks like a description
        """
        name_lower = name.lower()

        # Reject if it contains description phrases
        description_phrases = [
            'subsidiary for', 'developer of', 'maker of', 'known for',
            'specializing in', 'focused on', 'provider of', 'platform for',
            'service for', 'company for', 'backed', 'owned by',
            'operates in', 'based on', 'creator of'
        ]

        for phrase in description_phrases:
            if phrase in name_lower:
                return False

        # Reject if it's too long (likely a description)
        if len(name) > 100:
            return False

        # Reject if it contains multiple "of" or "for" (likely descriptive)
        if name_lower.count(' of ') > 1 or name_lower.count(' for ') > 1:
            return False

        return True

    def _store_financial_intelligence(self, sec_results):
        """
        Store directors, shareholders, and transactions in the database.

        Args:
            sec_results (dict): Results from find_subsidiaries_sec_edgar containing financial intelligence
        """
        try:
            import database as db

            company_name = sec_results.get('company_name')
            cik = sec_results.get('cik')
            filing_date = sec_results.get('filing_date')
            filing_type = '10-K' if sec_results['method'] == 'sec_edgar_10k' else '20-F'
            source_url = sec_results.get('fin_intel_url') or sec_results.get('source_url')

            directors = sec_results.get('directors', [])
            shareholders = sec_results.get('shareholders', [])
            transactions = sec_results.get('transactions', [])

            if directors:
                self._log(f"Storing {len(directors)} directors in database...", "INFO")
                db.insert_directors(company_name, cik, directors, filing_type, filing_date, source_url)

            if shareholders:
                self._log(f"Storing {len(shareholders)} shareholders in database...", "INFO")
                db.insert_shareholders(company_name, cik, shareholders, filing_type, filing_date, source_url)

            if transactions:
                self._log(f"Storing {len(transactions)} transactions in database...", "INFO")
                db.insert_transactions(company_name, cik, transactions, filing_type, filing_date, source_url)

        except Exception as e:
            self._log(f"Error storing financial intelligence: {e}", "ERROR")

    def _search_sister_companies(self, company_name):
        """
        Search for sister companies using DuckDuckGo (fallback method).

        Args:
            company_name (str): Company name

        Returns:
            list: List of sister company dictionaries
        """
        # Enhanced search query for sister companies
        query = f'site:opencorporates.com "{company_name}" "parent company" OR "sister company" OR "affiliated with" OR "same parent" OR "holding company"'

        try:
            results = self.ddgs.text(query, max_results=15)
            if not results:
                return []

            # Aggregate search result text
            text_data = ""
            for r in results:
                text_data += f"Title: {r.get('title', '')}\n"
                text_data += f"URL: {r.get('href', '')}\n"
                text_data += f"Snippet: {r.get('body', '')}\n\n"

            # Use LLM to extract sister companies
            prompt = f"""
Analyze the following search results about "{company_name}".

Extract ONLY the LEGAL ENTITY NAMES of SISTER COMPANIES.

Sister companies are companies that share the SAME PARENT COMPANY with "{company_name}".
They are NOT subsidiaries OF "{company_name}" - they are OTHER subsidiaries of the same parent.

CRITICAL RULES:
1. Extract ONLY the actual legal company name (e.g., "Company A Inc.", "Company B Ltd.")
2. DO NOT include descriptions, products, or services (e.g., NOT "Gaming subsidiary specializing in...")
3. DO NOT include parent company references (e.g., NOT "Parent-backed company")
4. DO NOT include phrases like "developer of", "maker of", "known for"
5. DO NOT include any numbering or bullet points (e.g., NOT "1. Company Name" - just "Company Name")
6. If you cannot find a clear legal name, SKIP that entry entirely

DO NOT include:
- "{company_name}" itself
- Subsidiaries of "{company_name}" (companies owned BY "{company_name}")
- The parent company itself
- Numbered lists or bullets

For each sister company found, provide:
- Legal entity name ONLY (no numbers, no bullets)
- Jurisdiction (country/state if mentioned)
- Status (always mark as "Sister Company")
- Source URL (the exact URL from the search result where this company was mentioned)

Search Results:
{text_data}

Output format (one per line, NO NUMBERING):
LEGAL_ENTITY_NAME | JURISDICTION | Sister Company | SOURCE_URL

GOOD Examples (format only - these are NOT real companies to be extracted):
Disney Channel Networks | United States | Sister Company | https://opencorporates.com/companies/us/xyz123
Paramount Television | United States | Sister Company | https://opencorporates.com/companies/ca/abc456
Warner Bros. Entertainment | United States | Sister Company | https://opencorporates.com/companies/fi/tech789

IMPORTANT:
- DO NOT number the lines (no "1.", "2.", etc.)
- Always include the SOURCE_URL from the search results above
- Only output the pipe-delimited format shown above

BAD Examples (DO NOT output these):
1. Parent-backed company | United States | Sister Company  ← WRONG: numbered list
2. Developer of products | United States | Sister Company  ← WRONG: numbered and description
LEGAL_ENTITY_NAME | United States | Sister Company  ← WRONG: placeholder text
Gaming subsidiary for mobile | China | Sister Company  ← WRONG: description not legal name

If no sister companies are clearly identified, respond with "NO_SISTERS_FOUND".
Be conservative - only extract entities clearly identified as sister companies with clear legal names.
"""

            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=800
            )

            content = response.choices[0].message.content.strip()

            if "NO_SISTERS_FOUND" in content:
                return []

            # Parse LLM response with validation
            sisters = []
            for line in content.split('\n'):
                line = line.strip()
                if not line or '|' not in line:
                    continue

                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3:
                    company_name = parts[0]

                    # Strip leading numbering (e.g., "1. ", "9. ", "12. ") from search results
                    # Pattern: optional whitespace + digits + dot + optional whitespace
                    # This preserves numbers in company names like "3M Company", "21st Century Fox"
                    company_name = re.sub(r'^\s*\d+\.\s*', '', company_name).strip()

                    # Filter out placeholder text and invalid entries
                    invalid_placeholders = [
                        'LEGAL_ENTITY_NAME',
                        'NO_SISTERS_FOUND',
                        'COMPANY_NAME',
                        'EXAMPLE',
                        'XYZ Corporation',
                        'ABC International',
                        'Tech Solutions'
                    ]

                    # Skip if it's a placeholder or example
                    if any(placeholder.lower() in company_name.lower() for placeholder in invalid_placeholders):
                        self._log(f"Filtered out placeholder/example: '{company_name}'", "INFO")
                        continue

                    # Validate that it looks like a company name, not a description
                    if self._validate_company_name(company_name):
                        # Parse source URL if provided
                        source_url = None
                        if len(parts) >= 4:
                            url = parts[3].strip()
                            if url and url.startswith('http'):
                                source_url = url

                        sisters.append({
                            'name': company_name,
                            'jurisdiction': parts[1],
                            'status': parts[2],
                            'relationship': 'sister',
                            'level': 0,
                            'source': 'duckduckgo',
                            'reference_url': source_url
                        })
                    else:
                        self._log(f"Filtered out invalid entry: '{company_name}'", "INFO")

            return sisters

        except Exception as e:
            self._log(f"Error searching sister companies via DuckDuckGo: {e}", "ERROR")
            return []

    def _search_parent_company(self, company_name):
        """
        Search for parent company using DuckDuckGo + LLM extraction.

        Search queries:
        - "{company_name}" parent company
        - "{company_name}" owned by
        - "{company_name}" subsidiary of
        - site:wikipedia.org "{company_name}" parent company

        Args:
            company_name (str): Company name to search

        Returns:
            dict: {
                'name': str,
                'relationship': 'parent',
                'source': str (URL where found),
                'confidence': str ('high'/'medium'/'low')
            } or None if not found
        """
        self._log(f"Searching for parent company of '{company_name}'...", "INFO")

        # Try multiple search strategies
        queries = [
            f'site:wikipedia.org "{company_name}" "parent company" OR "owned by" OR "subsidiary of" OR "acquired by"',
            f'site:opencorporates.com "{company_name}" "parent company" OR "owned by"',
            f'"{company_name}" "parent company" OR "owned by" OR "subsidiary of" OR "holding company" OR "acquired by" OR "acquisition"'
        ]

        all_results = []
        for query in queries:
            try:
                results = self.ddgs.text(query, max_results=10)
                if results:
                    all_results.extend(results)
            except Exception as e:
                self._log(f"Search query failed: {e}", "WARN")
                continue

        if not all_results:
            self._log("No search results found for parent company", "INFO")
            return None

        # Aggregate search result text
        text_data = ""
        for r in all_results[:20]:  # Limit to top 20 results
            text_data += f"Title: {r.get('title', '')}\n"
            text_data += f"URL: {r.get('href', '')}\n"
            text_data += f"Snippet: {r.get('body', '')}\n\n"

        # Use LLM to extract parent company
        prompt = f"""
Analyze the following search results about "{company_name}".

Identify the PARENT COMPANY that OWNS "{company_name}".

CRITICAL RULES:
1. Extract ONLY the actual legal company name of the parent/owner (e.g., "Company A Holdings Inc.")
2. DO NOT include "{company_name}" itself - we want the company that OWNS "{company_name}"
3. DO NOT include subsidiaries of "{company_name}" - we want the company ABOVE it in the hierarchy
4. DO NOT include sister companies - we want the direct parent/owner
5. If multiple ownership levels exist, extract the DIRECT parent (not the ultimate parent)
6. Be conservative - only extract if clearly stated that company X OWNS, is the PARENT of, or ACQUIRED "{company_name}" (acquisition = ownership)

Search Results:
{text_data}

Output format (single line):
PARENT_COMPANY_NAME | JURISDICTION | CONFIDENCE | SOURCE_URL

Where CONFIDENCE is one of: high, medium, low
- high: explicitly stated as parent/owner with clear evidence
- medium: likely parent based on context
- low: possible parent but uncertain

If NO CLEAR PARENT COMPANY is found, respond with exactly: "NO_PARENT_FOUND"

Example good output:
Huawei Investment & Holding Co., Ltd | China | high | https://en.wikipedia.org/wiki/Huawei
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=300
            )

            content = response.choices[0].message.content.strip()

            if "NO_PARENT_FOUND" in content:
                self._log("No parent company identified", "INFO")
                return None

            # Parse LLM response
            if '|' in content:
                parts = [p.strip() for p in content.split('|')]
                if len(parts) >= 3:
                    parent_name = parts[0]

                    # Filter out placeholder text
                    invalid_placeholders = [
                        'PARENT_COMPANY_NAME',
                        'NO_PARENT_FOUND',
                        'COMPANY_NAME',
                        'EXAMPLE'
                    ]

                    if any(placeholder.lower() in parent_name.lower() for placeholder in invalid_placeholders):
                        self._log(f"Filtered out placeholder: '{parent_name}'", "INFO")
                        return None

                    # Validate that it's different from the search company
                    if parent_name.lower() == company_name.lower():
                        self._log(f"Parent name matches search company - skipping", "INFO")
                        return None

                    # Validate that it looks like a company name
                    if self._validate_company_name(parent_name):
                        source_url = None
                        if len(parts) >= 4:
                            url = parts[3].strip()
                            if url and url.startswith('http'):
                                source_url = url

                        parent_info = {
                            'name': parent_name,
                            'jurisdiction': parts[1],
                            'relationship': 'parent',
                            'confidence': parts[2],
                            'source': 'duckduckgo',
                            'reference_url': source_url
                        }

                        self._log(f"✓ Found parent company: {parent_name} (confidence: {parts[2]})", "SUCCESS")
                        return parent_info
                    else:
                        self._log(f"Filtered out invalid parent name: '{parent_name}'", "INFO")

            return None

        except Exception as e:
            self._log(f"Error extracting parent company: {e}", "ERROR")
            return None

    def _generate_subsidiary_queries(self, company_name):
        """
        Generate multiple search query variations for finding subsidiaries.
        Using different phrasings increases recall significantly.

        Args:
            company_name (str): Company name

        Returns:
            list: List of search query strings
        """
        queries = [
            f'"subsidiaries of {company_name}"',  # User's preferred format
            f'"{company_name} subsidiaries list"',
            f'"{company_name}" wholly owned companies',
            f'"{company_name}" business units divisions',
            f'"{company_name}" operating companies',
            f'"{company_name}" brands divisions',
            f'"companies owned by {company_name}"',
            f'"{company_name}" corporate structure subsidiaries'
        ]
        return queries

    def _search_subsidiaries_duckduckgo(self, company_name):
        """
        Search for subsidiaries using DuckDuckGo with multiple query variations.
        Uses 8 different query patterns to maximize recall.

        Args:
            company_name (str): Company name

        Returns:
            list: List of subsidiary dictionaries
        """
        # Generate multiple query variations (8 different phrasings)
        queries = self._generate_subsidiary_queries(company_name)

        all_results = []
        seen_urls = set()

        # Search with each query variation
        for idx, query in enumerate(queries, 1):
            self._log(f"DuckDuckGo query {idx}/{len(queries)}: {query[:80]}...", "INFO")
            try:
                # Increased from 15 to 100 results per query
                results = self.ddgs.text(query, max_results=100)

                if results:
                    # Deduplicate by URL
                    for r in results:
                        url = r.get('href', '')
                        if url and url not in seen_urls:
                            all_results.append(r)
                            seen_urls.add(url)

                    self._log(f"  Found {len(results)} results (unique: {len(all_results)} total so far)", "INFO")

                # Rate limiting - small delay between queries
                if idx < len(queries):
                    time.sleep(0.5)

            except Exception as e:
                self._log(f"Error with query {idx}: {e}", "WARN")
                continue

        if not all_results:
            self._log("No DuckDuckGo results found across all query variations", "WARN")
            return []

        self._log(f"✓ Collected {len(all_results)} unique search results from {len(queries)} query variations", "SUCCESS")

        # Aggregate search result text from all queries
        text_data = ""
        for r in all_results:
            text_data += f"Title: {r.get('title', '')}\n"
            text_data += f"URL: {r.get('href', '')}\n"
            text_data += f"Snippet: {r.get('body', '')}\n\n"

        try:
            # Use LLM to extract subsidiaries
            prompt = f"""
Analyze the following search results about "{company_name}".

Extract ONLY the LEGAL ENTITY NAMES of SUBSIDIARY COMPANIES.

Subsidiary companies are companies that are OWNED BY "{company_name}".
They are NOT sister companies (companies owned by the same parent as "{company_name}").

CRITICAL RULES:
1. Extract ONLY the actual legal company name (e.g., "Company A Inc.", "Company B Ltd.")
2. DO NOT include descriptions, products, or services (e.g., NOT "Gaming subsidiary specializing in...")
3. DO NOT include parent company references (e.g., NOT "Parent-backed company")
4. DO NOT include phrases like "developer of", "maker of", "known for"
5. DO NOT include any numbering or bullet points (e.g., NOT "1. Company Name" - just "Company Name")
6. If you cannot find a clear legal name, SKIP that entry entirely

DO NOT include:
- "{company_name}" itself
- Sister companies (companies owned by the SAME PARENT as "{company_name}")
- The parent company of "{company_name}"
- Numbered lists or bullets

For each subsidiary company found, provide:
- Legal entity name ONLY (no numbers, no bullets)
- Jurisdiction (country/state if mentioned)
- Status (always mark as "Subsidiary")
- Source URL (the exact URL from the search result where this company was mentioned)

Search Results:
{text_data}

Output format (one per line, NO NUMBERING):
LEGAL_ENTITY_NAME | JURISDICTION | Subsidiary | SOURCE_URL

GOOD Examples (format only - these are NOT real companies to be extracted):
Taobao Holding Limited | China | Subsidiary | https://example.com/page1
Tmall Technology Co., Ltd. | China | Subsidiary | https://example.com/page2
Alibaba Cloud Computing Ltd. | China | Subsidiary | https://example.com/page3

IMPORTANT:
- DO NOT number the lines (no "1.", "2.", etc.)
- Always include the SOURCE_URL from the search results above
- Only output the pipe-delimited format shown above

BAD Examples (DO NOT output these):
1. Parent-backed company | United States | Subsidiary  ← WRONG: numbered list
2. Developer of products | United States | Subsidiary  ← WRONG: numbered and description
LEGAL_ENTITY_NAME | United States | Subsidiary  ← WRONG: placeholder text
Gaming subsidiary for mobile | China | Subsidiary  ← WRONG: description not legal name

If no subsidiaries are clearly identified, respond with "NO_SUBSIDIARIES_FOUND".
Be conservative - only extract entities clearly identified as subsidiaries with clear legal names.
"""

            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000  # Increased from 800 to handle more results
            )

            content = response.choices[0].message.content.strip()

            if "NO_SUBSIDIARIES_FOUND" in content:
                return []

            # Parse LLM response with validation
            subsidiaries = []
            for line in content.split('\n'):
                line = line.strip()
                if not line or '|' not in line:
                    continue

                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3:
                    company_name_extracted = parts[0]

                    # Strip leading numbering (e.g., "1. ", "9. ", "12. ") from search results
                    # Pattern: optional whitespace + digits + dot + optional whitespace
                    # This preserves numbers in company names like "3M Company", "21st Century Fox"
                    company_name_extracted = re.sub(r'^\s*\d+\.\s*', '', company_name_extracted).strip()

                    # Filter out placeholder text and invalid entries
                    invalid_placeholders = [
                        'LEGAL_ENTITY_NAME',
                        'NO_SUBSIDIARIES_FOUND',
                        'COMPANY_NAME',
                        'EXAMPLE',
                        'XYZ Corporation',
                        'ABC International',
                        'Tech Solutions'
                    ]

                    # Skip if it's a placeholder or example
                    if any(placeholder.lower() in company_name_extracted.lower() for placeholder in invalid_placeholders):
                        self._log(f"Filtered out placeholder/example: '{company_name_extracted}'", "INFO")
                        continue

                    # Validate that it looks like a company name, not a description
                    if self._validate_company_name(company_name_extracted):
                        # Parse source URL if provided
                        source_url = None
                        if len(parts) >= 4:
                            url = parts[3].strip()
                            if url and url.startswith('http'):
                                source_url = url

                        subsidiaries.append({
                            'name': company_name_extracted,
                            'jurisdiction': parts[1],
                            'status': parts[2],
                            'relationship': 'subsidiary',
                            'level': 1,
                            'source': 'duckduckgo',
                            'reference_url': source_url
                        })
                    else:
                        self._log(f"Filtered out invalid entry: '{company_name_extracted}'", "INFO")

            return subsidiaries

        except Exception as e:
            self._log(f"Error searching subsidiaries via DuckDuckGo: {e}", "ERROR")
            return []

    def _search_google_subsidiaries(self, company_name):
        """
        Search for subsidiaries using Google (via googlesearch-python), prioritising
        high-quality sources such as greyb.com.

        Args:
            company_name (str): Company name

        Returns:
            list: List of subsidiary dictionaries with source='google'
        """
        if not GOOGLE_SEARCH_AVAILABLE:
            self._log("googlesearch-python not installed; skipping Google subsidiary search", "WARN")
            return []

        try:
            queries = [
                f'"{company_name}" subsidiaries list site:insights.greyb.com',
                f'"{company_name}" subsidiaries complete list',
            ]

            seen_urls = []
            for query in queries:
                try:
                    for url in google_search(query, num_results=5, sleep_interval=1):
                        if url and url not in seen_urls:
                            seen_urls.append(url)
                except Exception as e:
                    self._log(f"Google query failed '{query[:60]}': {e}", "WARN")
                time.sleep(2)

            # Prioritise greyb.com URLs
            seen_urls.sort(key=lambda u: (0 if 'greyb.com' in u else 1))
            top_urls = seen_urls[:3]

            if not top_urls:
                return []

            all_subsidiaries = []

            for url in top_urls:
                try:
                    response = requests.get(
                        url,
                        headers={'User-Agent': 'Mozilla/5.0 (compatible; research-bot/1.0)'},
                        timeout=15
                    )
                    response.raise_for_status()

                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.text, 'lxml')

                    # Remove noise tags
                    for tag in soup(['nav', 'footer', 'script', 'style', 'header']):
                        tag.decompose()

                    page_text = soup.get_text(separator='\n', strip=True)[:15000]

                    prompt = f"""
Analyze the following web page content about "{company_name}".

Extract ONLY the LEGAL ENTITY NAMES of SUBSIDIARY COMPANIES.

Subsidiary companies are companies that are OWNED BY "{company_name}".

CRITICAL RULES:
1. Extract ONLY the actual legal company name (e.g., "Company A Inc.", "Company B Ltd.")
2. DO NOT include descriptions, products, or services
3. DO NOT include "{company_name}" itself
4. DO NOT include numbering or bullet points in the name field

For each subsidiary company found, provide:
- Legal entity name ONLY
- Jurisdiction (country/state if mentioned, else 'Unknown')
- Status (always "Subsidiary")
- Source URL: {url}

Output format (one per line):
LEGAL_ENTITY_NAME | JURISDICTION | Subsidiary | {url}

If no subsidiaries are clearly identified, respond with "NO_SUBSIDIARIES_FOUND".

Page content:
{page_text}
"""

                    response_llm = self.client.chat.completions.create(
                        model=self.model_id,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.1,
                        max_tokens=2000
                    )

                    content = response_llm.choices[0].message.content.strip()

                    if "NO_SUBSIDIARIES_FOUND" in content:
                        continue

                    for line in content.split('\n'):
                        line = line.strip()
                        if not line or '|' not in line:
                            continue
                        parts = [p.strip() for p in line.split('|')]
                        if len(parts) >= 3:
                            extracted_name = re.sub(r'^\s*\d+\.\s*', '', parts[0]).strip()
                            invalid_placeholders = [
                                'LEGAL_ENTITY_NAME', 'NO_SUBSIDIARIES_FOUND',
                                'COMPANY_NAME', 'EXAMPLE'
                            ]
                            if any(p.lower() in extracted_name.lower() for p in invalid_placeholders):
                                continue
                            if self._validate_company_name(extracted_name):
                                all_subsidiaries.append({
                                    'name': extracted_name,
                                    'jurisdiction': parts[1],
                                    'status': parts[2],
                                    'relationship': 'subsidiary',
                                    'level': 1,
                                    'source': 'google',
                                    'reference_url': url
                                })

                except Exception as e:
                    self._log(f"Error fetching/parsing {url}: {e}", "WARN")
                    continue

            return all_subsidiaries

        except Exception as e:
            self._log(f"Error in Google subsidiary search: {e}", "ERROR")
            return []

    def _search_wikipedia_subsidiaries(self, company_name):
        """
        Search Wikipedia for subsidiaries and sister companies.

        Args:
            company_name (str): Company name to search

        Returns:
            dict: {
                'subsidiaries': [list of subsidiary dicts],
                'sisters': [list of sister company dicts]
            }
        """
        subsidiaries = []
        sisters = []

        try:
            self._log(f"Searching Wikipedia for {company_name}...", "INFO")

            # Wikipedia requires User-Agent header
            headers = {
                'User-Agent': 'SanctionsScreeningBot/1.0 (Research Tool; Python/requests)'
            }

            # Search for the Wikipedia page
            search_url = "https://en.wikipedia.org/w/api.php"
            search_params = {
                'action': 'opensearch',
                'search': company_name,
                'limit': 3,
                'format': 'json'
            }

            response = requests.get(search_url, params=search_params, headers=headers, timeout=10)
            response.raise_for_status()
            search_results = response.json()

            # Pick the best matching title using fuzzy similarity
            if not search_results[1]:
                self._log(f"No Wikipedia page found for {company_name}", "WARN")
                return {'subsidiaries': [], 'sisters': []}

            from fuzzywuzzy import fuzz
            best_title = None
            best_score = 0
            for candidate in search_results[1]:
                score = fuzz.token_set_ratio(company_name.lower(), candidate.lower())
                if score > best_score:
                    best_score = score
                    best_title = candidate

            WIKI_SIMILARITY_THRESHOLD = 55
            if best_score < WIKI_SIMILARITY_THRESHOLD:
                self._log(
                    f"Wikipedia result '{best_title}' doesn't match '{company_name}' "
                    f"(similarity {best_score}% < {WIKI_SIMILARITY_THRESHOLD}%), skipping",
                    "WARN"
                )
                return {'subsidiaries': [], 'sisters': []}

            page_title = best_title
            self._log(f"Found Wikipedia page: {page_title}", "SUCCESS")

            # Fetch the page content
            content_params = {
                'action': 'query',
                'titles': page_title,
                'prop': 'extracts',
                'explaintext': 1,  # Plain text (Wikipedia API expects integer, not boolean)
                'exlimit': 1,  # Limit to 1 page
                'format': 'json',
                'formatversion': 2,  # Use newer API response format
                'redirects': 1  # Follow redirects automatically
            }

            # Note: Not using exintro=1 because we need full article for subsidiaries/sisters
            # Not using exsectionformat as it can cause empty responses

            response = requests.get(search_url, params=content_params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Extract the page content (formatversion 2 returns list, formatversion 1 returns dict)
            pages = data.get('query', {}).get('pages', [])

            # Handle both formatversion 2 (list) and formatversion 1 (dict)
            if isinstance(pages, dict):
                # Old format (formatversion 1) - dict with page IDs as keys
                pages = list(pages.values())

            # Debug: log what we got back
            if not pages:
                self._log(f"Wikipedia API returned no pages in response", "WARN")
                self._log(f"Response data: {str(data)[:200]}", "DEBUG")
                return {'subsidiaries': [], 'sisters': []}

            page_content = None
            for page_data in pages:
                # Check if page exists (not missing)
                if page_data.get('missing'):
                    self._log(f"Wikipedia page '{page_title}' was found in search but doesn't exist", "WARN")
                    return {'subsidiaries': [], 'sisters': []}

                page_content = page_data.get('extract', '')

                # Debug: show what we got
                if page_content:
                    self._log(f"Extracted {len(page_content)} characters from Wikipedia", "INFO")
                    break
                else:
                    self._log(f"Wikipedia page exists but extract field is empty", "WARN")
                    self._log(f"Page data keys: {list(page_data.keys())}", "DEBUG")
                    # Show a sample of the page data to help diagnose
                    page_sample = {k: str(v)[:100] if k != 'extract' else f"[empty, length={len(str(v))}]"
                                   for k, v in page_data.items()}
                    self._log(f"Page data sample: {page_sample}", "DEBUG")

            if not page_content or len(page_content.strip()) < 100:
                self._log(f"Could not extract meaningful Wikipedia content (page may be a stub, disambiguation, or redirect)", "WARN")
                return {'subsidiaries': [], 'sisters': []}

            # Limit content size (Wikipedia pages can be very long)
            # Increased from 30000 to 100000 to capture more subsidiary information
            max_chars = 100000
            if len(page_content) > max_chars:
                self._log(f"Wikipedia page is long ({len(page_content)} chars), using first {max_chars} chars", "INFO")
                page_content = page_content[:max_chars]

            self._log(f"Parsing Wikipedia content with LLM ({len(page_content)} chars)...", "INFO")

            # Use LLM to extract subsidiaries and sister companies
            prompt = f"""
Analyze this Wikipedia page about "{company_name}".

Extract ONLY the LEGAL ENTITY NAMES of:
1. SUBSIDIARIES: Companies that are owned/controlled by "{company_name}"
2. SISTER COMPANIES: Companies that share the same parent company with "{company_name}" (but are not owned by "{company_name}")

CRITICAL RULES:
1. Extract ONLY the actual legal company name or brand name (e.g., "Brand Name", "Company Inc.")
2. DO NOT include descriptions or products (e.g., NOT "Platform for services")
3. DO NOT include parent references (e.g., NOT "Parent-owned company")
4. DO NOT include phrases like "developer of", "maker of", "service for"
5. Brand names are OK if they're the actual company name
6. If you cannot find a clear legal or brand name, SKIP that entry

For each company found, provide:
- Legal entity name or brand name ONLY
- Jurisdiction (country/state if mentioned, or "Unknown")
- Relationship (either "subsidiary" or "sister")
- Ownership percentage (if mentioned, otherwise "Unknown")

Wikipedia Content:
{page_content}

Output format (one per line):
LEGAL_NAME | JURISDICTION | RELATIONSHIP | OWNERSHIP_PCT

GOOD Examples (format only - these are NOT real companies):
ProductName | Country | subsidiary | 100
XYZ Company Inc. | United States | subsidiary | Unknown
ABC Corporation | Finland | subsidiary | 84.3
Tech Co. Ltd. | United States | sister

BAD Examples (DO NOT output these):
Mobile messaging app | China | subsidiary  ← WRONG: description
Parent-owned company | United States | subsidiary  ← WRONG: not a name
Developer of products | United States | subsidiary  ← WRONG: description

If no subsidiaries or sister companies are clearly mentioned, respond with "NO_COMPANIES_FOUND".
Focus on sections that list subsidiaries, divisions, or related companies.
Extract ALL entities with clear names.
"""

            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=3000  # Increased from 2000 to handle more Wikipedia content
            )

            content = response.choices[0].message.content.strip()

            if "NO_COMPANIES_FOUND" in content:
                self._log(f"No subsidiaries or sister companies found in Wikipedia", "WARN")
                return {'subsidiaries': [], 'sisters': []}

            # Parse LLM response with validation
            for line in content.split('\n'):
                line = line.strip()
                if not line or '|' not in line:
                    continue

                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3:
                    company_name = parts[0]

                    # Strip leading numbering (e.g., "1. ", "9. ", "12. ") from Wikipedia lists
                    # Pattern: optional whitespace + digits + dot + optional whitespace
                    # This preserves numbers in company names like "3M Company", "21st Century Fox"
                    company_name = re.sub(r'^\s*\d+\.\s*', '', company_name).strip()

                    relationship = parts[2].lower()

                    # Validate that it looks like a company name, not a description
                    if not self._validate_company_name(company_name):
                        self._log(f"Filtered out invalid entry: '{company_name}'", "INFO")
                        continue

                    # Parse ownership percentage if provided
                    ownership_pct = None
                    if len(parts) >= 4:
                        ownership_str = parts[3].lower()
                        if ownership_str != 'unknown' and ownership_str != '':
                            try:
                                ownership_pct = float(ownership_str.replace('%', '').strip())
                            except ValueError:
                                pass

                    wiki_url = f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
                    company_dict = {
                        'name': company_name,
                        'jurisdiction': parts[1],
                        'status': 'Active',
                        'level': 1,
                        'source': 'wikipedia',
                        'ownership_percentage': ownership_pct,
                        'reference_url': wiki_url
                    }

                    if relationship == 'subsidiary':
                        company_dict['relationship'] = 'subsidiary'
                        subsidiaries.append(company_dict)
                    elif relationship == 'sister':
                        company_dict['relationship'] = 'sister'
                        company_dict['level'] = 0
                        sisters.append(company_dict)

            self._log(f"Found {len(subsidiaries)} subsidiaries and {len(sisters)} sister companies from Wikipedia", "SUCCESS")

            return {'subsidiaries': subsidiaries, 'sisters': sisters}

        except Exception as e:
            self._log(f"Error searching Wikipedia: {e}", "ERROR")
            return {'subsidiaries': [], 'sisters': []}

    def find_parent_and_sisters(self, subsidiary_name, progress_callback=None):
        """
        Reverse search: Find parent company and sister companies when searching for a subsidiary.

        Args:
            subsidiary_name (str): Name of the subsidiary company
            progress_callback (callable): Optional callback for progress updates

        Returns:
            dict: {
                'parent': Parent company info (or None),
                'sisters': List of sister companies,
                'method': Search method used,
                'subsidiary_info': Info about the searched subsidiary
            }
        """
        print(f"[DEBUG] find_parent_and_sisters method ENTERED for: {subsidiary_name}")
        print(f"[DEBUG] progress_callback is: {progress_callback}")

        def log(msg, level):
            print(f"[DEBUG LOG] {level}: {msg}")  # Always print to console
            if progress_callback:
                progress_callback(msg, level)
            else:
                self._log(msg, level)

        log(f"Searching for parent company of {subsidiary_name}...", "SEARCH")

        parent = None
        sisters = []
        subsidiary_info = None
        method = 'none'

        # Try OpenCorporates API first (best for finding parent companies)
        if self.opencorporates_api_key:
            log("Trying OpenCorporates API to find parent...", "INFO")
            try:
                # Search for the subsidiary company
                subsidiary_data = self.search_opencorporates_company(subsidiary_name)

                if subsidiary_data:
                    subsidiary_info = subsidiary_data
                    log(f"Found subsidiary: {subsidiary_data['name']} ({subsidiary_data['jurisdiction_code']})", "SUCCESS")

                    # Search for parent company
                    url = f"{self.opencorporates_base_url}/statements/control_statements/search"
                    params = {
                        'api_token': self.opencorporates_api_key,
                        'controlled_jurisdiction_code': subsidiary_data['jurisdiction_code'],
                        'controlled_company_number': subsidiary_data['company_number'],
                        'per_page': 10
                    }

                    response = requests.get(url, params=params, timeout=30)

                    if response.status_code != 429 and response.status_code == 200:
                        data = response.json()

                        if data.get('results', {}).get('statements'):
                            statement = data['results']['statements'][0]
                            controller = statement.get('statement', {}).get('controller', {})

                            if controller:
                                parent = {
                                    'name': controller.get('name', 'Unknown'),
                                    'jurisdiction': controller.get('jurisdiction_code', 'Unknown'),
                                    'company_number': controller.get('company_number'),
                                    'status': 'Active',
                                    'source': 'opencorporates_api'
                                }
                                log(f"Found parent company: {parent['name']}", "SUCCESS")
                                method = 'opencorporates_api'

                                # Now find sister companies (other subsidiaries of the same parent)
                                log(f"Searching for sister companies of {subsidiary_name}...", "INFO")

                                params = {
                                    'api_token': self.opencorporates_api_key,
                                    'controller_jurisdiction_code': controller.get('jurisdiction_code'),
                                    'controller_company_number': controller.get('company_number'),
                                    'per_page': 100
                                }

                                response = requests.get(url, params=params, timeout=30)

                                if response.status_code == 200:
                                    data = response.json()

                                    for statement in data.get('results', {}).get('statements', []):
                                        controlled = statement.get('statement', {}).get('controlled_entity', {})
                                        if controlled:
                                            controlled_name = controlled.get('name', 'Unknown')

                                            # Don't include the searched subsidiary itself
                                            if controlled_name.lower() != subsidiary_name.lower():
                                                sisters.append({
                                                    'name': controlled_name,
                                                    'jurisdiction': controlled.get('jurisdiction_code', 'Unknown'),
                                                    'status': 'Active',
                                                    'relationship': 'sister',
                                                    'source': 'opencorporates_api'
                                                })

                                    if sisters:
                                        log(f"Found {len(sisters)} sister companies", "SUCCESS")
            except Exception as e:
                log(f"OpenCorporates API error: {e}", "ERROR")
        else:
            log("No OpenCorporates API key configured", "INFO")

        # If no parent found via API, try multiple sources
        if not parent:
            parent_candidates = []

            # Method 1: Try Wikipedia
            log("Trying Wikipedia to find parent company...", "INFO")
            try:
                headers = {'User-Agent': 'SanctionsScreeningBot/1.0 (Research Tool; Python/requests)'}
                search_url = "https://en.wikipedia.org/w/api.php"

                search_params = {
                    'action': 'opensearch',
                    'search': subsidiary_name,
                    'limit': 1,
                    'format': 'json'
                }

                response = requests.get(search_url, params=search_params, headers=headers, timeout=10)
                response.raise_for_status()
                search_results = response.json()

                log(f"Wikipedia search found {len(search_results[1]) if search_results[1] else 0} results", "DEBUG")

                if search_results[1]:
                    page_title = search_results[1][0]
                    log(f"Found Wikipedia page: {page_title}", "SUCCESS")

                    content_params = {
                        'action': 'query',
                        'titles': page_title,
                        'prop': 'extracts',
                        'explaintext': 1,
                        'exlimit': 1,
                        'format': 'json',
                        'formatversion': 2,
                        'redirects': 1
                    }

                    response = requests.get(search_url, params=content_params, headers=headers, timeout=10)
                    response.raise_for_status()
                    data = response.json()

                    pages = data.get('query', {}).get('pages', [])
                    if isinstance(pages, dict):
                        pages = list(pages.values())

                    if pages:
                        page_content = pages[0].get('extract', '')
                        log(f"Wikipedia page content length: {len(page_content)} chars", "DEBUG")
                        if page_content and len(page_content) > 100:
                            intro = page_content[:3000]
                            log(f"Analyzing Wikipedia content ({len(intro)} chars)...", "INFO")
                            log(f"Wikipedia excerpt (first 200 chars): {intro[:200]}...", "DEBUG")

                            prompt = f"""
Extract the parent company from this Wikipedia excerpt about "{subsidiary_name}".

Text:
{intro}

CRITICAL RULES:
- Look for phrases: "subsidiary of", "owned by", "part of", "acquired by", "operated by", "division of"
- Extract ONLY the parent company's legal name
- DO NOT include any explanations, reasoning, or extra text
- Output ONLY in the exact format shown below, nothing else

Output format (ONLY output this line, nothing else):
PARENT_NAME | COUNTRY

If no parent company found, output only: NONE

Examples of CORRECT output:
Alibaba Group | China
Meta Platforms | United States
Google LLC | United States
NONE
"""

                            response = self.client.chat.completions.create(
                                model=self.model_id,
                                messages=[{"role": "user", "content": prompt}],
                                temperature=0.0,
                            )
                            result = response.choices[0].message.content.strip()
                            log(f"Wikipedia LLM extraction result: {result}", "DEBUG")

                            # Extract the actual "NAME | COUNTRY" line from potentially verbose response
                            # Look for the last line containing a pipe character
                            if result and result != 'NONE':
                                lines = [line.strip() for line in result.split('\n') if line.strip() and '|' in line]
                                if lines:
                                    result = lines[-1]  # Take the last line with a pipe
                                    log(f"Cleaned result: {result}", "DEBUG")

                            if result and result != 'NONE' and '|' in result:
                                parts = [p.strip() for p in result.split('|')]
                                if len(parts) >= 1 and parts[0]:
                                    parent_candidates.append({
                                        'name': parts[0],
                                        'jurisdiction': parts[1] if len(parts) > 1 else 'Unknown',
                                        'source': 'wikipedia',
                                        'confidence': 'high'
                                    })
                                    log(f"Wikipedia suggests parent: {parts[0]}", "INFO")
            except Exception as e:
                log(f"Wikipedia search error: {e}", "ERROR")

            # Method 2: Try DuckDuckGo search
            log("Trying DuckDuckGo search for parent company...", "INFO")
            try:
                import urllib.parse
                search_query = urllib.parse.quote(f'"{subsidiary_name}" parent company owner')
                ddg_url = f"https://html.duckduckgo.com/html/?q={search_query}"

                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }

                response = requests.get(ddg_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Extract search result snippets
                    results = soup.find_all('a', class_='result__snippet')
                    snippets = []
                    for result in results[:3]:
                        text = result.get_text(strip=True)
                        if text:
                            snippets.append(text)

                    log(f"DuckDuckGo found {len(snippets)} snippets", "DEBUG")

                    if snippets:
                        combined_text = "\n".join(snippets[:3])
                        log(f"Analyzing DuckDuckGo results ({len(combined_text)} chars)...", "INFO")
                        log(f"DuckDuckGo snippets: {combined_text[:300]}...", "DEBUG")

                        prompt = f"""
Extract the parent company of "{subsidiary_name}" from these search results.

Search results:
{combined_text}

CRITICAL RULES:
- Look for phrases: "subsidiary of", "owned by", "part of", "acquired by"
- Extract ONLY the parent company name
- DO NOT include any explanations, reasoning, or extra text
- Output ONLY in the exact format shown below, nothing else

Output format (ONLY output this line, nothing else):
PARENT_NAME | COUNTRY

If no parent found, output only: NONE

Examples of CORRECT output:
Alibaba Group | China
Meta Platforms | United States
NONE
"""

                        response = self.client.chat.completions.create(
                            model=self.model_id,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.0,
                        )
                        result = response.choices[0].message.content.strip()
                        log(f"DuckDuckGo LLM extraction result: {result}", "DEBUG")

                        # Extract the actual "NAME | COUNTRY" line from potentially verbose response
                        if result and result != 'NONE':
                            lines = [line.strip() for line in result.split('\n') if line.strip() and '|' in line]
                            if lines:
                                result = lines[-1]  # Take the last line with a pipe
                                log(f"Cleaned result: {result}", "DEBUG")

                        if result and result != 'NONE' and '|' in result:
                            parts = [p.strip() for p in result.split('|')]
                            if len(parts) >= 1 and parts[0]:
                                parent_candidates.append({
                                    'name': parts[0],
                                    'jurisdiction': parts[1] if len(parts) > 1 else 'Unknown',
                                    'source': 'duckduckgo',
                                    'confidence': 'medium'
                                })
                                log(f"DuckDuckGo suggests parent: {parts[0]}", "INFO")
            except Exception as e:
                log(f"DuckDuckGo search error: {e}", "ERROR")

            # Method 3: Try SEC EDGAR (check if subsidiary is mentioned in any company's filings)
            log("Trying SEC EDGAR to find parent company...", "INFO")
            try:
                # Try searching for the subsidiary name in SEC's full-text search
                import urllib.parse
                encoded_name = urllib.parse.quote(subsidiary_name)
                search_url = f"https://www.sec.gov/cgi-bin/browse-edgar?company={encoded_name}&owner=exclude&action=getcompany"

                time.sleep(0.2)  # Rate limiting
                response = requests.get(search_url, headers=self.sec_headers, timeout=15)

                if response.status_code == 200:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Look for company name in the results
                    company_info = soup.find('span', {'class': 'companyName'})
                    if company_info:
                        company_text = company_info.get_text().strip()
                        # Remove CIK from the name
                        import re
                        company_name = re.sub(r'CIK#:\s*\d+', '', company_text).strip()

                        # Check if this is the subsidiary itself or a parent
                        if company_name.lower() != subsidiary_name.lower():
                            parent_candidates.append({
                                'name': company_name,
                                'jurisdiction': 'United States',
                                'source': 'sec_edgar',
                                'confidence': 'medium'
                            })
                            log(f"SEC EDGAR suggests parent: {company_name}", "INFO")
            except Exception as e:
                log(f"SEC EDGAR search error: {e}", "ERROR")

            # Consolidate results - choose best candidate
            log(f"Total parent candidates found: {len(parent_candidates)}", "DEBUG")
            for idx, candidate in enumerate(parent_candidates):
                log(f"Candidate {idx+1}: {candidate['name']} from {candidate['source']} (confidence: {candidate['confidence']})", "DEBUG")

            if parent_candidates:
                # Prefer Wikipedia (most reliable), then DuckDuckGo, then SEC
                parent_candidates.sort(key=lambda x: {'high': 0, 'medium': 1, 'low': 2}.get(x['confidence'], 3))

                best_candidate = parent_candidates[0]
                parent = {
                    'name': best_candidate['name'],
                    'jurisdiction': best_candidate['jurisdiction'],
                    'status': 'Active',
                    'relationship': 'parent',
                    'source': best_candidate['source']
                }
                method = best_candidate['source']
                log(f"Selected parent company: {parent['name']} (source: {method})", "SUCCESS")

                # Now search for sister companies using the parent name
                log(f"Searching for subsidiaries of parent: {parent['name']}...", "INFO")
                parent_results = self.find_subsidiaries(parent['name'], depth=1, include_sisters=False, progress_callback=progress_callback)

                # All subsidiaries of the parent are sister companies (except the one we searched for)
                for sub in parent_results.get('subsidiaries', []):
                    if sub['name'].lower() != subsidiary_name.lower():
                        sub['relationship'] = 'sister'
                        sisters.append(sub)

                if sisters:
                    log(f"Found {len(sisters)} sister companies", "SUCCESS")
                else:
                    log("No sister companies found", "WARN")

        # Return results
        if not parent:
            log(f"No parent company found for {subsidiary_name}", "WARN")
            log("This may be a parent company or independent entity", "INFO")

        return {
            'parent': parent,
            'sisters': sisters,
            'subsidiary_info': subsidiary_info,
            'method': method,
            'searched_company': subsidiary_name
        }

    def find_subsidiaries(self, parent_company_name, depth=1, include_sisters=True, progress_callback=None, ownership_threshold=0, depth_search_subsidiaries=None, max_level_2_searches=20, max_level_3_searches=10):
        """
        Search for subsidiaries and optionally sister companies.
        Tries OpenCorporates API first, then SEC EDGAR, then Wikipedia + DuckDuckGo.

        Args:
            parent_company_name (str): Name of the parent/target company
            depth (int): Search depth for subsidiaries (1-3 levels)
            include_sisters (bool): Whether to also search for sister companies
            progress_callback (callable): Optional callback for progress updates
            ownership_threshold (int): Minimum ownership percentage (0-100). 0 = all subsidiaries, 100 = wholly-owned only
            depth_search_subsidiaries (list): Optional list of subsidiary names to search at depth 2/3. If None, searches all subsidiaries
            max_level_2_searches (int): Maximum subsidiaries to search for level 2 (default: 20, range: 5-50)
            max_level_3_searches (int): Maximum subsidiaries to search for level 3 (default: 10, range: 5-30)

        Returns:
            dict: {
                'subsidiaries': [...],
                'sisters': [...],
                'parent': {...} or None,
                'method': 'api' or 'sec_edgar' or 'wikipedia+duckduckgo' or 'duckduckgo'
            }
        """
        # Set callback for this search
        self.progress_callback = progress_callback

        # Track all data sources tried (for transparency)
        data_sources_tried = []

        # Method 1: Try OpenCorporates API (preferred - fastest & most accurate for international companies)
        if self.opencorporates_api_key:
            data_sources_tried.append('opencorporates_api')
            self._log(f"Trying OpenCorporates API for {parent_company_name}...", "SEARCH")
            api_results = self.find_related_companies_api(parent_company_name)

            # If we got results from API, filter and return them
            if api_results['method'] == 'api' and (api_results['subsidiaries'] or api_results['sisters']):
                self._log(f"✓ API found {len(api_results['subsidiaries'])} level 1 subsidiaries, {len(api_results['sisters'])} sister companies", "SUCCESS")

                # Apply ownership filtering
                if ownership_threshold > 0:
                    original_count = len(api_results['subsidiaries'])
                    api_results['subsidiaries'] = self._filter_by_ownership(api_results['subsidiaries'], ownership_threshold)
                    filtered_count = original_count - len(api_results['subsidiaries'])
                    if filtered_count > 0:
                        self._log(f"Filtered out {filtered_count} subsidiaries not meeting {ownership_threshold}% ownership threshold", "INFO")

                # Multi-level depth search if depth > 1
                if depth >= 2:
                    level_1_subs = list(api_results['subsidiaries'])  # Save current level 1

                    # Filter to selected subsidiaries if specified
                    if depth_search_subsidiaries is not None:
                        level_1_subs_to_search = [sub for sub in level_1_subs if sub['name'] in depth_search_subsidiaries]
                        self._log(f"Searching level 2 for {len(level_1_subs_to_search)} selected subsidiaries (out of {len(level_1_subs)} total)", "INFO")
                    else:
                        # Sort by ownership percentage (highest first) and limit to prevent timeouts
                        sorted_level_1 = sorted(
                            level_1_subs,
                            key=lambda x: x.get('ownership_percentage', 0) or 0,
                            reverse=True
                        )

                        if len(sorted_level_1) > max_level_2_searches:
                            level_1_subs_to_search = sorted_level_1[:max_level_2_searches]
                            api_results.setdefault('warnings', []).append({
                                'source': 'level_2_search',
                                'message': f'Limited level 2 search to top {max_level_2_searches} subsidiaries by ownership (out of {len(level_1_subs)} total) to prevent timeout',
                                'severity': 'info'
                            })
                            self._log(f"⚠️  Limiting level 2 search to top {max_level_2_searches} subsidiaries by ownership (out of {len(level_1_subs)} total)", "WARN")
                        else:
                            level_1_subs_to_search = sorted_level_1

                        self._log(f"Searching for level 2 subsidiaries (processing {len(level_1_subs_to_search)} entities)...", "INFO")

                    seen_names = set(sub['name'].lower() for sub in api_results['subsidiaries'])
                    seen_names_lock = Lock()

                    # Define wrapper function for parallel level 2 searches
                    def search_level_2_subsidiary(sub, idx, total):
                        """Wrapper function for parallel level 2 subsidiary search"""
                        try:
                            self._log(f"[{idx}/{total}] Searching level 2 for: {sub['name']}", "INFO")
                            level_2_results = self.find_related_companies_api(sub['name'])
                            return (sub, level_2_results, None)  # (input, results, error)
                        except Exception as e:
                            self._log(f"Error searching level 2 for {sub['name']}: {str(e)}", "ERROR")
                            return (sub, {'subsidiaries': [], 'sisters': [], 'parent': None}, str(e))

                    # Parallel execution with ThreadPoolExecutor
                    try:
                        max_parallel_searches = settings.MAX_PARALLEL_SUBSIDIARY_SEARCHES
                    except (NameError, AttributeError):
                        max_parallel_searches = 10  # Fallback if settings not available

                    max_workers = min(len(level_1_subs_to_search), max_parallel_searches)
                    self._log(f"Searching for level 2 subsidiaries (processing {len(level_1_subs_to_search)} entities with {max_workers} parallel workers)...", "INFO")

                    level_2_start_time = time.time()
                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        # Submit all tasks
                        future_to_sub = {
                            executor.submit(search_level_2_subsidiary, sub, idx, len(level_1_subs_to_search)): sub
                            for idx, sub in enumerate(level_1_subs_to_search, 1)
                        }

                        # Process results as they complete
                        for future in as_completed(future_to_sub):
                            sub_input, level_2_results, error = future.result()

                            if error:
                                self._log(f"Failed to search {sub_input['name']}: {error}", "WARN")
                                continue

                            if level_2_results['subsidiaries']:
                                for sub2 in level_2_results['subsidiaries']:
                                    # Thread-safe deduplication
                                    with seen_names_lock:
                                        if sub2['name'].lower() not in seen_names:
                                            sub2['level'] = 2
                                            sub2['relationship'] = 'subsidiary'
                                            api_results['subsidiaries'].append(sub2)
                                            seen_names.add(sub2['name'].lower())

                    level_2_duration = time.time() - level_2_start_time
                    self._log(f"✓ Found {len(api_results['subsidiaries']) - len(level_1_subs)} level 2 subsidiaries", "SUCCESS")
                    self._log(f"⏱️  Level 2 search completed in {level_2_duration:.2f} seconds (parallel execution with {max_workers} workers)", "INFO")

                if depth >= 3:
                    level_2_subs = [s for s in api_results['subsidiaries'] if s.get('level') == 2]

                    # Sort by ownership percentage and limit to prevent timeouts
                    sorted_level_2 = sorted(
                        level_2_subs,
                        key=lambda x: x.get('ownership_percentage', 0) or 0,
                        reverse=True
                    )

                    if len(sorted_level_2) > max_level_3_searches:
                        level_2_subs_to_search = sorted_level_2[:max_level_3_searches]
                        api_results.setdefault('warnings', []).append({
                            'source': 'level_3_search',
                            'message': f'Limited level 3 search to top {max_level_3_searches} level 2 subsidiaries by ownership (out of {len(level_2_subs)} total) to prevent timeout',
                            'severity': 'info'
                        })
                        self._log(f"⚠️  Limiting level 3 search to top {max_level_3_searches} level 2 subsidiaries by ownership (out of {len(level_2_subs)} total)", "WARN")
                    else:
                        level_2_subs_to_search = sorted_level_2

                    self._log(f"Searching for level 3 subsidiaries (processing {len(level_2_subs_to_search)} level 2 entities)...", "INFO")
                    seen_names = set(sub['name'].lower() for sub in api_results['subsidiaries'])
                    seen_names_lock = Lock()
                    original_count = len(api_results['subsidiaries'])

                    # Define wrapper function for parallel level 3 searches
                    def search_level_3_subsidiary(sub):
                        """Wrapper function for parallel level 3 subsidiary search"""
                        try:
                            level_3_results = self.find_related_companies_api(sub['name'])
                            return (sub, level_3_results, None)
                        except Exception as e:
                            self._log(f"Error searching level 3 for {sub['name']}: {str(e)}", "ERROR")
                            return (sub, {'subsidiaries': [], 'sisters': [], 'parent': None}, str(e))

                    # Parallel execution for level 3
                    try:
                        max_parallel_searches = settings.MAX_PARALLEL_SUBSIDIARY_SEARCHES
                    except (NameError, AttributeError):
                        max_parallel_searches = 10  # Fallback

                    max_workers = min(len(level_2_subs_to_search), max_parallel_searches)

                    level_3_start_time = time.time()
                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        future_to_sub = {
                            executor.submit(search_level_3_subsidiary, sub): sub
                            for sub in level_2_subs_to_search
                        }

                        for future in as_completed(future_to_sub):
                            sub_input, level_3_results, error = future.result()

                            if error:
                                self._log(f"Failed to search level 3 for {sub_input['name']}: {error}", "WARN")
                                continue

                            if level_3_results['subsidiaries']:
                                for sub3 in level_3_results['subsidiaries']:
                                    # Thread-safe deduplication
                                    with seen_names_lock:
                                        if sub3['name'].lower() not in seen_names:
                                            sub3['level'] = 3
                                            sub3['relationship'] = 'subsidiary'
                                            api_results['subsidiaries'].append(sub3)
                                            seen_names.add(sub3['name'].lower())

                    level_3_duration = time.time() - level_3_start_time
                    self._log(f"✓ Found {len(api_results['subsidiaries']) - original_count} level 3 subsidiaries", "SUCCESS")
                    self._log(f"⏱️  Level 3 search completed in {level_3_duration:.2f} seconds (parallel execution with {max_workers} workers)", "INFO")

                # Apply ownership filtering again after depth search
                if ownership_threshold > 0 and depth > 1:
                    original_count = len(api_results['subsidiaries'])
                    api_results['subsidiaries'] = self._filter_by_ownership(api_results['subsidiaries'], ownership_threshold)
                    filtered_count = original_count - len(api_results['subsidiaries'])
                    if filtered_count > 0:
                        self._log(f"Filtered out {filtered_count} level 2/3 subsidiaries not meeting {ownership_threshold}% ownership threshold", "INFO")

                self._log(f"✓ Total: {len(api_results['subsidiaries'])} subsidiaries across {depth} level(s)", "SUCCESS")
                api_results['data_sources_tried'] = data_sources_tried
                return api_results
            else:
                self._log("API returned no results or hit rate limit", "WARN")
        else:
            self._log("No OpenCorporates API key configured", "INFO")

        # Method 2: Try SEC EDGAR (best for US public companies)
        data_sources_tried.append('sec_edgar')
        self._log(f"Trying SEC EDGAR for {parent_company_name}...", "SEARCH")
        try:
            sec_results = self.find_subsidiaries_sec_edgar(parent_company_name)

            # If we got subsidiaries from SEC EDGAR (either 10-K or 20-F)
            if sec_results['method'] in ['sec_edgar_10k', 'sec_edgar_20f'] and sec_results['subsidiaries']:
                filing_type_display = "10-K" if sec_results['method'] == 'sec_edgar_10k' else "20-F"
                self._log(f"✓ SEC EDGAR found {len(sec_results['subsidiaries'])} level 1 subsidiaries via {filing_type_display}", "SUCCESS")

                # Store financial intelligence in database if available
                if sec_results.get('directors') or sec_results.get('shareholders') or sec_results.get('transactions'):
                    self._store_financial_intelligence(sec_results)

                # Apply ownership filtering
                if ownership_threshold > 0:
                    original_count = len(sec_results['subsidiaries'])
                    sec_results['subsidiaries'] = self._filter_by_ownership(sec_results['subsidiaries'], ownership_threshold)
                    filtered_count = original_count - len(sec_results['subsidiaries'])
                    if filtered_count > 0:
                        self._log(f"Filtered out {filtered_count} subsidiaries not meeting {ownership_threshold}% ownership threshold", "INFO")

                # Multi-level depth search if depth > 1
                if depth >= 2:
                    level_1_subs = list(sec_results['subsidiaries'])  # Save current level 1

                    # Filter to selected subsidiaries if specified
                    if depth_search_subsidiaries is not None:
                        level_1_subs_to_search = [sub for sub in level_1_subs if sub['name'] in depth_search_subsidiaries]
                        self._log(f"Searching level 2 for {len(level_1_subs_to_search)} selected subsidiaries (out of {len(level_1_subs)} total)", "INFO")
                    else:
                        level_1_subs_to_search = level_1_subs
                        self._log(f"Searching for level 2 subsidiaries (processing all {len(level_1_subs_to_search)} entities)...", "INFO")

                    seen_names = set(sub['name'].lower() for sub in sec_results['subsidiaries'])

                    for idx, sub in enumerate(level_1_subs_to_search, 1):
                        # Progress indicator
                        self._log(f"[{idx}/{len(level_1_subs_to_search)}] Searching level 2 for: {sub['name']}", "INFO")

                        # Search for subsidiaries of this subsidiary using DuckDuckGo
                        level_2_subs = self._search_subsidiaries_level(sub['name'], 2)
                        for sub2 in level_2_subs:
                            if sub2['name'].lower() not in seen_names:
                                sub2['relationship'] = 'subsidiary'
                                sec_results['subsidiaries'].append(sub2)
                                seen_names.add(sub2['name'].lower())

                    self._log(f"✓ Found {len(sec_results['subsidiaries']) - len(level_1_subs)} level 2 subsidiaries", "SUCCESS")

                if depth >= 3:
                    level_2_subs = [s for s in sec_results['subsidiaries'] if s.get('level') == 2]

                    # Filter to selected subsidiaries if specified
                    if depth_search_subsidiaries is not None:
                        level_2_subs_to_search = [sub for sub in level_2_subs if sub['name'] in depth_search_subsidiaries]
                        self._log(f"Searching level 3 for {len(level_2_subs_to_search)} selected subsidiaries (out of {len(level_2_subs)} total)", "INFO")
                    else:
                        level_2_subs_to_search = level_2_subs
                        self._log(f"Searching for level 3 subsidiaries (processing all {len(level_2_subs_to_search)} entities)...", "INFO")

                    seen_names = set(sub['name'].lower() for sub in sec_results['subsidiaries'])
                    original_count = len(sec_results['subsidiaries'])

                    for idx, sub in enumerate(level_2_subs_to_search, 1):
                        # Progress indicator
                        self._log(f"[{idx}/{len(level_2_subs_to_search)}] Searching level 3 for: {sub['name']}", "INFO")

                        # Search for subsidiaries of this level 2 subsidiary
                        level_3_subs = self._search_subsidiaries_level(sub['name'], 3)
                        for sub3 in level_3_subs:
                            if sub3['name'].lower() not in seen_names:
                                sub3['relationship'] = 'subsidiary'
                                sec_results['subsidiaries'].append(sub3)
                                seen_names.add(sub3['name'].lower())

                    self._log(f"✓ Found {len(sec_results['subsidiaries']) - original_count} level 3 subsidiaries", "SUCCESS")

                # Apply ownership filtering again after depth search
                if ownership_threshold > 0 and depth > 1:
                    original_count = len(sec_results['subsidiaries'])
                    sec_results['subsidiaries'] = self._filter_by_ownership(sec_results['subsidiaries'], ownership_threshold)
                    filtered_count = original_count - len(sec_results['subsidiaries'])
                    if filtered_count > 0:
                        self._log(f"Filtered out {filtered_count} level 2/3 subsidiaries not meeting {ownership_threshold}% ownership threshold", "INFO")

                # If sister companies are requested, search with DuckDuckGo
                if include_sisters:
                    self._log("SEC doesn't provide sister companies, searching with DuckDuckGo...", "INFO")
                    sisters = self._search_sister_companies(parent_company_name)

                    if sisters:
                        self._log(f"✓ DuckDuckGo found {len(sisters)} sister companies", "SUCCESS")
                        sec_results['sisters'] = sisters
                        # Preserve the filing type in the method name
                        sec_results['method'] = f"{sec_results['method']}+duckduckgo"

                # Search for parent company (SEC doesn't provide this, use web search)
                self._log("SEC doesn't provide parent companies, searching with DuckDuckGo...", "INFO")
                parent_company = self._search_parent_company(parent_company_name)
                if parent_company:
                    self._log(f"✓ Found parent company: {parent_company['name']}", "SUCCESS")
                    sec_results['parent'] = parent_company
                else:
                    self._log("No parent company found", "INFO")

                self._log(f"✓ Total: {len(sec_results['subsidiaries'])} subsidiaries across {depth} level(s)", "SUCCESS")
                sec_results['data_sources_tried'] = data_sources_tried
                return sec_results
            else:
                self._log("SEC EDGAR returned no results", "WARN")
        except Exception as e:
            self._log(f"SEC EDGAR failed: {str(e)}", "ERROR")

        # Method 3: Try Wikipedia (good for well-known companies)
        data_sources_tried.extend(['wikipedia', 'duckduckgo'])
        self._log(f"Trying Wikipedia for {parent_company_name}...", "SEARCH")
        wiki_results = self._search_wikipedia_subsidiaries(parent_company_name)
        wiki_subsidiaries = wiki_results.get('subsidiaries', [])
        wiki_sisters = wiki_results.get('sisters', [])

        # Method 4: Fall back to DuckDuckGo search (supplement Wikipedia)
        self._log(f"Using DuckDuckGo search for {parent_company_name}...", "SEARCH")
        subsidiaries = []
        seen_names = set()

        # Add Wikipedia results first
        for sub in wiki_subsidiaries:
            subsidiaries.append(sub)
            seen_names.add(sub['name'].lower())

        # Search for subsidiaries via DuckDuckGo (to supplement Wikipedia)
        self._log(f"Searching subsidiaries via DuckDuckGo...", "INFO")

        # Use the direct DuckDuckGo subsidiary search
        ddg_subs = self._search_subsidiaries_duckduckgo(parent_company_name)
        for sub in ddg_subs:
            if sub['name'].lower() not in seen_names:
                subsidiaries.append(sub)
                seen_names.add(sub['name'].lower())

        # Google search (greyb.com and other sources)
        self._log("Searching subsidiaries via Google...", "INFO")
        google_subs = self._search_google_subsidiaries(parent_company_name)
        if google_subs:
            self._log(f"Found {len(google_subs)} subsidiaries via Google", "SUCCESS")
            for sub in google_subs:
                if sub['name'].lower() not in seen_names:
                    subsidiaries.append(sub)
                    seen_names.add(sub['name'].lower())
            if 'google' not in data_sources_tried:
                data_sources_tried.append('google')

        # Also use the level-based search for deeper hierarchy
        level_1_subs = self._search_subsidiaries_level(parent_company_name, 1)
        for sub in level_1_subs:
            if sub['name'].lower() not in seen_names:
                sub['relationship'] = 'subsidiary'
                subsidiaries.append(sub)
                seen_names.add(sub['name'].lower())

        # Multi-level subsidiary search if depth > 1
        if depth >= 2:
            # Filter to selected subsidiaries if specified
            if depth_search_subsidiaries is not None:
                level_1_subs_to_search = [sub for sub in level_1_subs if sub['name'] in depth_search_subsidiaries]
                self._log(f"Searching level 2 for {len(level_1_subs_to_search)} selected subsidiaries (out of {len(level_1_subs)} total)", "INFO")
            else:
                level_1_subs_to_search = level_1_subs
                self._log(f"Searching level 2 subsidiaries (processing all {len(level_1_subs_to_search)} entities)...", "INFO")

            for idx, sub in enumerate(level_1_subs_to_search, 1):
                self._log(f"[{idx}/{len(level_1_subs_to_search)}] Searching level 2 for: {sub['name']}", "INFO")

                level_2_subs = self._search_subsidiaries_level(sub['name'], 2)
                for sub2 in level_2_subs:
                    if sub2['name'].lower() not in seen_names:
                        sub2['relationship'] = 'subsidiary'
                        subsidiaries.append(sub2)
                        seen_names.add(sub2['name'].lower())

        if depth >= 3:
            level_2_only = [s for s in subsidiaries if s['level'] == 2]

            # Filter to selected subsidiaries if specified
            if depth_search_subsidiaries is not None:
                level_2_to_search = [sub for sub in level_2_only if sub['name'] in depth_search_subsidiaries]
                self._log(f"Searching level 3 for {len(level_2_to_search)} selected subsidiaries (out of {len(level_2_only)} total)", "INFO")
            else:
                level_2_to_search = level_2_only
                self._log(f"Searching level 3 subsidiaries (processing all {len(level_2_to_search)} entities)...", "INFO")

            for idx, sub in enumerate(level_2_to_search, 1):
                self._log(f"[{idx}/{len(level_2_to_search)}] Searching level 3 for: {sub['name']}", "INFO")

                level_3_subs = self._search_subsidiaries_level(sub['name'], 3)
                for sub3 in level_3_subs:
                    if sub3['name'].lower() not in seen_names:
                        sub3['relationship'] = 'subsidiary'
                        subsidiaries.append(sub3)
                        seen_names.add(sub3['name'].lower())

        # Search for sister companies if requested
        sisters = []
        seen_sister_names = set()

        if include_sisters:
            # Add Wikipedia sister companies first
            for sister in wiki_sisters:
                sisters.append(sister)
                seen_sister_names.add(sister['name'].lower())

            # Supplement with DuckDuckGo
            self._log("Searching for sister companies via DuckDuckGo...", "INFO")
            ddg_sisters = self._search_sister_companies(parent_company_name)
            for sister in ddg_sisters:
                if sister['name'].lower() not in seen_sister_names:
                    sisters.append(sister)
                    seen_sister_names.add(sister['name'].lower())

        self._log(f"✓ Combined results: {len(subsidiaries)} subsidiaries, {len(sisters)} sister companies", "SUCCESS")

        # Filter subsidiaries based on ownership threshold
        if ownership_threshold > 0:
            original_count = len(subsidiaries)
            subsidiaries = self._filter_by_ownership(subsidiaries, ownership_threshold)
            filtered_count = original_count - len(subsidiaries)

            if filtered_count > 0:
                self._log(f"Filtered out {filtered_count} subsidiaries not meeting {ownership_threshold}% ownership threshold", "INFO")

        # Search for parent company
        self._log("Searching for parent company...", "INFO")
        parent_company = self._search_parent_company(parent_company_name)
        if parent_company:
            self._log(f"✓ Found parent company: {parent_company['name']}", "SUCCESS")
        else:
            self._log("No parent company found", "INFO")

        # Determine method label based on what found results
        sources = []
        if wiki_subsidiaries or wiki_sisters:
            sources.append('wikipedia')
        sources.append('duckduckgo')
        if 'google' in data_sources_tried:
            sources.append('google')
        method_label = '+'.join(sources)

        return {
            'subsidiaries': subsidiaries,
            'sisters': sisters,
            'parent': parent_company,
            'method': method_label,
            'source_url': None,  # Web search doesn't have a single source document
            'filing_date': None,
            'data_sources_tried': data_sources_tried
        }

    def _search_subsidiaries_level(self, company_name, level):
        """
        Search for direct subsidiaries of a company at a specific level.

        Args:
            company_name (str): Company name to search
            level (int): Hierarchy level (1, 2, or 3)

        Returns:
            list: List of subsidiary dictionaries
        """
        # Search OpenCorporates via DuckDuckGo
        query = f'site:opencorporates.com "{company_name}" subsidiaries OR subsidiary OR "controlled by"'

        try:
            results = self.ddgs.text(query, max_results=20)

            if not results:
                return []

            # Extract subsidiary information using LLM
            subsidiaries_text = ""
            for r in results:
                subsidiaries_text += f"Title: {r.get('title', '')}\n"
                subsidiaries_text += f"URL: {r.get('href', '')}\n"
                subsidiaries_text += f"Snippet: {r.get('body', '')}\n\n"

            # Use LLM to extract structured subsidiary list
            prompt = f"""
Analyze the following search results from OpenCorporates about "{company_name}".

Extract ONLY the LEGAL ENTITY NAMES of subsidiary companies.

CRITICAL RULES:
1. Extract ONLY the actual legal company name (e.g., "Company Entertainment Inc.", "Business Corp.")
2. DO NOT include descriptions, products, or services (e.g., NOT "Company subsidiary for Product X")
3. DO NOT include parent company references (e.g., NOT "Parent-backed subsidiary")
4. DO NOT include phrases like "subsidiary for", "developer of", "maker of"
5. If you cannot find a clear legal name, SKIP that entry entirely

For each subsidiary, provide:
- Legal entity name ONLY (e.g., "Company Name Inc.", "Company Ltd.")
- Jurisdiction (country/state if mentioned)
- Status (active/inactive if mentioned, otherwise "Unknown")
- Ownership percentage (if mentioned, otherwise "Unknown")
- Source URL (the exact URL from the search result where this company was mentioned)

Search Results:
{subsidiaries_text}

Output format (one per line):
LEGAL_ENTITY_NAME | JURISDICTION | STATUS | OWNERSHIP_PCT | SOURCE_URL

GOOD Examples (format only - these are NOT real companies):
XYZ Entertainment Inc. | United States | Active | 100 | https://opencorporates.com/companies/us/xyz123
ABC Technologies Oy | Finland | Active | Unknown | https://opencorporates.com/companies/fi/abc456
Tech Solutions Ltd. | Canada | Active | 51 | https://opencorporates.com/companies/ca/tech789

IMPORTANT: Always include the SOURCE_URL from the search results above. This is the URL where you found the information about each company.

BAD Examples (DO NOT output these):
Company subsidiary for Product | Canada | Active  ← WRONG: includes description
Parent-backed subsidiary | Canada | Active  ← WRONG: includes parent reference
Developer of products | United States | Active  ← WRONG: description not a company name

If no clear legal entity names are found, respond with "NO_SUBSIDIARIES_FOUND".
"""

            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1000
            )

            content = response.choices[0].message.content.strip()

            if "NO_SUBSIDIARIES_FOUND" in content:
                return []

            # Parse LLM response with validation
            subsidiaries = []
            for line in content.split('\n'):
                line = line.strip()
                if not line or '|' not in line:
                    continue

                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3:
                    company_name = parts[0]

                    # Validate that it looks like a company name, not a description
                    if self._validate_company_name(company_name):
                        # Parse ownership percentage if provided
                        ownership_pct = None
                        if len(parts) >= 4:
                            ownership_str = parts[3].lower()
                            if ownership_str != 'unknown' and ownership_str != '':
                                try:
                                    ownership_pct = float(ownership_str.replace('%', '').strip())
                                except ValueError:
                                    pass

                        # Parse source URL if provided
                        source_url = None
                        if len(parts) >= 5:
                            url = parts[4].strip()
                            if url and url.startswith('http'):
                                source_url = url

                        subsidiaries.append({
                            'name': company_name,
                            'jurisdiction': parts[1],
                            'status': parts[2],
                            'level': level,
                            'relationship': 'subsidiary',
                            'source': 'duckduckgo',
                            'ownership_percentage': ownership_pct,
                            'reference_url': source_url
                        })
                    else:
                        self._log(f"Filtered out invalid entry: '{company_name}'", "INFO")

            return subsidiaries

        except Exception as e:
            print(f"Error searching subsidiaries for {company_name}: {e}")
            return []