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
        if 'is_saved' not in columns:
            cursor.execute("ALTER TABLE analysis_history ADD COLUMN is_saved INTEGER DEFAULT 0")
        if 'save_label' not in columns:
            cursor.execute("ALTER TABLE analysis_history ADD COLUMN save_label TEXT")
        if 'saved_at' not in columns:
            cursor.execute("ALTER TABLE analysis_history ADD COLUMN saved_at TEXT")

        conn.commit()
    except Exception as e:
        print(f"Error ensuring columns exist: {e}")
    finally:
        conn.close()


# Ensure columns exist on import
_ensure_columns_exist()


def _ensure_financial_tables_exist():
    """
    Ensure the SEC financial intelligence tables exist.
    These store directors, shareholders, and transaction data from SEC EDGAR filings.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    try:
        c.execute('''CREATE TABLE IF NOT EXISTS directors_officers
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      company_name TEXT NOT NULL,
                      cik TEXT,
                      person_name TEXT NOT NULL,
                      title TEXT,
                      nationality TEXT,
                      biography TEXT,
                      other_positions TEXT,
                      filing_type TEXT,
                      filing_date TEXT,
                      source_url TEXT,
                      sanctions_hit INTEGER DEFAULT 0,
                      date_added TEXT,
                      last_updated TEXT)''')

        c.execute('''CREATE TABLE IF NOT EXISTS major_shareholders
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      company_name TEXT NOT NULL,
                      cik TEXT,
                      shareholder_name TEXT NOT NULL,
                      shareholder_type TEXT,
                      ownership_percentage REAL,
                      voting_rights REAL,
                      jurisdiction TEXT,
                      filing_type TEXT,
                      filing_date TEXT,
                      source_url TEXT,
                      sanctions_hit INTEGER DEFAULT 0,
                      date_added TEXT,
                      last_updated TEXT)''')

        c.execute('''CREATE TABLE IF NOT EXISTS related_party_transactions
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      company_name TEXT NOT NULL,
                      cik TEXT,
                      transaction_type TEXT,
                      counterparty TEXT NOT NULL,
                      relationship TEXT,
                      amount REAL,
                      currency TEXT,
                      transaction_date TEXT,
                      purpose TEXT,
                      terms TEXT,
                      filing_type TEXT,
                      filing_date TEXT,
                      source_url TEXT,
                      date_added TEXT,
                      last_updated TEXT)''')

        conn.commit()
    except Exception as e:
        print(f"Error ensuring financial tables exist: {e}")
    finally:
        conn.close()


_ensure_financial_tables_exist()


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
                   results, intelligence_report, tier, is_saved, save_label
            FROM analysis_history
            WHERE analysis_id = ?
        """, (search_id,))

        row = cursor.fetchone()

        if not row:
            return None

        # Parse row
        analysis_id, timestamp, query_term, match_count, risk_level, results_json, intelligence_report, tier, is_saved, save_label = row

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
            "financial_flows": network_data.get('financial_flows', []) if network_data else [],
            # Phase 4 fields
            "director_pivots": network_data.get('director_pivots', []) if network_data else [],
            "infrastructure": network_data.get('infrastructure', []) if network_data else [],
            "beneficial_owners": network_data.get('beneficial_owners', []) if network_data else [],
            "advanced_osint": network_data.get('advanced_osint', {}) if network_data else {},
            "intelligence_report": intelligence_report,
            "timestamp": timestamp,
            "metadata": results_data.get('metadata', {}),
            "is_saved": bool(is_saved),
            "save_label": save_label,
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
            SELECT analysis_id, timestamp, query_term, match_count, risk_level, tier,
                   is_saved, save_label
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
                "timestamp": row[1],
                "is_saved": bool(row[6]),
                "save_label": row[7],
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


