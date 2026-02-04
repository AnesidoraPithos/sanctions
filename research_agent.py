import os
import time
import re
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
                        "snippet": snippet
                    })
                
                # Stop after finding 3 verified good links to save time
                if len(verified_hits) >= 3:
                    break
            
            return verified_hits
                
        except Exception as e:
            print(f"Sanction news search failed: {e}")
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