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

    # --- NEW TABLES: DIRECTORS, SHAREHOLDERS, TRANSACTIONS (SEC EDGAR Financial Intelligence) ---
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

    # --- NEW TABLE: LOAN AGREEMENTS (Exhibit 4.3 and 4.5) ---
    c.execute('''CREATE TABLE IF NOT EXISTS loan_agreements
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  company_name TEXT NOT NULL,
                  cik TEXT,
                  lender TEXT NOT NULL,
                  borrower TEXT NOT NULL,
                  guarantors TEXT,
                  loan_type TEXT,
                  principal_amount REAL,
                  currency TEXT,
                  interest_rate TEXT,
                  maturity_date TEXT,
                  effective_date TEXT,
                  purpose TEXT,
                  covenants TEXT,
                  security_collateral TEXT,
                  prepayment_terms TEXT,
                  exhibit_type TEXT,
                  filing_type TEXT,
                  filing_date TEXT,
                  source_url TEXT,
                  date_added TEXT,
                  last_updated TEXT)''')

    # Create indexes for loan_agreements
    c.execute('''CREATE INDEX IF NOT EXISTS idx_loan_company ON loan_agreements(company_name)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_loan_lender ON loan_agreements(lender)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_loan_borrower ON loan_agreements(borrower)''')

    # --- NEW TABLE: SAVED SEARCHES (Complete Search Results) ---
    c.execute('''CREATE TABLE IF NOT EXISTS saved_searches
                 (search_id TEXT PRIMARY KEY,
                  timestamp TEXT NOT NULL,
                  entity_name TEXT NOT NULL,
                  translated_name TEXT,
                  country_filter TEXT,
                  fuzzy_search INTEGER,
                  is_conglomerate INTEGER DEFAULT 0,
                  is_reverse_search INTEGER DEFAULT 0,
                  search_depth INTEGER DEFAULT 1,
                  ownership_threshold REAL DEFAULT 0,
                  match_count INTEGER,
                  risk_level TEXT,
                  subsidiary_count INTEGER DEFAULT 0,
                  sister_count INTEGER DEFAULT 0,
                  notes TEXT,
                  tags TEXT,
                  is_auto_saved INTEGER DEFAULT 1,
                  sanctions_data TEXT,
                  media_data TEXT,
                  report_text TEXT,
                  pdf_data BLOB,
                  conglomerate_data TEXT,
                  last_accessed TEXT,
                  access_count INTEGER DEFAULT 0,
                  is_shared INTEGER DEFAULT 0,
                  share_token TEXT)''')

    # Create indexes for faster queries
    c.execute('''CREATE INDEX IF NOT EXISTS idx_entity_name ON saved_searches(entity_name)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_timestamp ON saved_searches(timestamp)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_tags ON saved_searches(tags)''')

    # --- NEW TABLE: SEARCH COMPARISONS ---
    c.execute('''CREATE TABLE IF NOT EXISTS search_comparisons
                 (comparison_id TEXT PRIMARY KEY,
                  timestamp TEXT NOT NULL,
                  search_ids TEXT NOT NULL,
                  comparison_notes TEXT,
                  created_by TEXT)''')

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

# ============================================================================
# FINANCIAL INTELLIGENCE FUNCTIONS (Directors, Shareholders, Transactions)
# ============================================================================

