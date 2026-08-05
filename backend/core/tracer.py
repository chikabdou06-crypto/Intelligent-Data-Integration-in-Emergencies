"""
Agent Trace Logger.

Logs every plan-execute-synthesize cycle to a SQLite table so you can
inspect, debug, and report on every interaction the agent has ever had.
"""
import json
import sqlite3
import time
from pathlib import Path

# Re-use the same SQLite database that the execution cache already lives in.
BACKEND_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BACKEND_DIR / "vault" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = CACHE_DIR / "execution_cache.sqlite"


def _init_traces_table():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_traces (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT,
                timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_prompt TEXT,
                plan_json   TEXT,
                executed_json TEXT,
                synthesis   TEXT,
                tools_used  TEXT,
                retry_count INTEGER DEFAULT 0,
                duration_ms INTEGER,
                error       TEXT
            )
        """)


# Create the table on import
_init_traces_table()


def log_trace(
    session_id: str,
    user_prompt: str,
    plan: list,
    executed: list,
    synthesis: str,
    tools_used: list[str],
    retry_count: int = 0,
    duration_ms: int = 0,
    error: str | None = None,
):
    """Persist one full agent cycle as a trace row."""
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
        print(f"[Tracer] Warning: failed to log trace: {e}")


def get_traces(limit: int = 50) -> list[dict]:
    """Return the most recent *limit* traces, newest first."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM agent_traces ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        print(f"[Tracer] Warning: failed to read traces: {e}")
        return []
