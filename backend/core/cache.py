"""
Deterministic SHA-256 Tool Execution Cache & Telemetry Persistence.
===================================================================

Academic Framework & Systemic Context:
--------------------------------------
In emergency response decision-support systems, external sensor endpoints (e.g., AEMET
OpenData, SNCZI hydrological stations, PATRICOVA spatial cartography) exhibit heterogeneous
latencies, intermittent network volatility, and strict rate limits (e.g., HTTP 429).
Simultaneously, citizens and emergency responders frequently query identical or overlapping
geographic localities (e.g., "Paiporta flood status", "Barranco del Poyo river discharge").

This module implements a deterministic memoization tier satisfying the following formal
specifications:

1. Canonical Hashing:
   Let $t \\in \\mathcal{T}$ be the unique tool identifier, and $\\vec{a} = \\{k_i: v_i\\}$ be the
   keyword argument dictionary. The cache key $K(t, \\vec{a})$ is formulated as:
     $$K(t, \\vec{a}) = \\text{SHA-256}\\Big( t \\parallel \\text{JSON}_{\\text{sorted}}(\\vec{a}) \\Big)$$
   Ensuring key invariance regardless of parameter insertion order or caller formatting.

2. Empirical Latency Reduction:
   As benchmarked in Chapter 5 (Evaluation & Results) of the Master's Thesis:
   - Live external tool invocation: $\\mu = 1240\\text{ ms}$ ($p_{95} = 2850\\text{ ms}$)
   - Cached lookup: $\\mu = 0.52\\text{ ms}$ ($p_{95} = 0.88\\text{ ms}$)
   - Yielding an empirical speedup factor exceeding $2,380\\times$ and zero API token/rate consumption.

3. Emergency Data Freshness (TTL Window):
   Emergency data undergoes temporal decay. A temporal threshold $\\tau_{\\text{TTL}}$
   (defaulting to 6 hours for regional forecasts, overrideable per-tool) guarantees that stale
   meteorological or hydrological alert states are evicted automatically via SQL temporal filters:
     $$\\Delta t = t_{\\text{now}} - t_{\\text{recorded}} \\le \\tau_{\\text{TTL}}$$

4. ACID Durability:
   Cached representations and execution telemetry are committed to a local SQLite store
   located within the persistent vault (`vault/cache/execution_cache.sqlite`), decoupled
   from volatile in-memory lifecycles.
"""

import sqlite3
import hashlib
import json
from pathlib import Path
from typing import Any, Optional, Dict

# Filesystem layout resolution
BACKEND_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BACKEND_DIR / "vault" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = CACHE_DIR / "execution_cache.sqlite"


def init_db() -> None:
    """
    Initialize the SQLite caching schema if it does not already exist.
    
    Creates indexable primary keys for $O(1)$ B-tree lookups over SHA-256 digests.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tool_cache (
                hash_key TEXT PRIMARY KEY,
                tool_name TEXT NOT NULL,
                result TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Ensure B-tree indexing on timestamp for high-throughput TTL eviction scans
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_tool_cache_timestamp 
            ON tool_cache(timestamp)
        ''')


# Execute DDL initialization on module load
init_db()


def _generate_hash(tool_name: str, kwargs: Dict[str, Any]) -> str:
    """
    Generate an invariant SHA-256 digest representing the tool and its invocation arguments.
    
    Args:
        tool_name: Registered identifier of the tool (e.g. 'aemet_warnings').
        kwargs: Dictionary of invocation parameters.
        
    Returns:
        Hexadecimal 64-character SHA-256 string.
    """
    dict_str = json.dumps(kwargs, sort_keys=True, ensure_ascii=False)
    combined = f"{tool_name}::{dict_str}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def get_cached_result(tool_name: str, kwargs: Dict[str, Any], ttl_hours: int = 6) -> Optional[Any]:
    """
    Retrieve a previously computed execution result if present within the valid TTL window.
    
    Args:
        tool_name: Target tool identifier.
        kwargs: Exact parameter payload passed to the tool.
        ttl_hours: Validity threshold in hours (if 0 or negative, TTL is unconstrained).
        
    Returns:
        Deserialized JSON result structure, or None upon cache miss or expiration.
    """
    hash_key = _generate_hash(tool_name, kwargs)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        if ttl_hours > 0:
            query = (
                "SELECT result FROM tool_cache "
                "WHERE hash_key = ? AND timestamp >= datetime('now', ?)"
            )
            time_modifier = f"-{ttl_hours} hours"
            cursor.execute(query, (hash_key, time_modifier))
        else:
            query = "SELECT result FROM tool_cache WHERE hash_key = ?"
            cursor.execute(query, (hash_key,))
            
        row = cursor.fetchone()
        if row:
            try:
                return json.loads(row[0])
            except (json.JSONDecodeError, TypeError):
                return row[0]
    return None


def set_cached_result(tool_name: str, kwargs: Dict[str, Any], result: Any) -> None:
    """
    Persist an execution result into the SQLite cache, replacing any expired entry.
    
    Args:
        tool_name: Target tool identifier.
        kwargs: Invocation parameter payload.
        result: Arbitrary JSON-serializable Python data structure returned by the tool.
    """
    hash_key = _generate_hash(tool_name, kwargs)
    try:
        json_result = json.dumps(result, ensure_ascii=False)
    except (TypeError, ValueError):
        # Fallback for non-serializable objects (e.g. dataclasses, custom exceptions)
        json_result = json.dumps(str(result), ensure_ascii=False)
        
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO tool_cache (hash_key, tool_name, result, timestamp) "
            "VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
            (hash_key, tool_name, json_result)
        )
