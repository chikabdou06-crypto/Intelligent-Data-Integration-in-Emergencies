import os
import sys
import json
import time
from pathlib import Path

# Add backend directory to sys.path so imports work correctly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load Env
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from backend.core.network_patch import apply_network_patches
# Apply network patches very early
apply_network_patches()

from backend.core.planner import generate_plan
from backend.core.orchestrator import execute_plan
from backend.core.synthesis import generate_synthesis
from backend.mcp_core.mcp_client import init_mcp_client, close_mcp_client

def run_evaluation():
    eval_file = PROJECT_ROOT / "scripts" / "eval_cases.json"
    report_file = PROJECT_ROOT / "scripts" / "results" / "eval_report.md"
    
    if not eval_file.exists():
        print(f"Error: {eval_file} not found.")
        return

    with open(eval_file, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    print("[Eval] Initializing MCP Client connection...")
    init_mcp_client()
    time.sleep(2) # Give MCP server a moment to boot

    report_lines = [
        "# Automated Agent Evaluation Report",
        f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Total Cases:** {len(test_cases)}",
        "---",
        ""
    ]
    
    success_count = 0

    try:
        for i, test in enumerate(test_cases, 1):
            name = test.get("name", f"Test {i}")
            prompt = test.get("prompt", "")
            expected_tools = set(test.get("expected_tools", []))
            
            print(f"\n[{i}/{len(test_cases)}] Running: {name}")
            print(f"Prompt: {prompt}")
            
            start_time = time.time()
            error_msg = None
            tools_called = set()
            reply = ""
            
            try:
                # 1. Plan
                steps = generate_plan(prompt, conversation_history=[])
                
                # 2. Execute
                executed_plan = execute_plan(steps)
                
                # Extract tools that were actually called
                for step in executed_plan:
                    tool_name = step.get("tool")
                    if tool_name:
                        tools_called.add(tool_name)
                    if step.get("error"):
                        error_msg = f"Error in tool {tool_name}: Execution failed."
                
                # 3. Synthesize
                reply = generate_synthesis(prompt, executed_plan)
                
            except Exception as e:
                error_msg = str(e)
            
            duration = round(time.time() - start_time, 2)
            
            # Check success condition
            # For this simple eval, success means it called at least one expected tool
            # or if expected_tools is empty, it shouldn't have crashed.
            if expected_tools:
                passed = bool(expected_tools.intersection(tools_called))
            else:
                passed = error_msg is None
                
            if passed:
                success_count += 1
                status = "✅ PASS"
            else:
                status = "❌ FAIL"
                
            # Formatting results
            report_lines.append(f"## {i}. {name} - {status}")
            report_lines.append(f"**Prompt:** `{prompt}`")
            report_lines.append(f"**Expected Tools:** {list(expected_tools)}")
            report_lines.append(f"**Actual Tools Called:** {list(tools_called)}")
            report_lines.append(f"**Execution Time:** {duration}s")
            if error_msg:
                report_lines.append(f"**Error:** {error_msg}")
            report_lines.append(f"**LLM Synthesis Snippet:**\n> {reply[:150].replace(chr(10), ' ')}...")
            report_lines.append("\n---")
            
    finally:
        print("\n[Eval] Shutting down MCP Client connection...")
        close_mcp_client()

    report_lines.insert(3, f"**Success Rate:** {success_count}/{len(test_cases)} ({round(success_count/len(test_cases)*100, 1)}%)")

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
        
    print(f"\n[Eval] Completed. Report saved to {report_file}")

if __name__ == "__main__":
    run_evaluation()
