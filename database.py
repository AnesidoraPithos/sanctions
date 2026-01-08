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
    # Simple deduplication
    c.execute("SELECT * FROM china_list WHERE name=?", (entity_name,))
    if not c.fetchone():
        c.execute("INSERT INTO china_list VALUES (?, ?, ?, ?, ?)", 
                  (entity_name, "Sanctioned Entity", datetime.now().strftime("%Y-%m-%d"), url, f"Source: {headline}"))
        conn.commit()
    conn.close()

def search_china_db(query):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(f"SELECT * FROM china_list WHERE name LIKE '%{query}%'", conn)
    conn.close()
    return df

def get_recent_logs(limit=10):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(f"SELECT * FROM agent_logs ORDER BY timestamp DESC LIMIT {limit}", conn)
    conn.close()
    return df