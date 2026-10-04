import sqlite3
import json
import datetime
from typing import List, Dict, Any, Optional

DB_PATH = "rfp_eval.db"

DEFAULT_CRITERIA = [
    {
        "criterion_id": 1,
        "name": "Technical Capability",
        "description": "Architecture, integrations, scalability, technical fit",
        "weight": 30.0,
        "max_score": 10.0,
        "is_active": 1
    },
    {
        "criterion_id": 2,
        "name": "Implementation Plan",
        "description": "Timeline, milestones, staffing, risk plan",
        "weight": 20.0,
        "max_score": 10.0,
        "is_active": 1
    },
    {
        "criterion_id": 3,
        "name": "Commercial Value",
        "description": "Pricing clarity, total cost, assumptions",
        "weight": 20.0,
        "max_score": 10.0,
        "is_active": 1
    },
    {
        "criterion_id": 4,
        "name": "Security & Compliance",
        "description": "Controls, certifications, privacy, auditability",
        "weight": 20.0,
        "max_score": 10.0,
        "is_active": 1
    },
    {
        "criterion_id": 5,
        "name": "Support & Experience",
        "description": "Support model, similar projects, references",
        "weight": 10.0,
        "max_score": 10.0,
        "is_active": 1
    }
]

def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str = DB_PATH):
    """Creates SQLite tables and seeds default evaluation criteria if empty."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # 1. evaluation_criteria table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluation_criteria (
                criterion_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                weight REAL NOT NULL,
                max_score REAL NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1
            )
        """)
        
        # 2. rfp_runs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rfp_runs (
                rfp_run_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)
        
        # 3. supplier_results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS supplier_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rfp_run_id TEXT NOT NULL,
                supplier_name TEXT NOT NULL,
                submission_date TEXT NOT NULL,
                experience_rating REAL NOT NULL,
                absolute_score REAL NOT NULL,
                ppi REAL NOT NULL,
                final_rank INTEGER NOT NULL,
                result_json TEXT NOT NULL,
                FOREIGN KEY (rfp_run_id) REFERENCES rfp_runs (rfp_run_id)
            )
        """)
        
        # Seed default criteria if table is empty
        cursor.execute("SELECT COUNT(*) FROM evaluation_criteria")
        if cursor.fetchone()[0] == 0:
            for item in DEFAULT_CRITERIA:
                cursor.execute("""
                    INSERT INTO evaluation_criteria (criterion_id, name, description, weight, max_score, is_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (item["criterion_id"], item["name"], item["description"], item["weight"], item["max_score"], item["is_active"]))
        conn.commit()

def get_active_criteria(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Returns all active evaluation criteria sorted by criterion_id."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM evaluation_criteria WHERE is_active = 1 ORDER BY criterion_id ASC")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_all_criteria(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Returns all criteria including inactive ones."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM evaluation_criteria ORDER BY criterion_id ASC")
        return [dict(r) for r in cursor.fetchall()]

def update_criterion(criterion_id: int, weight: float, max_score: float, is_active: int, db_path: str = DB_PATH):
    """Updates criterion properties."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE evaluation_criteria
            SET weight = ?, max_score = ?, is_active = ?
            WHERE criterion_id = ?
        """, (weight, max_score, is_active, criterion_id))
        conn.commit()

def save_rfp_run(rfp_run_id: str, status: str, supplier_rankings: List[Dict[str, Any]], db_path: str = DB_PATH):
    """Saves a complete RFP run and supplier results into SQLite."""
    init_db(db_path)
    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO rfp_runs (rfp_run_id, created_at, status)
            VALUES (?, ?, ?)
        """, (rfp_run_id, created_at, status))
        
        for item in supplier_rankings:
            cursor.execute("""
                INSERT INTO supplier_results 
                (rfp_run_id, supplier_name, submission_date, experience_rating, absolute_score, ppi, final_rank, result_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rfp_run_id,
                item["supplier_name"],
                item["submission_date"],
                float(item.get("experience_rating", 0.0)),
                float(item["absolute_score"]),
                float(item["ppi"]),
                int(item["final_rank"]),
                json.dumps(item)
            ))
        conn.commit()

def get_rfp_run(rfp_run_id: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieves a complete RFP run by ID."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rfp_runs WHERE rfp_run_id = ?", (rfp_run_id,))
        run_row = cursor.fetchone()
        if not run_row:
            return None
        
        cursor.execute("SELECT * FROM supplier_results WHERE rfp_run_id = ? ORDER BY final_rank ASC", (rfp_run_id,))
        results = [json.loads(r["result_json"]) for r in cursor.fetchall()]
        
        return {
            "rfp_run_id": run_row["rfp_run_id"],
            "created_at": run_row["created_at"],
            "status": run_row["status"],
            "supplier_results": results
        }

def list_all_runs(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Lists all stored RFP runs."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rfp_runs ORDER BY created_at DESC")
        return [dict(r) for r in cursor.fetchall()]
