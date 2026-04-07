import logging
import requests
import os
import json
from matching_utils import calculate_similarity_scores, get_composite_score, classify_match_quality, combine_scores

logger = logging.getLogger(__name__)

class USASanctionsAgent:
    API_URL = "https://data.trade.gov/consolidated_screening_list/v1/search"
    
    def __init__(self):
        self.API_KEY = os.getenv('USA_TRADE_GOV_API_KEY')

    def search(self, search_params, query_name=None, score_threshold=0):
        """
        Fetches ALL results by handling pagination automatically.
        Now also searches local database for external sources.

        Args:
            search_params (dict): API search parameters
            query_name (str, optional): Original query name for local fuzzy matching
            score_threshold (int): Stop fetching when API batch scores drop below this value
        """
        # 1. Query API (existing logic)
        api_results = self._search_api(search_params, query_name, score_threshold)

        # 2. Query local database (new logic)
        local_results = []
        if query_name:
            local_results = self._search_local_db(query_name)

        # 3. Merge results
        all_results = api_results + local_results

        # 4. Sort by combined_score (descending) - ensures best matches appear first
        # Filter out error results before sorting
        valid_results = [r for r in all_results if 'error' not in r]
        error_results = [r for r in all_results if 'error' in r]

        if valid_results:
            valid_results.sort(key=lambda x: x.get('combined_score', 0), reverse=True)

        return valid_results + error_results  # Errors at the end

    def _search_api(self, search_params, query_name=None, score_threshold=0):
        """
        Search USA Trade API with pagination.

        Args:
            search_params (dict): API search parameters
            query_name (str, optional): Original query name for local fuzzy matching

        Returns:
            list: Formatted API results
        """
        if not self.API_KEY:
            return [{"error": "Missing API Key. Check your .env file."}]

        # 1. Clean parameters (remove empty values)
        # We use 'v is not None' to ensure we don't accidentally remove offset=0
        clean_params = {k: v for k, v in search_params.items() if v}

        if "fuzzy_name" not in clean_params:
            clean_params["fuzzy_name"] = "true"

        headers = {
            'Cache-Control': 'no-cache',
            'subscription-key': self.API_KEY,
            'User-Agent': 'SanctionsDashboard/1.0'
        }

        all_results = []
        offset = 0
        batch_size = 50  # API Max is 50

        # Safety break to prevent infinite loops (e.g., if API breaks)
        max_limit = 2000

        try:
            while True:
                # Update pagination parameters for this batch
                current_params = clean_params.copy()
                current_params['size'] = batch_size
                current_params['offset'] = offset

                # Make the request
                response = requests.get(self.API_URL, params=current_params, headers=headers, timeout=15)

                if response.status_code == 200:
                    try:
                        data = response.json()
                        results = data.get('results', [])
                        total_matches = data.get('total', 0)
                        # Add this batch to our master list
                        formatted_batch = self._format_results(results, query_name)
                        all_results.extend(formatted_batch)

                        # LOGIC: Should we stop?
                        # 1. If we have fetched everything available
                        if len(all_results) >= total_matches:
                            break
                        # 2. If the API returned fewer results than requested (end of list)
                        if len(results) < batch_size:
                            break
                        # 3. Safety break
                        if len(all_results) >= max_limit:
                            break
                        # 4. Early termination: API results are sorted by score descending.
                        # Once the lowest score in a batch drops below the threshold,
                        # all subsequent pages will also be below it and get filtered out.
                        if score_threshold > 0 and results:
                            min_batch_score = min(float(r.get('score') or 0) for r in results)
                            if min_batch_score < score_threshold:
                                break

                        # Prepare for next page
                        offset += batch_size

                    except json.JSONDecodeError:
                        return [{"error": "API returned invalid JSON."}]
                elif response.status_code == 401:
                    return [{"error": "401 Unauthorized: API Key rejected."}]
                else:
                    if all_results:
                        break  # pagination limit hit; return what we have
                    return [{"error": f"API Error {response.status_code}"}]

            if not all_results:
                return []

            return all_results

        except Exception as e:
            if all_results:
                return all_results
            return [{"error": f"Connection failed: {str(e)}"}]

    def _search_local_db(self, query_name):
        """
        Search local entities using fuzzy matching.

        This searches entities from external sources:
        - DOD Section 1260H (Chinese Military Companies)
        - FCC Covered List (Equipment/Services)

        Enhanced matching: Also checks abbreviated names in parentheses
        (e.g., "Huawei" matches "Huawei Technologies Co., Ltd. (Huawei)")

        Args:
            query_name (str): Search query

        Returns:
            list: Formatted results (same structure as API results)
        """
        from database import search_local_entities
        import re

        # Get all local entities
        entities = search_local_entities(query_name)

        if not entities:
            return []

        # Apply fuzzy matching and format results
        formatted = []
        for entity in entities:
            entity_full_name = entity['name']

            # Calculate score for full name
            local_score = get_composite_score(query_name, entity_full_name)

            # ENHANCEMENT 1: Also check abbreviated name in parentheses
            # Extract text in parentheses (e.g., "Company Ltd. (ABBREV)" -> "ABBREV")
            parenthetical_match = re.search(r'\(([^)]+)\)$', entity_full_name)
            if parenthetical_match:
                abbreviated_name = parenthetical_match.group(1)
                # Calculate score for abbreviated name
                abbrev_score = get_composite_score(query_name, abbreviated_name)
                # Use the better score
                if abbrev_score > local_score:
                    local_score = abbrev_score

            # ENHANCEMENT 2: Also try with legal suffixes stripped
            # This helps match "Autel Robotics" against "Autel Robotics Co., Ltd"
            LEGAL_SUFFIXES = [
                'Co., Ltd', 'Co., Ltd.', 'Co. Ltd', 'Co. Ltd.',
                'Company Limited', 'Company Ltd', 'Company Ltd.',
                'Inc', 'Inc.', 'Incorporated',
                'Corp', 'Corp.', 'Corporation',
                'Limited', 'Ltd', 'Ltd.',
                'LLC', 'L.L.C.'
            ]

            # Extract base name (before parentheses if they exist)
            entity_base = entity_full_name
            if parenthetical_match:
                entity_base = entity_full_name[:parenthetical_match.start()].strip()

            # Strip legal suffix from base name
            for suffix in LEGAL_SUFFIXES:
                if entity_base.endswith(suffix):
                    entity_base = entity_base[:-len(suffix)].strip()
                    break

            # Calculate score for base name (without legal suffix)
            base_score = get_composite_score(query_name, entity_base)
            # Use the better score (max of full name, abbreviated name, or base name)
            local_score = max(local_score, base_score)

            # Only include results above a minimum threshold to reduce noise
            # Using 60 as minimum threshold (below "medium" but catches fuzzy matches)
            if local_score < 60:
                continue

            # Classify match quality based on local score
            match_quality = classify_match_quality(local_score)

            # Format to match API result structure
            formatted.append({
                "Score": local_score,  # Keep for backward compatibility
                "api_score": None,  # No API score for local entities
                "local_score": local_score,
                "combined_score": local_score,  # Same as local (no API component)
                "match_quality": match_quality,
                "similarity_breakdown": calculate_similarity_scores(query_name, entity_full_name),
                "Name": entity['name'],
                "List": entity['source_list'],
                "Type": entity['entity_type'],
                "Address": "N/A",
                "Remark": entity['additional_info'] if entity['additional_info'] else "Local Database Entry",
                "Link": entity['source_url']
            })

        return formatted

    def _format_results(self, results, query_name=None):
        """
        Format API results with enhanced scoring information.

        Args:
            results (list): Raw results from API
            query_name (str, optional): Original query name for local fuzzy matching

        Returns:
            list: Formatted results with scoring information
        """
        formatted = []
        for r in results:
            try:
                addresses = r.get('addresses', [])
                addr_0 = next((a for a in addresses if isinstance(a, dict)), {})
                first_addr = addr_0.get('address') or 'N/A'
                city = addr_0.get('city', '')
                country = addr_0.get('country', '')

                full_loc = f"{first_addr}, {city} ({country})"

                # Get API score
                api_score = float(r.get('score') or 0)

                # Calculate local similarity if query_name provided
                if query_name:
                    result_name = r.get('name', '') or ''
                    try:
                        local_score = get_composite_score(query_name, result_name)
                        for alt_name in (r.get('alt_names') or []):
                            if alt_name:
                                alt_score = get_composite_score(query_name, alt_name)
                                local_score = max(local_score, alt_score)
                        combined_score = combine_scores(api_score, local_score)
                        match_quality = classify_match_quality(combined_score)
                        similarity_breakdown = calculate_similarity_scores(query_name, result_name)
                    except Exception:
                        # Fallback to API score only if local scoring fails
                        logger.warning("Local scoring failed for %r; falling back to API score", result_name, exc_info=True)
                        local_score = api_score
                        combined_score = api_score
                        match_quality = classify_match_quality(api_score)
                        similarity_breakdown = {}
                else:
                    # No query_name provided; use API score directly
                    local_score = api_score
                    combined_score = api_score
                    match_quality = classify_match_quality(api_score)
                    similarity_breakdown = {}

                formatted.append({
                    "Score": api_score,  # Keep original for backward compatibility
                    "api_score": api_score,  # New: explicit API score
                    "local_score": local_score,  # New: local fuzzy score
                    "combined_score": combined_score,  # New: weighted combination
                    "match_quality": match_quality,  # New: EXACT/HIGH/MEDIUM/LOW
                    "similarity_breakdown": similarity_breakdown,  # New: detailed algorithm scores
                    "Name": r.get('name'),
                    "List": r.get('source', 'USA'),
                    "Type": r.get('type', 'Entity'),
                    "Address": full_loc,
                    "Remark": r.get('remarks') or r.get('federal_register_notice', 'See official link'),
                    "Link": r.get('source_list_url')
                })
            except Exception:
                logger.warning("Skipping malformed result entry: %r", r, exc_info=True)
                continue
        return formatted