import sqlite3
import json
import time
from pathlib import Path


DB_PATH = Path(__file__).parent / "run_cache.db"


def _get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS source_cache (
            idea_hash TEXT PRIMARY KEY,
            raw_idea TEXT,
            results TEXT,
            created_at REAL
        )
    """)
    return conn


def _hash_idea(idea: str) -> str:
    import hashlib
    return hashlib.sha256(idea.strip().lower().encode()).hexdigest()[:16]


def load_cached(idea: str, ttl_seconds: int = 3600) -> dict | None:
    conn = _get_conn()
    row = conn.execute(
        "SELECT results, created_at FROM source_cache WHERE idea_hash = ?",
        (_hash_idea(idea),),
    ).fetchone()
    conn.close()
    if row and time.time() - row[1] < ttl_seconds:
        return json.loads(row[0])
    return None


def save_cache(idea: str, results: dict):
    conn = _get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO source_cache (idea_hash, raw_idea, results, created_at) VALUES (?, ?, ?, ?)",
        (_hash_idea(idea), idea, json.dumps(results), time.time()),
    )
    conn.commit()
    conn.close()
