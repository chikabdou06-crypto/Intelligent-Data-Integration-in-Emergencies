import os
import sys
import time
from backend.core.network_patch import apply_network_patches

# Apply network patches very early
apply_network_patches()
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[App] Initializing MCP Client connection...")
    from backend.mcp_core.mcp_client import init_mcp_client, close_mcp_client
    init_mcp_client()
    yield
    print("[App] Shutting down MCP Client connection...")
    close_mcp_client()

# Fix paths
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Load Env
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from backend.core.planner import generate_plan
from backend.core.orchestrator import execute_plan
from backend.core.synthesis import generate_synthesis
from backend.core.memory import memory
from backend.core.tracer import log_trace, get_traces

app = FastAPI(title="ToolUniverse RAG Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/tools")
def get_tools():
    """Returns the schemas for all registered tools to the frontend via MCP."""
    tools = []
    try:
        from backend.mcp_core.mcp_client import get_mcp_client
        mcp = get_mcp_client()
        mcp_tools = mcp.get_tools()
        for tool in mcp_tools.tools:
            # Reconstruct the schema to match what the frontend expects
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            })
    except Exception as e:
        print(f"[Error] Failed to fetch tools for frontend: {e}")
        
    return {"tools": tools}

@app.get("/api/traces")
def api_get_traces(limit: int = 50):
    """Returns the most recent agent traces for observability."""
    return {"traces": get_traces(limit=limit)}

@app.get("/api/csv-data")
def api_get_csv_data(file: str = ""):
    """Returns available CSV files and data for the requested CSV file."""
    try:
        from backend.tools.local.csv_reader import list_available_csvs, read_csv_data
        csv_list = list_available_csvs()
        selected = file
        if not selected and csv_list and "available_files" in csv_list and csv_list["available_files"]:
            selected = list(csv_list["available_files"].keys())[0]
        elif not selected:
            selected = "company_sales.csv"
            
        data = read_csv_data(selected, max_rows=100) if selected else None
        return {
            "csv_list": csv_list,
            "selected_file": selected,
            "default_data": data
        }
    except Exception as e:
        print(f"[Error] /api/csv-data failed: {e}")
        return {"error": str(e), "csv_list": {}, "selected_file": file, "default_data": None}

@app.get("/api/providers/status")
def api_get_providers_status():
    """Returns real-time status of cloud and local LLM providers."""
    from backend.core.llm import get_providers_status
    return get_providers_status()

@app.post("/api/providers/select")
async def api_select_provider(request: Request):
    """Allows toggling between Auto fallback, Force Gemini, or Force Ollama."""
    from backend.core.llm import set_active_mode, get_active_mode
    try:
        payload = await request.json()
        mode = payload.get("mode", "auto")
        if set_active_mode(mode):
            return {"status": "success", "mode": get_active_mode()}
        return JSONResponse({"error": f"Invalid mode '{mode}'"}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

from fastapi.concurrency import run_in_threadpool

@app.post("/api/chat")
async def chat(request: Request):
    """The main entrypoint for the Agent cycle."""
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON payload."}, status_code=400)
        
    prompt = payload.get("message", "")
    if not prompt:
        return JSONResponse({"error": "Prompt cannot be empty."}, status_code=400)

    # Session management
    session_id = payload.get("session_id") or memory.new_session_id()
    
    print(f"\n[Agent Prompt] -> {prompt}  (session: {session_id})")
    
    def run_agent_sync():
        start_time = time.time()
        current_prompt = prompt
        max_retries = 2
        retry_count = 0
        
        # Fetch conversation history for this session
        conversation_history = memory.format_for_prompt(session_id)
        
        for attempt in range(max_retries + 1):
            # 1. Plan (with memory context)
            steps = generate_plan(current_prompt, conversation_history=conversation_history)
            print(f"[Plan] Attempt {attempt+1}/{max_retries+1} | {len(steps)} steps: {[s.get('tool') for s in steps]}")
            
            # 2. Execute
            executed_plan = execute_plan(steps)
            
            # Check for errors
            has_error = False
            for step in executed_plan:
                res = step.get("result")
                if step.get("error") or (isinstance(res, dict) and res.get("status") == "error"):
                    has_error = True
                    step["error"] = True  # Normalize for the logic below
                    break
            
            if not has_error or attempt == max_retries:
                # 3. Synthesize
                reply = generate_synthesis(prompt, executed_plan)  # Always use original prompt
                duration_ms = int((time.time() - start_time) * 1000)
                
                # 4. Save to memory
                memory.add_exchange(session_id, prompt, reply)
                
                # 5. Log trace
                tools_used = [s["tool"] for s in executed_plan if s.get("tool") != "general"]
                log_trace(
                    session_id=session_id,
                    user_prompt=prompt,
                    plan=steps,
                    executed=executed_plan,
                    synthesis=reply,
                    tools_used=tools_used,
                    retry_count=retry_count,
                    duration_ms=duration_ms,
                    error=None if not has_error else "Exhausted retries",
                )
                
                return steps, executed_plan, reply
                
            # If error, build a correction prompt for the LLM Judge
            retry_count += 1
            print(f"[Self-Correction] Attempt {attempt+1} failed. Triggering LLM Judge rewrite...")
            error_details = []
            for s in executed_plan:
                if s.get("error"):
                    err_msg = s.get("result", {}).get("error_message", "Unknown error")
                    error_details.append(f"- Tool '{s['tool']}' failed with error: {err_msg}")
                    
            current_prompt = (
                f"Original Request: {prompt}\n\n"
                f"PREVIOUS ATTEMPT FAILED. The execution returned these errors:\n"
                + "\n".join(error_details) + "\n\n"
                f"CRITICAL FIX REQUIRED: Rewrite your JSON plan to fix the errors above. "
                f"If you hallucinated a parameter, double-check the arguments. "
                f"If $PREV failed, it means you tried to guess the answer instead of correctly chaining the tool outputs. Wait for data!"
            )
            
        return steps, executed_plan, generate_synthesis(prompt, executed_plan)

    try:
        steps, executed_plan, reply = await run_in_threadpool(run_agent_sync)
        tools_used = [s["tool"] for s in executed_plan if s.get("tool") != "general"]
        
        primary_tool = tools_used[0] if len(tools_used) == 1 else ("multi_tool" if tools_used else "general")
        
        return {
            "reply": reply,
            "session_id": session_id,
            "tool_used": primary_tool,
            "tools_used": tools_used,
            "plan": steps,
            "tool_results": executed_plan,
            "tool_data": executed_plan[-1].get("result") if executed_plan else None,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse({"error": f"Internal Agent Error: {str(e)}"}, status_code=500)

# Serve static frontend (mount last as catch-all)
frontend_dir = PROJECT_ROOT / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
else:
    print("[Warning] Frontend directory not found.")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"\nStarting FastAPI server on http://localhost:{port}")
    uvicorn.run("backend.app:app", host="0.0.0.0", port=port, reload=True)

