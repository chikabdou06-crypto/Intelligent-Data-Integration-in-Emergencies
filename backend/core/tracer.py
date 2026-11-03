"""
Agent Execution Tracer & Regulatory Audit Persistence.
======================================================

Academic Framework & Systemic Context:
--------------------------------------
Under European Union and Spanish Civil Protection directives (e.g., Ley 17/2015 del Sistema
Nacional de Protección Civil), algorithmic advisory systems deployed in critical life-safety
contexts must maintain rigorous explainability, traceability, and post-incident auditability.

When an autonomous agent advises a citizen on evacuation routing or flood shelter-in-place:
1. Every planning decision (the generated DAG) must be recorded verbatim.
2. Every external sensor/API observation retrieved must be stored immutably.
3. Every reflection iteration, fallback event, latency measurement, and final synthesis must
   be timestamped and linked to the active session.

This module implements an ACID-compliant Audit Trail in SQLite:
- Table: `agent_traces`
- Attributes: `(id, session_id, timestamp, user_prompt, plan_json, executed_json, synthesis,
               tools_used, retry_count, duration_ms, error)`
- Purpose: Enables evaluators, tribunal judges, and municipal auditors to inspect, verify,
  and benchmark system behavior historically or post-crisis.
"""

import json
import sqlite3
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Resolve persistent vault SQLite database location
BACKEND_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BACKEND_DIR / "vault" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = CACHE_DIR / "execution_cache.sqlite"


def _init_traces_table() -> None:
    """
    Initialize the audit traces table and associated performance indexes.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_traces (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id    TEXT NOT NULL,
                timestamp     DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_prompt   TEXT NOT NULL,
                plan_json     TEXT NOT NULL,
                executed_json TEXT NOT NULL,
                synthesis     TEXT NOT NULL,
                tools_used    TEXT NOT NULL,
                retry_count   INTEGER DEFAULT 0,
                duration_ms   INTEGER DEFAULT 0,
                error         TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_traces_session 
            ON agent_traces(session_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_traces_timestamp 
            ON agent_traces(timestamp)
        """)


# Ensure schema creation on module import
_init_traces_table()


def log_trace(
    session_id: str,
    user_prompt: str,
    plan: list,
    executed: list,
    synthesis: str,
    tools_used: List[str],
    retry_count: int = 0,
    duration_ms: int = 0,
    error: Optional[str] = None,
) -> None:
    """
    Persist an entire Plan-and-Solve execution cycle into the audit trail.
    
    Args:
        session_id: Unique conversational identifier.
        user_prompt: Verbatim natural language query from the user.
        plan: List of planned DAG steps emitted by the Planner.
        executed: Full list of step outcomes with raw sensor observations.
        synthesis: Final natural language guidance provided to the user.
        tools_used: List of tool names invoked during DAG execution.
        retry_count: Number of reflection loop correction passes required.
        duration_ms: Total elapsed execution wall-clock time in milliseconds.
        error: Detailed error description string if the pipeline encountered an unrecoverable failure.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                """
                INSERT INTO agent_traces
                    (session_id, user_prompt, plan_json, executed_json, synthesis,
                     tools_used, retry_count, duration_ms, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    user_prompt,
                    json.dumps(plan, ensure_ascii=False),
                    json.dumps(executed, ensure_ascii=False, default=str),
                    synthesis,
                    ",".join(tools_used),
                    retry_count,
                    duration_ms,
                    error,
                ),
            )
    except Exception as e:
        print(f"[Tracer] Warning: Failed to persist execution audit trace: {e}")


def get_traces(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieve historical execution traces ordered chronologically (newest first).
    
    Args:
        limit: Maximum number of trace records to retrieve.
        
    Returns:
        List of trace dictionaries representing historical agent executions.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM agent_traces ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        print(f"[Tracer] Warning: Failed to query execution audit traces: {e}")
        return []