def insert_directors(company_name, cik, directors_list, filing_type, filing_date, source_url):
    """
    Insert directors and officers for a company.

    Args:
        company_name (str): Company name
        cik (str): Company CIK number
        directors_list (list): List of director dictionaries
        filing_type (str): Filing type (10-K, 20-F, DEF 14A)
        filing_date (str): Filing date
        source_url (str): Source URL
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Clear existing directors for this company/filing
    c.execute("DELETE FROM directors_officers WHERE company_name = ? AND cik = ?", (company_name, cik))

    for director in directors_list:
        c.execute("""INSERT INTO directors_officers
                     (company_name, cik, person_name, title, nationality, biography, other_positions,
                      filing_type, filing_date, source_url, sanctions_hit, date_added, last_updated)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)""",
                  (company_name, cik, director.get('name'), director.get('title'),
                   director.get('nationality'), director.get('biography'), director.get('other_positions'),
                   filing_type, filing_date, source_url, timestamp, timestamp))

    conn.commit()
    conn.close()

def insert_shareholders(company_name, cik, shareholders_list, filing_type, filing_date, source_url):
    """
    Insert major shareholders for a company.

    Args:
        company_name (str): Company name
        cik (str): Company CIK number
        shareholders_list (list): List of shareholder dictionaries
        filing_type (str): Filing type (10-K, 20-F, DEF 14A)
        filing_date (str): Filing date
        source_url (str): Source URL
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Clear existing shareholders for this company/filing
    c.execute("DELETE FROM major_shareholders WHERE company_name = ? AND cik = ?", (company_name, cik))

    for shareholder in shareholders_list:
        c.execute("""INSERT INTO major_shareholders
                     (company_name, cik, shareholder_name, shareholder_type, ownership_percentage,
                      voting_rights, jurisdiction, filing_type, filing_date, source_url, sanctions_hit,
                      date_added, last_updated)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)""",
                  (company_name, cik, shareholder.get('name'), shareholder.get('type'),
                   shareholder.get('ownership_percentage'), shareholder.get('voting_rights'),
                   shareholder.get('jurisdiction'), filing_type, filing_date, source_url,
                   timestamp, timestamp))

    conn.commit()
    conn.close()

def insert_transactions(company_name, cik, transactions_list, filing_type, filing_date, source_url):
    """
    Insert related party transactions for a company.

    Args:
        company_name (str): Company name
        cik (str): Company CIK number
        transactions_list (list): List of transaction dictionaries
        filing_type (str): Filing type (10-K, 20-F, DEF 14A)
        filing_date (str): Filing date
        source_url (str): Source URL
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Clear existing transactions for this company/filing
    c.execute("DELETE FROM related_party_transactions WHERE company_name = ? AND cik = ?", (company_name, cik))

    for txn in transactions_list:
        c.execute("""INSERT INTO related_party_transactions
                     (company_name, cik, transaction_type, counterparty, relationship, amount,
                      currency, transaction_date, purpose, terms, filing_type, filing_date,
                      source_url, date_added, last_updated)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (company_name, cik, txn.get('transaction_type'), txn.get('counterparty'),
                   txn.get('relationship'), txn.get('amount'), txn.get('currency'),
                   txn.get('transaction_date'), txn.get('purpose'), txn.get('terms'),
                   filing_type, filing_date, source_url, timestamp, timestamp))

    conn.commit()
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

# ============================================================================
# LOAN AGREEMENTS FUNCTIONS (Exhibit 4.3 and 4.5)
# ============================================================================

