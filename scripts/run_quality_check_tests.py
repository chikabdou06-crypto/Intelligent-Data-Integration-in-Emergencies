import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from backend.core.planner import generate_plan
from backend.core.orchestrator import execute_plan
from backend.core.synthesis import generate_synthesis
from backend.mcp_core.mcp_client import close_mcp_client

# A robust mix of 3 prompts testing all APIs, web search, and data crossing (Limited to 3 to avoid Google API Rate Limits)
PROMPTS = [
    "Search the web for the latest news on 'DANA Valencia' from this week and summarize it.",
    "Look up the coordinates for 'Alicante' and check the Patricova flood risk for that exact location.",
    "What are the current active weather warnings for Valencia right now? Keep it short."
]

def run_quality_check():
    print(f"\n========================================================")
    print(f"STARTING QUALITY CHECK AUTOMATION ({len(PROMPTS)} PROMPTS)")
    print(f"========================================================")
    
    report_path = Path(__file__).parent.parent / "quality_check_report.md"
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Agent Quality Check Report\n\n")
        
        for i, prompt in enumerate(PROMPTS, 1):
            print(f"\n--- Running Prompt {i}/{len(PROMPTS)} ---")
            print(f"USER: {prompt}")
            
            f.write(f"## Prompt {i}\n**USER:** `{prompt}`\n\n")
            
            try:
                # 1. Plan
                steps = generate_plan(prompt)
                f.write("### 1. Generated Plan\n```json\n" + json.dumps(steps, indent=2) + "\n```\n\n")
                
                # 2. Execute
                executed_plan = execute_plan(steps)
                
                # 3. Synthesize
                reply = generate_synthesis(prompt, executed_plan)
                
                f.write("### 2. Final Answer\n" + reply + "\n\n")
                f.write("---\n\n")
                
                print("[SUCCESS] Answer generated.")
                
            except Exception as e:
                print(f"[ERROR] {e}")
                f.write(f"### [ERROR] Pipeline Failed\n```\n{e}\n```\n\n---\n\n")

    print(f"\n========================================================")
    print(f"QUALITY CHECK COMPLETE. Report saved to: {report_path.name}")
    print(f"========================================================")

if __name__ == "__main__":
    try:
        run_quality_check()
    finally:
        close_mcp_client()
