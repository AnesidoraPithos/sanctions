"""
Serialization utilities for saving and loading complex search results.

This module handles the conversion of search data structures (including DataFrames,
binary data, and nested dictionaries) into JSON-serializable formats for database storage.
"""

import json
import base64
from datetime import datetime
from typing import Dict, Any, Optional


def serialize_search_results(results_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert complex search results into database-serializable format.

    Args:
        results_data: Dictionary containing:
            - us_results: List of sanctions matches
            - media_hits: List of media/OSINT hits
            - report: Intelligence report text
            - pdf_bytes: PDF binary data
            - conglomerate_data: Optional conglomerate search data

    Returns:
        Dictionary with serialized fields ready for database storage
    """
    serialized = {}

    # Sanctions data (already JSON-serializable lists)
    if 'us_results' in results_data and results_data['us_results']:
        serialized['sanctions_data'] = json.dumps(results_data['us_results'])
    else:
        serialized['sanctions_data'] = None

    # Media data
    if 'media_hits' in results_data and results_data['media_hits']:
        serialized['media_data'] = json.dumps(results_data['media_hits'])
    else:
        serialized['media_data'] = None

    # Report text
    if 'report' in results_data and results_data['report']:
        serialized['report_text'] = results_data['report']
    else:
        serialized['report_text'] = None

    # PDF bytes (stored as-is, SQLite handles BLOB type)
    if 'pdf_bytes' in results_data and results_data['pdf_bytes']:
        serialized['pdf_data'] = results_data['pdf_bytes']
    else:
        serialized['pdf_data'] = None

    # Conglomerate data (complex nested structure)
    if 'conglomerate_data' in results_data and results_data['conglomerate_data']:
        conglom = results_data['conglomerate_data']
        # Ensure all fields are JSON-serializable
        serializable_conglom = {
            'subsidiaries': conglom.get('subsidiaries', []),
            'sisters': conglom.get('sisters', []),
            'method': conglom.get('method', 'unknown'),
            'source_url': conglom.get('source_url'),
            'filing_date': conglom.get('filing_date'),
            'is_reverse_search': conglom.get('is_reverse_search', False),
            'directors': conglom.get('directors', []),
            'shareholders': conglom.get('shareholders', []),
            'transactions': conglom.get('transactions', [])
        }
        serialized['conglomerate_data'] = json.dumps(serializable_conglom)
    else:
        serialized['conglomerate_data'] = None

    return serialized


def deserialize_search_results(db_row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert database row back into original data structures.

    Args:
        db_row: Dictionary with database fields (from cursor.fetchone() with row_factory)

    Returns:
        Dictionary with deserialized search results
    """
    results = {}

    # Parse JSON fields
    if db_row.get('sanctions_data'):
        try:
            results['us_results'] = json.loads(db_row['sanctions_data'])
        except json.JSONDecodeError:
            results['us_results'] = []
    else:
        results['us_results'] = []

    if db_row.get('media_data'):
        try:
            results['media_hits'] = json.loads(db_row['media_data'])
        except json.JSONDecodeError:
            results['media_hits'] = []
    else:
        results['media_hits'] = []

    if db_row.get('report_text'):
        results['report'] = db_row['report_text']
    else:
        results['report'] = ""

    if db_row.get('pdf_data'):
        results['pdf_bytes'] = db_row['pdf_data']
    else:
        results['pdf_bytes'] = None

    if db_row.get('conglomerate_data'):
        try:
            results['conglomerate_data'] = json.loads(db_row['conglomerate_data'])
        except json.JSONDecodeError:
            results['conglomerate_data'] = None
    else:
        results['conglomerate_data'] = None

    return results


def serialize_search_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize search parameters for database storage.

    Args:
        params: Dictionary with search parameters

    Returns:
        Dictionary with serialized parameters
    """
    return {
        'country_filter': params.get('country', 'GLOBAL'),
        'fuzzy_search': 1 if params.get('fuzzy', False) else 0,
        'is_conglomerate': 1 if params.get('conglomerate', False) else 0,
        'is_reverse_search': 1 if params.get('reverse_search', False) else 0,
        'search_depth': params.get('search_depth', 1),
        'ownership_threshold': params.get('ownership_threshold', 0.0),
    }


def calculate_summary_metrics(results_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate summary metrics for quick display in search history.

    Args:
        results_data: Search results data

    Returns:
        Dictionary with summary metrics
    """
    us_results = results_data.get('us_results', [])
    conglom_data = results_data.get('conglomerate_data')

    # Match count
    match_count = len(us_results) if us_results and 'error' not in (us_results[0] if us_results else {}) else 0

    # Risk level calculation (same logic as app.py)
    max_score = 0
    if match_count > 0:
        scores = [float(r.get('combined_score', r.get('Score', 0))) for r in us_results
                  if r.get('combined_score') or r.get('Score')]
        max_score = max(scores) if scores else 0

    has_exact_match = match_count > 0 and max_score >= 92
    has_high_match = match_count > 0 and 80 <= max_score < 92
    has_medium_match = match_count > 0 and 65 <= max_score < 80

    # Determine risk level
    if match_count == 0:
        risk_level = "SAFE"
    elif has_medium_match:
        risk_level = "LOW"
    elif has_high_match:
        risk_level = "MID"
    elif has_exact_match:
        risk_level = "HIGH"
    else:
        risk_level = "LOW"

    # Conglomerate counts
    subsidiary_count = 0
    sister_count = 0
    if conglom_data:
        subsidiary_count = len(conglom_data.get('subsidiaries', []))
        sister_count = len(conglom_data.get('sisters', []))

    return {
        'match_count': match_count,
        'risk_level': risk_level,
        'subsidiary_count': subsidiary_count,
        'sister_count': sister_count
    }


def generate_search_id() -> str:
    """
    Generate a unique search ID.

    Returns:
        Unique search ID string
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return f"search_{timestamp}"


def parse_tags(tags_input: str) -> str:
    """
    Parse and format tags for database storage.

    Args:
        tags_input: Comma-separated tag string

    Returns:
        JSON string of tags list
    """
    if not tags_input:
        return "[]"

    # Split by comma and clean
    tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
    return json.dumps(tags)


def format_tags_for_display(tags_json: str) -> list:
    """
    Parse tags from database for display.

    Args:
        tags_json: JSON string of tags

    Returns:
        List of tag strings
    """
    if not tags_json:
        return []

    try:
        return json.loads(tags_json)
    except json.JSONDecodeError:
        return []
