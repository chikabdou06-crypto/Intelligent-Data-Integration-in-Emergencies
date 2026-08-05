import sqlite3
import hashlib
import json
from pathlib import Path

# Paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BACKEND_DIR / "vault" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = CACHE_DIR / "execution_cache.sqlite"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tool_cache (
                hash_key TEXT PRIMARY KEY,
                tool_name TEXT,
                result TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

# Initialize table on import
init_db()

def _generate_hash(tool_name: str, kwargs: dict) -> str:
    """Generate a consistent SHA256 hash for the tool name and its arguments."""
    dict_str = json.dumps(kwargs, sort_keys=True)
    combined = f"{tool_name}::{dict_str}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()

def get_cached_result(tool_name: str, kwargs: dict, ttl_hours: int = 6):
    """Retrieve a cached execution result if it exists and is within TTL."""
    hash_key = _generate_hash(tool_name, kwargs)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        if ttl_hours > 0:
            query = f"SELECT result FROM tool_cache WHERE hash_key = ? AND timestamp >= datetime('now', '-{ttl_hours} hours')"
        else:
            query = "SELECT result FROM tool_cache WHERE hash_key = ?"
            
        cursor.execute(query, (hash_key,))
        row = cursor.fetchone()
        if row:
            return json.loads(row[0])
    return None

def set_cached_result(tool_name: str, kwargs: dict, result: any):
    """Save an execution result to the cache to skip future API calls."""
    hash_key = _generate_hash(tool_name, kwargs)
    try:
        json_result = json.dumps(result)
    except TypeError:
        # If result is not JSON serializable, convert to string
        json_result = json.dumps(str(result))
        
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO tool_cache (hash_key, tool_name, result) VALUES (?, ?, ?)",
            (hash_key, tool_name, json_result)
        )
