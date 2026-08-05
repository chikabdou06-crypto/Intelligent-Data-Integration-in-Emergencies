# Project Rules for AI Agents (AGENTS.md)

This file contains mandatory behavioral guidelines and execution rules for all AI models, agents, and subagents working in this workspace (`RAG_BASIC_TEST_LANGCHAIN`).

## 1. Zero-Blocking Server & Long-Running Command Rule (CRITICAL)
- **NEVER run servers or continuous scripts synchronously in the foreground.**
- Any command that starts a server (e.g., `uvicorn backend.app:app`, `python backend/app.py`, frontend dev servers, watchdog scripts) **MUST** be sent to the background immediately.
- When using `run_command` for servers or watchers, always set `WaitMsBeforeAsync` to a small value (e.g., 2000-3000ms) so the command detaches into a background task rather than hanging the IDE execution.

## 2. Preventing "Agent Execution Terminated" & Timeouts
- **Do NOT poll in loops:** Never write scripts or use tools in a tight polling loop to check server status or command completion.
- **Modular Execution:** Keep individual tool invocations and tasks bite-sized to avoid hitting IDE timeout limits or exceeding token windows.
- **Graceful Failures:** When encountering API rate limits (e.g., `429 RESOURCE_EXHAUSTED` from cloud LLM providers), fall back gracefully to local providers (such as Ollama on `localhost:11434`) rather than letting exceptions terminate the task.

## 3. RAG & Provider Guidelines
- All LLM interactions in `backend/core/` should respect the fallback hierarchy (Cloud -> HF -> Local Ollama).
- When modifying JSON schemas or MCP tool catalogs, ensure required imports (such as `import json`) are present to prevent silent initialization failures in `planner.py`.

## 4. Stopping the Server Before Core UI or Backend Changes (CRITICAL)
- **Always stop the server BEFORE modifying core UI or backend code:** Before making any changes to the core UI or backend server files, you MUST explicitly stop any running server processes (`app.py`, `uvicorn`, etc.) to prevent file lock issues, partial reload crashes, or state corruption.
- After completing the code changes and verifying syntax, restart the server in the background as per Rule 1.
