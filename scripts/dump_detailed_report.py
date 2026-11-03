import os
import sys
import json
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from backend.core.network_patch import apply_network_patches
apply_network_patches()

from backend.core.planner import generate_plan
from backend.core.orchestrator import execute_plan
from backend.core.synthesis import generate_synthesis
from backend.mcp_core.mcp_client import init_mcp_client, close_mcp_client

def generate_detailed_report():
    eval_file = PROJECT_ROOT / "scripts" / "eval_cases.json"
    report_file = PROJECT_ROOT / "scripts" / "results" / "detailed_test_report.md"
    
    with open(eval_file, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    init_mcp_client()
    time.sleep(2)

    report_lines = [
        "# Detailed Agent Architecture Test Report",
        "This report contains the raw JSON output of the Planner and the final Synthesizer response for each test prompt.",
        "---"
    ]

    try:
        for i, test in enumerate(test_cases, 1):
            prompt = test.get("prompt", "")
            name = test.get("name", "")
            
            report_lines.append(f"## Test {i}: {name}")
            report_lines.append(f"**User Prompt:** `{prompt}`\n")
            
            # 1. Plan
            steps = generate_plan(prompt, conversation_history=[])
            
            report_lines.append("### 🧠 1. Planner JSON Output")
            report_lines.append("```json")
            report_lines.append(json.dumps(steps, indent=2, ensure_ascii=False))
            report_lines.append("```\n")
            
            # 2. Execute
            executed_plan = execute_plan(steps)
            
            # 3. Synthesize
            reply = generate_synthesis(prompt, executed_plan)
            
            report_lines.append("### 🗣️ 2. Synthesizer Final Response")
            report_lines.append(reply)
            report_lines.append("\n---\n")
            
            print(f"[Eval] Sleeping for 15s to respect Gemini API rate limits...")
            time.sleep(15)
            
    finally:
        close_mcp_client()

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
        
if __name__ == "__main__":
    generate_detailed_report()
