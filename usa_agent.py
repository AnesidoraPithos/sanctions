import requests
import os
import json
from matching_utils import calculate_similarity_scores, get_composite_score, classify_match_quality, combine_scores

class USASanctionsAgent:
    API_URL = "https://data.trade.gov/consolidated_screening_list/v1/search"
    
    def __init__(self):
        self.API_KEY = os.getenv('USA_TRADE_GOV_API_KEY')

    def search(self, search_params, query_name=None):
        """
        Fetches ALL results by handling pagination automatically.

        Args:
            search_params (dict): API search parameters
            query_name (str, optional): Original query name for local fuzzy matching
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
                            
                        # Prepare for next page
                        offset += batch_size
                        
                    except json.JSONDecodeError:
                        return [{"error": "API returned invalid JSON."}]
                elif response.status_code == 401:
                    return [{"error": "401 Unauthorized: API Key rejected."}]
                else:
                    return [{"error": f"API Error {response.status_code}"}]
            
            if not all_results:
                return []
                
            return all_results

        except Exception as e:
            return [{"error": f"Connection failed: {str(e)}"}]

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
            addresses = r.get('addresses', [])
            first_addr = addresses[0].get('address') if addresses else "N/A"
            city = addresses[0].get('city') if addresses else ""
            country = addresses[0].get('country') if addresses else ""

            full_loc = f"{first_addr}, {city} ({country})"

            # Get API score
            api_score = float(r.get('score', 0))

            # Calculate local similarity if query_name provided
            if query_name:
                result_name = r.get('name', '')
                try:
                    local_score = get_composite_score(query_name, result_name)
                    combined_score = combine_scores(api_score, local_score)
                    match_quality = classify_match_quality(combined_score)
                    similarity_breakdown = calculate_similarity_scores(query_name, result_name)
                except Exception as e:
                    # Fallback to API score only if local scoring fails
                    local_score = api_score
                    combined_score = api_score
                    match_quality = "EXACT" if api_score >= 100 else "HIGH" if api_score >= 90 else "MEDIUM"
                    similarity_breakdown = {}
            else:
                # Fallback to API score only if no query_name provided
                local_score = api_score
                combined_score = api_score
                match_quality = "EXACT" if api_score >= 100 else "HIGH" if api_score >= 90 else "MEDIUM"
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
        return formatted