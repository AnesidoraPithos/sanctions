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