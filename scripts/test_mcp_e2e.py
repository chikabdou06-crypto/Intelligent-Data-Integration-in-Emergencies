import sys
from pathlib import Path
import asyncio

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from backend.core.planner import generate_plan
from backend.core.orchestrator import execute_plan
from backend.mcp_core.mcp_client import close_mcp_client
import json

def test_mcp_integration():
    try:
        print("1. Generating plan via MCP...")
        # A simple prompt that should trigger a known tool like vault_pdf_search or ine_search_operations
        prompt = "Search for 'DANA' in the BOE summary for 20240102"
        plan = generate_plan(prompt)
        
        print("\n[PLAN]")
        print(json.dumps(plan, indent=2))
        
        if plan and plan[0].get("tool") != "general":
            print("\n2. Executing plan via MCP...")
            executed = execute_plan(plan)
            print("\n[EXECUTED]")
            for step in executed:
                res = step.get("result", {})
                status = res.get("status", "unknown") if isinstance(res, dict) else "ok"
                print(f"Tool: {step['tool']} -> Status: {status}")
        else:
            print("No actionable plan generated.")
            
    finally:
        print("\nCleaning up MCP client...")
        close_mcp_client()

if __name__ == "__main__":
    test_mcp_integration()
