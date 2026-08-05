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
        
        # Write the output to a file for easy reading
        with open(PROJECT_ROOT / "complex_prompt_result.md", "w", encoding="utf-8") as f:
            f.write(f"# Prompt Test Result\n\n**USER:** {prompt}\n\n")
            f.write("### 1. Generated Plan\n```json\n")
            f.write(json.dumps(steps, indent=2))
            f.write("\n```\n\n### 2. Final Answer\n\n")
            f.write(reply)
            f.write("\n")
            
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else "What are the current weather alerts and flood risks for Alicante right now, and what emergency protocols should I follow if my house is at risk?"
    run_agent_interactive(prompt)
    
    print("\nClosing MCP Client...")
    close_mcp_client()
