import os
import time
import re
import requests
from openai import OpenAI
from fpdf import FPDF

# Handle DDGS import
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

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
            'User-Agent': 'SanctionsScreeningTool/1.0 (Business Intelligence; contact@example.com)',  # SEC requires descriptive user agent
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
            f"{entity_name} official press release 2024 2025",
            f"{entity_name} major business partners collaborations"
        ]
        
        evidence_text = self._search_web(search_queries)

        prompt = f"""
        You are a Senior Intelligence Analyst. Produce a formal "Due Diligence Intelligence Report" on the entity: "{entity_name}".
        
        Use the following retrieved information as your ONLY source of evidence:
        {evidence_text}
        
        ---
        REPORT REQUIREMENTS:
        1. **Tone**: Professional, objective, and formal.
        2. **Structure**:
           - **Executive Summary**: High-level risk assessment.
           - **Regulatory & Legal Status**: Details on investigations, lawsuits, or sanctions risks (US focus).
           - **Political Activity**: Lobbying efforts or legislative scrutiny.
           - **Recent Developments**: Key press releases or news from the last 2 years.
           - **Collaborations**: Known partners (to assess 2nd order risk).
        3. **Citations**: You MUST cite the source URL for every factual claim using brackets, e.g. [Source: example.com].
        
        Do not output preambles. Start directly with the report title.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": "You are a professional intelligence analyst. Output in Markdown."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
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

        Args:
            company_name (str): Company name to search

        Returns:
            str or None: CIK number if found, None otherwise
        """
        try:
            # Use SEC's search API endpoint
            # Note: SEC requires specific user agent and rate limiting
            time.sleep(0.1)  # Rate limit: max 10 requests/second

            # Try the company tickers endpoint (correct URL)
            url = "https://www.sec.gov/files/company_tickers.json"
            response = requests.get(url, headers=self.sec_headers, timeout=10)
            response.raise_for_status()

            companies = response.json()

            # Search for company by name (case-insensitive)
            company_lower = company_name.lower()
            best_match = None
            best_match_score = 0

            for key, company_data in companies.items():
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

            self._log(f"No CIK found for {company_name}", "WARN")
            return None

        except Exception as e:
            self._log(f"Error searching for CIK: {e}", "ERROR")
            return None

    def get_latest_10k_filing(self, cik):
        """
        Get the latest 10-K filing for a company using SEC EDGAR search.

        Args:
            cik (str): Company's CIK number (10 digits with leading zeros)

        Returns:
            dict or None: Filing data with accession number and filing URL
        """
        try:
            # Rate limit
            time.sleep(0.1)

            # Remove leading zeros for CIK integer
            cik_int = str(int(cik))

            # Search for 10-K filings using SEC EDGAR full-text search
            # This is more reliable than the submissions endpoint
            search_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik_int}&type=10-K&dateb=&owner=exclude&count=10&search_text="

            self._log(f"Searching for 10-K filings...", "INFO")

            response = requests.get(search_url, headers=self.sec_headers, timeout=15)
            response.raise_for_status()

            html_content = response.text

            # Parse HTML to find 10-K filings
            import re

            # Look for document viewer links in the format:
            # /cgi-bin/viewer?action=view&cik=XXXXX&accession_number=XXXXXXXXXX-XX-XXXXXX&xbrl_type=v
            pattern = r'documentsbutton.*?href="([^"]+)"'
            doc_matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)

            if not doc_matches:
                self._log(f"No 10-K filings found for CIK {cik}", "WARN")
                return None

            # Get the first (most recent) 10-K filing
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

            self._log(f"Found 10-K filing from {filing_date}", "SUCCESS")

            return {
                'accession': accession_no_hyphens,
                'accession_formatted': accession_with_hyphens,
                'filing_date': filing_date,
                'cik': cik
            }

        except Exception as e:
            self._log(f"Error getting 10-K filing: {e}", "ERROR")
            return None

    def extract_subsidiaries_from_10k(self, filing_data):
        """
        Extract subsidiaries from 10-K filing's Exhibit 21.

        Args:
            filing_data (dict): Filing data from get_latest_10k_filing()

        Returns:
            list: List of subsidiary dictionaries
        """
        subsidiaries = []

        try:
            # Remove leading zeros from CIK for URL
            cik = filing_data['cik']
            cik_int = str(int(cik))
            accession = filing_data['accession']
            accession_formatted = filing_data['accession_formatted']

            # Rate limit
            time.sleep(0.1)

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
                    return []

            # Look for Exhibit 21 document in the index
            content = response.text
            exhibit_21_doc = None

            # Search for Exhibit 21 links using regex
            import re

            # Pattern to find exhibit 21 references
            ex21_patterns = [
                r'href="([^"]*ex-?21[^"]*\.htm[l]?)"',
                r'href="([^"]*ex-?21[^"]*)"',
                r'href="([^"]*exhibit-?21[^"]*)"'
            ]

            for pattern in ex21_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    exhibit_21_doc = match.group(1)
                    break

            if not exhibit_21_doc:
                self._log("Could not find Exhibit 21 in filing", "WARN")
                return []

            # Fetch Exhibit 21 document
            if exhibit_21_doc.startswith('http'):
                exhibit_url = exhibit_21_doc
            else:
                exhibit_url = f"https://www.sec.gov{exhibit_21_doc}" if exhibit_21_doc.startswith('/') else f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession}/{exhibit_21_doc}"

            self._log(f"Found Exhibit 21, downloading document...", "SUCCESS")

            time.sleep(0.1)  # Rate limit
            exhibit_response = requests.get(exhibit_url, headers=self.sec_headers, timeout=15)
            exhibit_response.raise_for_status()

            exhibit_text = exhibit_response.text

            # Strip HTML tags to get cleaner text for LLM
            import re
            # Remove HTML tags but keep the text content
            text_only = re.sub(r'<[^>]+>', ' ', exhibit_text)
            # Remove extra whitespace
            text_only = re.sub(r'\s+', ' ', text_only)
            # Remove common HTML entities
            text_only = text_only.replace('&nbsp;', ' ').replace('&amp;', '&')

            # For very long documents, we'll process in chunks
            # Most Exhibit 21s are 50-500 subsidiaries
            max_chars = 50000  # Increased from 8000 to handle large companies
            text_chunk = text_only[:max_chars]

            self._log(f"Parsing Exhibit 21 with LLM ({len(text_only)} chars)...", "INFO")

            prompt = f"""
Extract ALL subsidiary companies from this SEC Exhibit 21 document.

Exhibit 21 lists subsidiaries of a company. Extract each subsidiary with:
- Company name (full legal name)
- Jurisdiction of incorporation (state/country)

IMPORTANT: This may be a long list. Extract EVERY subsidiary mentioned, even if there are hundreds.

Document content:
{text_chunk}

Output format (one per line):
COMPANY_NAME | JURISDICTION

Example:
Apple Retail Holdings, LLC | Nevada
Apple Operations International | Ireland

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
                self._log("No subsidiaries found in Exhibit 21", "WARN")
                return []

            # Parse LLM response
            for line in content.split('\n'):
                line = line.strip()
                if not line or '|' not in line:
                    continue

                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 2:
                    subsidiaries.append({
                        'name': parts[0],
                        'jurisdiction': parts[1],
                        'status': 'Active',
                        'relationship': 'subsidiary',
                        'level': 1,
                        'source': 'sec_edgar'
                    })

            self._log(f"Extracted {len(subsidiaries)} subsidiaries from Exhibit 21", "SUCCESS")

            # Return both subsidiaries and the source URL
            return {
                'subsidiaries': subsidiaries,
                'exhibit_21_url': exhibit_url,
                'filing_date': filing_data.get('filing_date', 'Unknown')
            }

        except Exception as e:
            self._log(f"Error extracting subsidiaries: {e}", "ERROR")
            return {'subsidiaries': [], 'exhibit_21_url': None, 'filing_date': None}

    def find_subsidiaries_sec_edgar(self, company_name):
        """
        Find subsidiaries using SEC EDGAR 10-K filings (US public companies only).

        Args:
            company_name (str): Company name to search

        Returns:
            dict: {
                'subsidiaries': [list of subsidiary dicts],
                'sisters': [],  # SEC doesn't provide sister companies
                'parent': None,
                'method': 'sec_edgar'
            }
        """
        print(f"[SEC EDGAR] Searching for {company_name}...")

        # Step 1: Find CIK
        cik = self.search_sec_edgar_cik(company_name)
        if not cik:
            return {'subsidiaries': [], 'sisters': [], 'parent': None, 'method': 'none', 'source_url': None, 'filing_date': None}

        # Step 2: Get latest 10-K filing
        filing_data = self.get_latest_10k_filing(cik)
        if not filing_data:
            return {'subsidiaries': [], 'sisters': [], 'parent': None, 'method': 'none', 'source_url': None, 'filing_date': None}

        # Step 3: Extract subsidiaries from Exhibit 21
        extraction_result = self.extract_subsidiaries_from_10k(filing_data)

        subsidiaries = extraction_result.get('subsidiaries', [])
        exhibit_url = extraction_result.get('exhibit_21_url')
        filing_date = extraction_result.get('filing_date')

        if not subsidiaries:
            return {'subsidiaries': [], 'sisters': [], 'parent': None, 'method': 'none', 'source_url': None, 'filing_date': None}

        return {
            'subsidiaries': subsidiaries,
            'sisters': [],  # SEC EDGAR doesn't provide sister companies
            'parent': None,
            'method': 'sec_edgar',
            'source_url': exhibit_url,  # Link to Exhibit 21
            'filing_date': filing_date
        }

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

Extract SISTER COMPANIES only. Sister companies are companies that share the SAME PARENT COMPANY with "{company_name}".

DO NOT include:
- "{company_name}" itself
- Subsidiaries of "{company_name}" (companies owned BY "{company_name}")
- The parent company itself

For each sister company found, provide:
- Company name (full legal name)
- Jurisdiction (country/state if mentioned)
- Status (always mark as "Sister Company")

Search Results:
{text_data}

Output format (one per line):
COMPANY_NAME | JURISDICTION | Sister Company

Example:
Huawei Technologies USA | United States | Sister Company
Huawei Device Co., Ltd. | China | Sister Company

If no sister companies are clearly identified, respond with "NO_SISTERS_FOUND".
Be conservative - only extract entities clearly identified as sister companies or co-subsidiaries.
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

            # Parse LLM response
            sisters = []
            for line in content.split('\n'):
                line = line.strip()
                if not line or '|' not in line:
                    continue

                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3:
                    sisters.append({
                        'name': parts[0],
                        'jurisdiction': parts[1],
                        'status': parts[2],
                        'relationship': 'sister',
                        'level': 0,
                        'source': 'duckduckgo'
                    })

            return sisters

        except Exception as e:
            self._log(f"Error searching sister companies via DuckDuckGo: {e}", "ERROR")
            return []

    def find_subsidiaries(self, parent_company_name, depth=1, include_sisters=True, progress_callback=None):
        """
        Search for subsidiaries and optionally sister companies.
        Tries OpenCorporates API first, then SEC EDGAR, finally DuckDuckGo.

        Args:
            parent_company_name (str): Name of the parent/target company
            depth (int): Search depth for subsidiaries (1-3 levels)
            include_sisters (bool): Whether to also search for sister companies
            progress_callback (callable): Optional callback for progress updates

        Returns:
            dict: {
                'subsidiaries': [...],
                'sisters': [...],
                'parent': {...} or None,
                'method': 'api' or 'sec_edgar' or 'duckduckgo'
            }
        """
        # Set callback for this search
        self.progress_callback = progress_callback

        # Method 1: Try OpenCorporates API (preferred - fastest & most accurate for international companies)
        if self.opencorporates_api_key:
            self._log(f"Trying OpenCorporates API for {parent_company_name}...", "SEARCH")
            api_results = self.find_related_companies_api(parent_company_name)

            # If we got results from API, return them
            if api_results['method'] == 'api' and (api_results['subsidiaries'] or api_results['sisters']):
                self._log(f"✓ API found {len(api_results['subsidiaries'])} subsidiaries, {len(api_results['sisters'])} sister companies", "SUCCESS")
                return api_results
            else:
                self._log("API returned no results or hit rate limit", "WARN")
        else:
            self._log("No OpenCorporates API key configured", "INFO")

        # Method 2: Try SEC EDGAR (best for US public companies)
        self._log(f"Trying SEC EDGAR for {parent_company_name}...", "SEARCH")
        try:
            sec_results = self.find_subsidiaries_sec_edgar(parent_company_name)

            # If we got subsidiaries from SEC EDGAR
            if sec_results['method'] == 'sec_edgar' and sec_results['subsidiaries']:
                self._log(f"✓ SEC EDGAR found {len(sec_results['subsidiaries'])} subsidiaries", "SUCCESS")

                # If sister companies are NOT requested, return SEC results
                if not include_sisters:
                    return sec_results

                # If sister companies ARE requested, try to supplement with DuckDuckGo for sisters
                self._log("SEC doesn't provide sister companies, searching with DuckDuckGo...", "INFO")
                sisters = self._search_sister_companies(parent_company_name)

                if sisters:
                    self._log(f"✓ DuckDuckGo found {len(sisters)} sister companies", "SUCCESS")
                    sec_results['sisters'] = sisters
                    sec_results['method'] = 'sec_edgar+duckduckgo'

                return sec_results
            else:
                self._log("SEC EDGAR returned no results", "WARN")
        except Exception as e:
            self._log(f"SEC EDGAR failed: {str(e)}", "ERROR")

        # Method 3: Fall back to DuckDuckGo search
        self._log(f"Using DuckDuckGo search for {parent_company_name}...", "SEARCH")
        subsidiaries = []
        seen_names = set()

        # Search for subsidiaries (existing logic)
        self._log(f"Searching level 1 subsidiaries via DuckDuckGo...", "INFO")
        level_1_subs = self._search_subsidiaries_level(parent_company_name, 1)
        for sub in level_1_subs:
            sub['relationship'] = 'subsidiary'
            subsidiaries.append(sub)
            seen_names.add(sub['name'].lower())

        # Multi-level subsidiary search if depth > 1
        if depth >= 2:
            self._log(f"Searching level 2 subsidiaries...", "INFO")
            for sub in level_1_subs:
                level_2_subs = self._search_subsidiaries_level(sub['name'], 2)
                for sub2 in level_2_subs:
                    if sub2['name'].lower() not in seen_names:
                        sub2['relationship'] = 'subsidiary'
                        subsidiaries.append(sub2)
                        seen_names.add(sub2['name'].lower())

        if depth >= 3:
            self._log(f"Searching level 3 subsidiaries...", "INFO")
            level_2_only = [s for s in subsidiaries if s['level'] == 2]
            for sub in level_2_only:
                level_3_subs = self._search_subsidiaries_level(sub['name'], 3)
                for sub3 in level_3_subs:
                    if sub3['name'].lower() not in seen_names:
                        sub3['relationship'] = 'subsidiary'
                        subsidiaries.append(sub3)
                        seen_names.add(sub3['name'].lower())

        # Search for sister companies if requested
        sisters = []
        if include_sisters:
            self._log("Searching for sister companies via DuckDuckGo...", "INFO")
            sisters = self._search_sister_companies(parent_company_name)

        self._log(f"✓ DuckDuckGo found {len(subsidiaries)} subsidiaries, {len(sisters)} sister companies", "SUCCESS")

        return {
            'subsidiaries': subsidiaries,
            'sisters': sisters,
            'parent': None,
            'method': 'duckduckgo',
            'source_url': None,  # DuckDuckGo doesn't have a single source document
            'filing_date': None
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

Extract ALL subsidiary companies mentioned. For each subsidiary, provide:
- Company name (full legal name)
- Jurisdiction (country/state if mentioned)
- Status (active/inactive if mentioned, otherwise "Unknown")

Search Results:
{subsidiaries_text}

Output format (one per line):
COMPANY_NAME | JURISDICTION | STATUS

Example:
Huawei Technologies Canada Co., Ltd. | Canada | Active
Huawei Device Co., Ltd. | China | Active

If no clear subsidiaries are found, respond with "NO_SUBSIDIARIES_FOUND".
Extract ONLY entities clearly identified as subsidiaries, controlled companies, or affiliates.
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

            # Parse LLM response
            subsidiaries = []
            for line in content.split('\n'):
                line = line.strip()
                if not line or '|' not in line:
                    continue

                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3:
                    subsidiaries.append({
                        'name': parts[0],
                        'jurisdiction': parts[1],
                        'status': parts[2],
                        'level': level,
                        'relationship': 'subsidiary',
                        'source': 'duckduckgo'
                    })

            return subsidiaries

        except Exception as e:
            print(f"Error searching subsidiaries for {company_name}: {e}")
            return []