def insert_loan_agreements(company_name, cik, loan_agreements_list, filing_type, filing_date, source_url):
    """
    Insert loan agreements extracted from SEC Exhibit 4.3 or 4.5.

    Args:
        company_name (str): Company name
        cik (str): Company CIK number
        loan_agreements_list (list): List of loan agreement dictionaries
        filing_type (str): Filing type (10-K, 20-F)
        filing_date (str): Filing date
        source_url (str): Source URL

    Returns:
        int: Number of records inserted
    """
    import json

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Clear existing loan agreements for this company/filing
    c.execute("DELETE FROM loan_agreements WHERE company_name = ? AND cik = ?", (company_name, cik))

    count = 0
    for loan in loan_agreements_list:
        c.execute("""INSERT INTO loan_agreements
                     (company_name, cik, lender, borrower, guarantors,
                      loan_type, principal_amount, currency, interest_rate,
                      maturity_date, effective_date, purpose, covenants,
                      security_collateral, prepayment_terms, exhibit_type,
                      filing_type, filing_date, source_url, date_added, last_updated)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (company_name, cik,
                   loan.get('lender'), loan.get('borrower'),
                   json.dumps(loan.get('guarantors', [])),
                   loan.get('loan_type'), loan.get('principal_amount'),
                   loan.get('currency'), loan.get('interest_rate'),
                   loan.get('maturity_date'), loan.get('effective_date'),
                   loan.get('purpose'), json.dumps(loan.get('covenants', [])),
                   loan.get('security_collateral'), loan.get('prepayment_terms'),
                   loan.get('exhibit_type'), filing_type,
                   filing_date, source_url,
                   timestamp, timestamp))
        count += 1

    conn.commit()
    conn.close()
    return count


def get_loan_agreements(company_name=None, cik=None):
    """
    Retrieve all loan agreements for a company.

    Args:
        company_name (str): Company name (optional)
        cik (str): Company CIK (optional)

    Returns:
        list: List of loan agreement dictionaries
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    try:
        if cik:
            c.execute("SELECT * FROM loan_agreements WHERE cik = ? ORDER BY filing_date DESC", (cik,))
        elif company_name:
            c.execute("SELECT * FROM loan_agreements WHERE company_name = ? ORDER BY filing_date DESC", (company_name,))
        else:
            return []

        rows = c.fetchall()
        loans = []
        for row in rows:
            loans.append({
                'id': row[0],
                'company_name': row[1],
                'cik': row[2],
                'lender': row[3],
                'borrower': row[4],
                'guarantors': row[5],
                'loan_type': row[6],
                'principal_amount': row[7],
                'currency': row[8],
                'interest_rate': row[9],
                'maturity_date': row[10],
                'effective_date': row[11],
                'purpose': row[12],
                'covenants': row[13],
                'security_collateral': row[14],
                'prepayment_terms': row[15],
                'exhibit_type': row[16],
                'filing_type': row[17],
                'filing_date': row[18],
                'source_url': row[19],
                'date_added': row[20],
                'last_updated': row[21]
            })
        return loans
    except Exception as e:
        print(f"Error retrieving loan agreements: {e}")
        return []
    finally:
        conn.close()


def get_loan_agreements_by_entity(entity_name):
    """
    Get all loans where entity is lender, borrower, or guarantor.

    Args:
        entity_name (str): Entity name to search for

    Returns:
        list: List of loan agreement dictionaries
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    try:
        c.execute("""SELECT * FROM loan_agreements
                     WHERE lender LIKE ? OR borrower LIKE ? OR guarantors LIKE ?
                     ORDER BY filing_date DESC""",
                  (f'%{entity_name}%', f'%{entity_name}%', f'%{entity_name}%'))

        rows = c.fetchall()
        loans = []
        for row in rows:
            loans.append({
                'id': row[0],
                'company_name': row[1],
                'cik': row[2],
                'lender': row[3],
                'borrower': row[4],
                'guarantors': row[5],
                'loan_type': row[6],
                'principal_amount': row[7],
                'currency': row[8],
                'interest_rate': row[9],
                'maturity_date': row[10],
                'effective_date': row[11],
                'purpose': row[12],
                'covenants': row[13],
                'security_collateral': row[14],
                'prepayment_terms': row[15],
                'exhibit_type': row[16],
                'filing_type': row[17],
                'filing_date': row[18],
                'source_url': row[19],
                'date_added': row[20],
                'last_updated': row[21]
            })
        return loans
    except Exception as e:
        print(f"Error retrieving loan agreements by entity: {e}")
        return []
    finally:
        conn.close()

# ============================================================================
# SAVED SEARCHES FUNCTIONS (Complete Search Results Save/Restore)
# ============================================================================

def save_search_results(search_id, entity_name, translated_name, search_params,
                       results_data, summary_metrics, user_metadata=None):
    """
    Save complete search results to database.

    Args:
        search_id (str): Unique identifier
        entity_name (str): Searched entity name
        translated_name (str): Translated name (if applicable)
        search_params (dict): Serialized search parameters
        results_data (dict): Serialized results data
        summary_metrics (dict): Summary metrics (match_count, risk_level, etc.)
        user_metadata (dict): Optional user metadata (notes, tags, is_auto_saved)

    Returns:
        bool: Success status
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # Prepare user metadata
        notes = user_metadata.get('notes', '') if user_metadata else ''
        tags = user_metadata.get('tags', '[]') if user_metadata else '[]'
        is_auto_saved = user_metadata.get('is_auto_saved', 1) if user_metadata else 1

        c.execute("""INSERT INTO saved_searches
                     (search_id, timestamp, entity_name, translated_name,
                      country_filter, fuzzy_search, is_conglomerate, is_reverse_search,
                      search_depth, ownership_threshold,
                      match_count, risk_level, subsidiary_count, sister_count,
                      notes, tags, is_auto_saved,
                      sanctions_data, media_data, report_text, pdf_data, conglomerate_data,
                      last_accessed, access_count)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (search_id, timestamp, entity_name, translated_name,
                   search_params.get('country_filter'),
                   search_params.get('fuzzy_search'),
                   search_params.get('is_conglomerate'),
                   search_params.get('is_reverse_search'),
                   search_params.get('search_depth'),
                   search_params.get('ownership_threshold'),
                   summary_metrics.get('match_count'),
                   summary_metrics.get('risk_level'),
                   summary_metrics.get('subsidiary_count'),
                   summary_metrics.get('sister_count'),
                   notes, tags, is_auto_saved,
                   results_data.get('sanctions_data'),
                   results_data.get('media_data'),
                   results_data.get('report_text'),
                   results_data.get('pdf_data'),
                   results_data.get('conglomerate_data'),
                   timestamp, 0))

        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving search results: {e}")
        return False
    finally:
        conn.close()


def load_search_results(search_id):
    """
    Load complete search results from database.

    Args:
        search_id (str): Search identifier

    Returns:
        dict: Complete search data or None if not found
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    c = conn.cursor()

    try:
        c.execute("SELECT * FROM saved_searches WHERE search_id = ?", (search_id,))
        row = c.fetchone()

        if not row:
            return None

        # Update last accessed and access count
        c.execute("""UPDATE saved_searches
                     SET last_accessed = ?, access_count = access_count + 1
                     WHERE search_id = ?""",
                  (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), search_id))
        conn.commit()

        # Convert row to dictionary
        return dict(row)
    except Exception as e:
        print(f"Error loading search results: {e}")
        return None
    finally:
        conn.close()


def get_saved_searches(limit=50, filters=None):
    """
    Get list of saved searches with optional filtering.

    Args:
        limit (int): Maximum number to return
        filters (dict): Optional filters:
            - entity_name: Search by entity
            - tags: Filter by tags (list)
            - date_range: (start, end) tuple
            - min_risk_level: Minimum risk level
            - is_auto_saved: Filter by auto-saved flag

    Returns:
        DataFrame: Search history with summary info
    """
    conn = sqlite3.connect(DB_FILE)

    try:
        query = """SELECT search_id, timestamp, entity_name, translated_name,
                          country_filter, fuzzy_search, is_conglomerate, is_reverse_search,
                          match_count, risk_level, subsidiary_count, sister_count,
                          notes, tags, is_auto_saved, last_accessed, access_count
                   FROM saved_searches"""

        where_clauses = []
        params = []

        if filters:
            if filters.get('entity_name'):
                where_clauses.append("entity_name LIKE ?")
                params.append(f"%{filters['entity_name']}%")

            if filters.get('tags'):
                # Tag filtering (basic implementation)
                tag_conditions = []
                for tag in filters['tags']:
                    tag_conditions.append("tags LIKE ?")
                    params.append(f"%{tag}%")
                if tag_conditions:
                    where_clauses.append(f"({' OR '.join(tag_conditions)})")

            if filters.get('is_auto_saved') is not None:
                where_clauses.append("is_auto_saved = ?")
                params.append(1 if filters['is_auto_saved'] else 0)

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        query += f" ORDER BY timestamp DESC LIMIT {limit}"

        df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception as e:
        print(f"Error getting saved searches: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def update_search_metadata(search_id, notes=None, tags=None):
    """
    Update notes and tags for a saved search.

    Args:
        search_id (str): Search ID
        notes (str): New notes (optional)
        tags (str): New tags JSON (optional)

    Returns:
        bool: Success status
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    try:
        if notes is not None:
            c.execute("UPDATE saved_searches SET notes = ? WHERE search_id = ?", (notes, search_id))

        if tags is not None:
            c.execute("UPDATE saved_searches SET tags = ? WHERE search_id = ?", (tags, search_id))

        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating search metadata: {e}")
        return False
    finally:
        conn.close()


def delete_saved_search(search_id):
    """
    Delete a saved search from database.

    Args:
        search_id (str): Search ID

    Returns:
        bool: Success status
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    try:
        c.execute("DELETE FROM saved_searches WHERE search_id = ?", (search_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting saved search: {e}")
        return False
    finally:
        conn.close()


def delete_multiple_searches(search_ids):
    """
    Delete multiple saved searches from database.

    Args:
        search_ids (list): List of search IDs

    Returns:
        tuple: (success_count, total_count)
    """
    if not search_ids:
        return (0, 0)

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    success_count = 0
    try:
        for search_id in search_ids:
            c.execute("DELETE FROM saved_searches WHERE search_id = ?", (search_id,))
            if c.rowcount > 0:
                success_count += 1
        conn.commit()
        return (success_count, len(search_ids))
    except Exception as e:
        print(f"Error deleting multiple searches: {e}")
        return (success_count, len(search_ids))
    finally:
        conn.close()


def delete_all_searches():
    """
    Delete all saved searches from database.

    Returns:
        int: Number of searches deleted
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    try:
        c.execute("DELETE FROM saved_searches")
        deleted_count = c.rowcount
        conn.commit()
        return deleted_count
    except Exception as e:
        print(f"Error deleting all searches: {e}")
        return 0
    finally:
        conn.close()


def get_all_tags():
    """
    Get all unique tags from saved searches.

    Returns:
        list: List of unique tags
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    try:
        c.execute("SELECT DISTINCT tags FROM saved_searches WHERE tags IS NOT NULL AND tags != '[]'")
        rows = c.fetchall()

        all_tags = set()
        for row in rows:
            try:
                import json
                tags = json.loads(row[0])
                all_tags.update(tags)
            except:
                pass

        return sorted(list(all_tags))
    except Exception as e:
        print(f"Error getting tags: {e}")
        return []
    finally:
        conn.close()


def create_share_token(search_id):
    """
    Generate shareable token for a search.

    Args:
        search_id (str): Search ID

    Returns:
        str: Share token
    """
    import uuid
    token = str(uuid.uuid4())

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    try:
        c.execute("""UPDATE saved_searches
                     SET is_shared = 1, share_token = ?
                     WHERE search_id = ?""", (token, search_id))
        conn.commit()
        return token
    except Exception as e:
        print(f"Error creating share token: {e}")
        return None
    finally:
        conn.close()


def get_search_by_token(token):
    """
    Load search by share token.

    Args:
        token (str): Share token

    Returns:
        dict: Search data or None
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    try:
        c.execute("SELECT * FROM saved_searches WHERE share_token = ?", (token,))
        row = c.fetchone()

        if row:
            return dict(row)
        return None
    except Exception as e:
        print(f"Error getting search by token: {e}")
        return None
    finally:
        conn.close()


# ============================================================================
# SEARCH COMPARISONS FUNCTIONS
# ============================================================================

def create_comparison(search_ids, notes=""):
    """
    Create a comparison session between multiple searches.

    Args:
        search_ids (list): List of search IDs to compare
        notes (str): Optional comparison notes

    Returns:
        str: Comparison ID or None on error
    """
    import uuid
    import json

    comparison_id = f"comparison_{uuid.uuid4().hex[:12]}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    try:
        c.execute("""INSERT INTO search_comparisons
                     (comparison_id, timestamp, search_ids, comparison_notes)
                     VALUES (?, ?, ?, ?)""",
                  (comparison_id, timestamp, json.dumps(search_ids), notes))
        conn.commit()
        return comparison_id
    except Exception as e:
        print(f"Error creating comparison: {e}")
        return None
    finally:
        conn.close()


def get_comparisons(limit=20):
    """
    Get list of saved comparisons.

    Args:
        limit (int): Maximum number to return

    Returns:
        DataFrame: Comparison history
    """
    conn = sqlite3.connect(DB_FILE)

    try:
        df = pd.read_sql_query(
            f"SELECT * FROM search_comparisons ORDER BY timestamp DESC LIMIT {limit}",
            conn
        )
        return df
    except Exception as e:
        print(f"Error getting comparisons: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def load_comparison(comparison_id):
    """
    Load searches for a comparison.

    Args:
        comparison_id (str): Comparison ID

    Returns:
        dict: Comparison data with loaded searches or None
    """
    import json

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    try:
        c.execute("SELECT * FROM search_comparisons WHERE comparison_id = ?", (comparison_id,))
        row = c.fetchone()

        if not row:
            return None

        comparison_data = dict(row)
        search_ids = json.loads(comparison_data['search_ids'])

        # Load all searches
        searches = []
        for sid in search_ids:
            search = load_search_results(sid)
            if search:
                searches.append(search)

        comparison_data['searches'] = searches
        return comparison_data
    except Exception as e:
        print(f"Error loading comparison: {e}")
        return None
    finally:
        conn.close()