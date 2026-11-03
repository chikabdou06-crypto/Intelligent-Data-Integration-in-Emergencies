"""
Conversational Session Memory & Sliding-Window Context Store.
============================================================

Academic Framework & Systemic Context:
--------------------------------------
In interactive emergency advisory systems, multi-turn citizen interactions require
conversational continuity (e.g., "What about my elderly parents in Catarroja?" followed
by "Are roads accessible there?"). However, injecting unbounded conversational history into
LLM prompts causes:
1. Context Window Saturation: Exceeding token limits and driving up inference latency.
2. Attention Diffusion: Distracting the Planner from current emergency sensory data.
3. Redundancy Amplification: Re-processing verbose previous recommendations.

This module implements a bounded Sliding-Window Conversational Memory:
- State Maintenance: Per-session dictionary storing ordered `(user, assistant)` dialog turns.
- Window Size: $k = 5$ exchanges ($2k = 10$ individual dialogue turns).
- Pruning Heuristic: Truncates historical assistant outputs to $\\le 400$ characters when
  formatting for prompt injection, preserving user intent while reserving maximum prompt
  bandwidth for real-time tool observation payloads.
"""

import uuid
from collections import defaultdict
from typing import Dict, List

MAX_EXCHANGES: int = 5  # Retain the most recent 5 dialogue pairs (10 messages)


class ConversationMemory:
    """
    Thread-safe in-memory sliding-window store indexed by session identifier.
    """

    def __init__(self, max_exchanges: int = MAX_EXCHANGES) -> None:
        self._store: Dict[str, List[Dict[str, str]]] = defaultdict(list)
        self._max = max_exchanges

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Return the raw chronological turn history for a given session.
        
        Args:
            session_id: Unique session UUID string.
            
        Returns:
            List of message dictionaries with 'role' and 'content' keys.
        """
        return list(self._store.get(session_id, []))

    def add_exchange(self, session_id: str, user_msg: str, assistant_msg: str) -> None:
        """
        Append an exchange pair and enforce sliding window bounds.
        
        Args:
            session_id: Unique session UUID.
            user_msg: Citizen query or prompt string.
            assistant_msg: Agent synthesized response.
        """
        history = self._store[session_id]
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": assistant_msg})

        # Trim to the configured sliding window maximum
        max_messages = self._max * 2
        if len(history) > max_messages:
            self._store[session_id] = history[-max_messages:]

    def clear(self, session_id: str) -> None:
        """
        Evict a session's history upon dialogue conclusion or citizen reset.
        
        Args:
            session_id: Target session UUID.
        """
        self._store.pop(session_id, None)

    @staticmethod
    def new_session_id() -> str:
        """
        Generate a cryptographically random 12-character hexadecimal session identifier.
        """
        return uuid.uuid4().hex[:12]

    def format_for_prompt(self, session_id: str) -> str:
        """
        Format recent conversation history into an injection-ready prompt block.
        
        Caps historical assistant replies at 400 characters to prevent prompt bloat.
        
        Args:
            session_id: Unique session UUID.
            
        Returns:
            Formatted plaintext string block, or empty string if no history exists.
        """
        history = self.get_history(session_id)
        if not history:
            return ""

        lines = ["=== CONVERSATION HISTORY (previous messages in this session) ==="]
        for msg in history:
            role_label = "User" if msg["role"] == "user" else "Assistant"
            content = msg["content"]
            # Prune previous assistant text to ensure fresh observations dominate the attention head
            if len(content) > 400:
                content = content[:400] + "…"
            lines.append(f"{role_label}: {content}")
        lines.append("=== END CONVERSATION HISTORY ===\n")
        return "\n".join(lines)


# Singleton instance shared across the FastAPI web tier and background pipelines
memory = ConversationMemory()