def toggle_save_result(search_id: str, is_saved: bool, label: Optional[str] = None) -> bool:
    """
    Bookmark or un-bookmark a search result.

    Args:
        search_id: Unique identifier for the search
        is_saved: True to save, False to unsave
        label: Optional label/note for the bookmark

    Returns:
        True if update successful, False otherwise
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        saved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if is_saved else None
        cursor.execute("""
            UPDATE analysis_history
            SET is_saved = ?, save_label = ?, saved_at = ?
            WHERE analysis_id = ?
        """, (1 if is_saved else 0, label if is_saved else None, saved_at, search_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error toggling save for {search_id}: {e}")
        return False
    finally:
        conn.close()


def get_saved_searches(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get all bookmarked search results.

    Args:
        limit: Maximum number of results to return

    Returns:
        List of saved search history entries, ordered by saved_at desc
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT analysis_id, timestamp, query_term, match_count, risk_level, tier,
                   is_saved, save_label, saved_at
            FROM analysis_history
            WHERE is_saved = 1
            ORDER BY saved_at DESC
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
                "timestamp": row[1],
                "is_saved": True,
                "save_label": row[7],
                "saved_at": row[8],
            }
            for row in rows
        ]

    except Exception as e:
        print(f"Error retrieving saved searches: {e}")
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


def get_directors(company_name=None, cik=None):
    """
    Retrieve directors for a company.

    Args:
        company_name (str): Company name (optional)
        cik (str): Company CIK (optional)

    Returns:
        list: List of director dictionaries
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    try:
        if cik:
            c.execute("SELECT * FROM directors_officers WHERE cik = ? ORDER BY person_name", (cik,))
        elif company_name:
            c.execute("SELECT * FROM directors_officers WHERE company_name = ? ORDER BY person_name", (company_name,))
        else:
            return []

        rows = c.fetchall()
        directors = []
        for row in rows:
            directors.append({
                'id': row[0],
                'company_name': row[1],
                'cik': row[2],
                'name': row[3],
                'title': row[4],
                'nationality': row[5],
                'biography': row[6],
                'other_positions': row[7],
                'filing_type': row[8],
                'filing_date': row[9],
                'source_url': row[10],
                'sanctions_hit': row[11],
                'date_added': row[12],
                'last_updated': row[13]
            })
        return directors
    except Exception as e:
        print(f"Error retrieving directors: {e}")
        return []
    finally:
        conn.close()


def get_shareholders(company_name=None, cik=None):
    """
    Retrieve major shareholders for a company.

    Args:
        company_name (str): Company name (optional)
        cik (str): Company CIK (optional)

    Returns:
        list: List of shareholder dictionaries
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    try:
        if cik:
            c.execute("SELECT * FROM major_shareholders WHERE cik = ? ORDER BY ownership_percentage DESC", (cik,))
        elif company_name:
            c.execute("SELECT * FROM major_shareholders WHERE company_name = ? ORDER BY ownership_percentage DESC", (company_name,))
        else:
            return []

        rows = c.fetchall()
        shareholders = []
        for row in rows:
            shareholders.append({
                'id': row[0],
                'company_name': row[1],
                'cik': row[2],
                'name': row[3],
                'type': row[4],
                'ownership_percentage': row[5],
                'voting_rights': row[6],
                'jurisdiction': row[7],
                'filing_type': row[8],
                'filing_date': row[9],
                'source_url': row[10],
                'sanctions_hit': row[11],
                'date_added': row[12],
                'last_updated': row[13]
            })
        return shareholders
    except Exception as e:
        print(f"Error retrieving shareholders: {e}")
        return []
    finally:
        conn.close()


def get_transactions(company_name=None, cik=None):
    """
    Retrieve related party transactions for a company.

    Args:
        company_name (str): Company name (optional)
        cik (str): Company CIK (optional)

    Returns:
        list: List of transaction dictionaries
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    try:
        if cik:
            c.execute("SELECT * FROM related_party_transactions WHERE cik = ? ORDER BY transaction_date DESC", (cik,))
        elif company_name:
            c.execute("SELECT * FROM related_party_transactions WHERE company_name = ? ORDER BY transaction_date DESC", (company_name,))
        else:
            return []

        rows = c.fetchall()
        transactions = []
        for row in rows:
            transactions.append({
                'id': row[0],
                'company_name': row[1],
                'cik': row[2],
                'transaction_type': row[3],
                'counterparty': row[4],
                'relationship': row[5],
                'amount': row[6],
                'currency': row[7],
                'transaction_date': row[8],
                'purpose': row[9],
                'terms': row[10],
                'filing_type': row[11],
                'filing_date': row[12],
                'source_url': row[13],
                'date_added': row[14],
                'last_updated': row[15]
            })
        return transactions
    except Exception as e:
        print(f"Error retrieving transactions: {e}")
        return []
    finally:
        conn.close()
