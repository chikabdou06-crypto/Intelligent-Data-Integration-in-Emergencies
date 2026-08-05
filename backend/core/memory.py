"""
Conversational Memory Store.

Keeps a sliding window of recent exchanges per session so the Planner
can see what was discussed in previous turns.
"""
import uuid
from collections import defaultdict

MAX_EXCHANGES = 5  # Keep the last 5 user/assistant pairs (10 messages)


class ConversationMemory:
    """In-memory, per-session conversation history."""

    def __init__(self, max_exchanges: int = MAX_EXCHANGES):
        self._store: dict[str, list[dict]] = defaultdict(list)
        self._max = max_exchanges

    # ── public API ──────────────────────────────────────────────────────

    def get_history(self, session_id: str) -> list[dict]:
        """Return the full history list for *session_id*."""
        return list(self._store.get(session_id, []))

    def add_exchange(self, session_id: str, user_msg: str, assistant_msg: str):
        """Append one user/assistant exchange and enforce the sliding window."""
        history = self._store[session_id]
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": assistant_msg})

        # Trim to the last MAX_EXCHANGES pairs (each pair = 2 messages)
        max_messages = self._max * 2
        if len(history) > max_messages:
            self._store[session_id] = history[-max_messages:]

    def clear(self, session_id: str):
        """Wipe the history for a session."""
        self._store.pop(session_id, None)

    @staticmethod
    def new_session_id() -> str:
        return uuid.uuid4().hex[:12]

    def format_for_prompt(self, session_id: str) -> str:
        """
        Render the history as a plain-text block ready to inject into an LLM
        system prompt.  Returns an empty string when there is no history.
        """
        history = self.get_history(session_id)
        if not history:
            return ""

        lines = ["=== CONVERSATION HISTORY (previous messages in this session) ==="]
        for msg in history:
            role_label = "User" if msg["role"] == "user" else "Assistant"
            # Truncate very long assistant replies to keep context lean
            content = msg["content"]
            if len(content) > 400:
                content = content[:400] + "…"
            lines.append(f"{role_label}: {content}")
        lines.append("=== END CONVERSATION HISTORY ===\n")
        return "\n".join(lines)


# ── Singleton instance (shared across the app) ─────────────────────────
memory = ConversationMemory()
