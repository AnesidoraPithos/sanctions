import sqlite3
import pandas as pd
from datetime import datetime
from config import DB_FILE

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS china_list
                 (name TEXT, entity_type TEXT, date_added TEXT, source_url TEXT, notes TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS agent_logs
                 (timestamp TEXT, action TEXT, details TEXT)''')
    # --- NEW TABLE: ANALYSIS HISTORY ---
    c.execute('''CREATE TABLE IF NOT EXISTS analysis_history
                 (analysis_id TEXT PRIMARY KEY, timestamp TEXT, query_term TEXT,
                  translated_term TEXT, match_count INTEGER, risk_level TEXT)''')
    # --- NEW TABLE: LOCAL ENTITIES (External Sources) ---
    c.execute('''CREATE TABLE IF NOT EXISTS local_entities
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  entity_type TEXT,
                  source_list TEXT NOT NULL,
                  source_url TEXT,
                  date_added TEXT,
                  last_updated TEXT,
                  additional_info TEXT)''')
    conn.commit()
    conn.close()

def log_agent_action(action, details):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO agent_logs VALUES (?, ?, ?)", 
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), action, details))
    conn.commit()
    conn.close()

def save_china_finding(entity_name, headline, url):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM china_list WHERE name=?", (entity_name,))
    if not c.fetchone():
        c.execute("INSERT INTO china_list VALUES (?, ?, ?, ?, ?)", 
                  (entity_name, "Sanctioned Entity", datetime.now().strftime("%Y-%m-%d"), url, f"Source: {headline}"))
        conn.commit()
    conn.close()

# --- NEW: Log User Search History ---
def log_analysis_run(analysis_id, query_term, translated_term, match_count, risk_level):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO analysis_history VALUES (?, ?, ?, ?, ?, ?)", 
                  (analysis_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                   query_term, translated_term, match_count, risk_level))
        conn.commit()
    except Exception as e:
        print(f"Logging error: {e}")
    finally:
        conn.close()

# --- NEW: Get User Search History ---
def get_analysis_history(limit=50):
    conn = sqlite3.connect(DB_FILE)
    try:
        df = pd.read_sql_query(f"SELECT * FROM analysis_history ORDER BY timestamp DESC LIMIT {limit}", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

def search_china_db(query):
    conn = sqlite3.connect(DB_FILE)
    try:
        df = pd.read_sql_query(f"SELECT * FROM china_list WHERE name LIKE '%{query}%'", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

def get_recent_logs(limit=10):
    conn = sqlite3.connect(DB_FILE)
    try:
        df = pd.read_sql_query(f"SELECT * FROM agent_logs ORDER BY timestamp DESC LIMIT {limit}", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

# ============================================================================
# LOCAL ENTITIES FUNCTIONS (External Sources: DOD 1260H, FCC Covered List)
# ============================================================================

def insert_local_entity(name, entity_type, source_list, source_url="", additional_info=""):
    """
    Insert a single entity into the local_entities table.

    Args:
        name (str): Entity name
        entity_type (str): Type of entity (Company, Equipment, Individual, etc.)
        source_list (str): Source identifier (DOD_1260H, FCC_COVERED)
        source_url (str): URL to the source document
        additional_info (str): JSON or text with additional fields
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute("""INSERT INTO local_entities
                 (name, entity_type, source_list, source_url, date_added, last_updated, additional_info)
                 VALUES (?, ?, ?, ?, ?, ?, ?)""",
              (name, entity_type, source_list, source_url, timestamp, timestamp, additional_info))
    conn.commit()
    conn.close()

def search_local_entities(query_name):
    """
    Retrieve all entities from local database for fuzzy matching.
    Fuzzy matching will be done in the agent layer.

    Args:
        query_name (str): Search term (currently unused, returns all for fuzzy matching)

    Returns:
        list: List of entity dictionaries
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    try:
        c.execute("SELECT * FROM local_entities")
        rows = c.fetchall()

        entities = []
        for row in rows:
            entities.append({
                'id': row[0],
                'name': row[1],
                'entity_type': row[2],
                'source_list': row[3],
                'source_url': row[4],
                'date_added': row[5],
                'last_updated': row[6],
                'additional_info': row[7]
            })
        return entities
    except Exception as e:
        print(f"Error searching local entities: {e}")
        return []
    finally:
        conn.close()

def get_local_entity_count():
    """
    Get count of entities by source.

    Returns:
        dict: {"DOD_1260H": count, "FCC_COVERED": count, "TOTAL": total}
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    try:
        c.execute("SELECT source_list, COUNT(*) FROM local_entities GROUP BY source_list")
        rows = c.fetchall()

        counts = {}
        total = 0
        for row in rows:
            counts[row[0]] = row[1]
            total += row[1]
        counts['TOTAL'] = total
        return counts
    except Exception as e:
        print(f"Error getting entity count: {e}")
        return {'TOTAL': 0}
    finally:
        conn.close()

def clear_local_entities_by_source(source_list):
    """
    Delete all entities from a specific source.
    Used for refresh operations.

    Args:
        source_list (str): Source identifier to clear (DOD_1260H, FCC_COVERED)

    Returns:
        int: Number of rows deleted
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    try:
        c.execute("DELETE FROM local_entities WHERE source_list = ?", (source_list,))
        deleted = c.rowcount
        conn.commit()
        return deleted
    except Exception as e:
        print(f"Error clearing entities: {e}")
        return 0
    finally:
        conn.close()