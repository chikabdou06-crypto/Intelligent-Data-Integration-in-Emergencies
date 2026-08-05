import sys
from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from backend.core.planner import generate_plan
from backend.core.orchestrator import execute_plan
from backend.core.synthesis import generate_synthesis
from backend.mcp_core.mcp_client import close_mcp_client

def run_agent_interactive(prompt: str):
    print(f"\n========================================================")
    print(f"USER: {prompt}")
    print(f"========================================================")
    
    try:
        print("[1] Generating Plan via MCP...")
        steps = generate_plan(prompt)
        print("\n[PLAN]")
        print(json.dumps(steps, indent=2))
        
        print("\n[2] Executing Plan via MCP...")
        executed_plan = execute_plan(steps)
        
        print("\n[3] Synthesizing Final Answer...")
        reply = generate_synthesis(prompt, executed_plan)
        
        print("\n==================== AGENT REPLY ====================")
        print(reply)
        print("========================================================\n")
        
        return steps, reply
        
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    prompts = [
        "What is the average magnitude of earthquakes in Valencia according to the local CSV data?",
        "Please fetch the summary of the BOE document for 20240102."
    ]
    
    for p in prompts:
        run_agent_interactive(p)
        
    print("\nClosing MCP Client...")
    close_mcp_client()
