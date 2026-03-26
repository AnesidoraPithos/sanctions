"""
Database Operations Wrapper

Wraps the existing core/database.py functions for use in the FastAPI backend.
Provides async interfaces where needed and handles path resolution.
"""

import os
import sys
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import sqlite3

# Get database path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_root = os.path.dirname(backend_dir)
DB_FILE = os.path.join(project_root, 'sanctions.db')


def _ensure_columns_exist():
    """
    Ensure the analysis_history table has all required columns for the API.
    Adds missing columns if they don't exist.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Check existing columns
        cursor.execute("PRAGMA table_info(analysis_history)")
        columns = {row[1] for row in cursor.fetchall()}

        # Add missing columns
        if 'results' not in columns:
            cursor.execute("ALTER TABLE analysis_history ADD COLUMN results TEXT")
        if 'intelligence_report' not in columns:
            cursor.execute("ALTER TABLE analysis_history ADD COLUMN intelligence_report TEXT")
        if 'tier' not in columns:
            cursor.execute("ALTER TABLE analysis_history ADD COLUMN tier TEXT DEFAULT 'base'")

        conn.commit()
    except Exception as e:
        print(f"Error ensuring columns exist: {e}")
    finally:
        conn.close()


# Ensure columns exist on import
_ensure_columns_exist()


def save_search_results(
    search_id: str,
    entity_name: str,
    tier: str,
    risk_level: str,
    sanctions_data: List[Dict[str, Any]],
    research_data: Optional[Dict[str, Any]] = None,
    network_data: Optional[Dict[str, Any]] = None,
    intelligence_report: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Save search results to database

    Args:
        search_id: Unique identifier for this search
        entity_name: Name of entity searched
        tier: Research tier (base/network/deep)
        risk_level: Calculated risk level (SAFE/LOW/MID/HIGH/VERY_HIGH)
        sanctions_data: List of sanctions hits
        research_data: OSINT media intelligence data
        network_data: Conglomerate and network data (Phase 2)
        intelligence_report: LLM-generated intelligence report
        metadata: Additional metadata (search parameters, timing, etc.)

    Returns:
        True if save successful, False otherwise
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Prepare data for database
        results_json = json.dumps({
            "sanctions": sanctions_data,
            "research": research_data or {},
            "network": network_data or {},
            "metadata": metadata or {}
        })

        # Insert into analysis_history table
        cursor.execute("""
            INSERT INTO analysis_history
            (analysis_id, timestamp, query_term, translated_term, match_count, risk_level, results, intelligence_report, tier)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            search_id,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            entity_name,
            entity_name,  # translated_term (same as query for now)
            len(sanctions_data),
            risk_level,
            results_json,
            intelligence_report,
            tier
        ))

        conn.commit()
        return True

    except Exception as e:
        print(f"Error saving search results: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()


def get_search_results(search_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve search results from database

    Args:
        search_id: Unique identifier for search

    Returns:
        Dictionary with search results or None if not found
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT analysis_id, timestamp, query_term, match_count, risk_level,
                   results, intelligence_report, tier
            FROM analysis_history
            WHERE analysis_id = ?
        """, (search_id,))

        row = cursor.fetchone()

        if not row:
            return None

        # Parse row
        analysis_id, timestamp, query_term, match_count, risk_level, results_json, intelligence_report, tier = row

        # Parse JSON results
        results_data = json.loads(results_json) if results_json else {}

        # Extract network tier fields (Phase 2)
        network_data = results_data.get('network', {})

        return {
            "search_id": analysis_id,
            "entity_name": query_term,
            "tier": tier or 'base',
            "risk_level": risk_level,
            "sanctions_hits": match_count,
            "sanctions_data": results_data.get('sanctions', []),
            "research_data": results_data.get('research', {}),
            "network_data": {
                **network_data.get('graph', {}),
                "parent_info": network_data.get('parent_info'),
                "sisters": network_data.get('sisters', []),
            } if network_data else {},
            "financial_intelligence": network_data.get('financial_intelligence', {}) if network_data else {},
            "subsidiaries": network_data.get('subsidiaries', []) if network_data else [],
            "warnings": network_data.get('warnings', []) if network_data else [],
            "data_sources_used": network_data.get('data_sources_used', []) if network_data else [],
            "intelligence_report": intelligence_report,
            "timestamp": timestamp,
            "metadata": results_data.get('metadata', {})
        }

    except Exception as e:
        print(f"Error retrieving search results: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        conn.close()


def get_search_history(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get search history

    Args:
        limit: Maximum number of results to return

    Returns:
        List of search history entries
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT analysis_id, timestamp, query_term, match_count, risk_level, tier
            FROM analysis_history
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()

        return [
            {
                "search_id": row[0],
                "entity_name": row[2],
                "tier": row[5] or 'base',
                "risk_level": row[4],
                "sanctions_hits": row[3],
                "timestamp": row[1]
            }
            for row in rows
        ]

    except Exception as e:
        print(f"Error retrieving search history: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        conn.close()


def search_local_entities(query: str) -> List[Dict[str, Any]]:
    """
    Search local database entities (DOD 1260H, FCC)

    Args:
        query: Search query

    Returns:
        List of matching entities
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT name, entity_type, source_list, source_url, additional_info
            FROM local_entities
            WHERE name LIKE ?
        """, (f'%{query}%',))

        rows = cursor.fetchall()

        return [
            {
                "name": row[0],
                "entity_type": row[1],
                "source_list": row[2],
                "source_url": row[3],
                "additional_info": row[4]
            }
            for row in rows
        ]

    except Exception as e:
        print(f"Error searching local entities: {e}")
        return []
    finally:
        conn.close()
