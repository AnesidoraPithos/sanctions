import requests
import os
import json

class USASanctionsAgent:
    API_URL = "https://data.trade.gov/consolidated_screening_list/v1/search"
    
    def __init__(self):
        self.API_KEY = os.getenv('USA_TRADE_GOV_API_KEY')

    def search(self, search_params):
        """
        Fetches ALL results by handling pagination automatically.
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
                        formatted_batch = self._format_results(results)
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

    def _format_results(self, results):
        formatted = []
        for r in results:
            addresses = r.get('addresses', [])
            first_addr = addresses[0].get('address') if addresses else "N/A"
            city = addresses[0].get('city') if addresses else ""
            country = addresses[0].get('country') if addresses else ""
            
            full_loc = f"{first_addr}, {city} ({country})"
            
            formatted.append({
                "Score": r.get('score', 'N/A'),
                "Name": r.get('name'),
                "List": r.get('source', 'USA'),
                "Type": r.get('type', 'Entity'),
                "Address": full_loc,
                "Remark": r.get('remarks') or r.get('federal_register_notice', 'See official link'),
                "Link": r.get('source_list_url')
            })
        return formatted