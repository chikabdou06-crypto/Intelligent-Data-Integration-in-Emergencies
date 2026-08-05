import sys
import os
import json
from pathlib import Path

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")

from backend.core.planner import generate_plan
from backend.core.orchestrator import execute_plan

def run_agent_sync_test(prompt: str):
    current_prompt = prompt
    max_retries = 2
    
    for attempt in range(max_retries + 1):
        print(f"\n--- Attempt {attempt + 1}/{max_retries + 1} ---")
        # 1. Plan
        steps = generate_plan(current_prompt)
        print(f"[Plan Generated]:")
        print(json.dumps(steps, indent=2))
        
        # 2. Execute
        print(f"\n[Executing Plan...]")
        executed_plan = execute_plan(steps)
        
        # Check for errors
        has_error = False
        for step in executed_plan:
            res = step.get("result")
            if step.get("error") or (isinstance(res, dict) and res.get("status") == "error"):
                has_error = True
                step["error"] = True
                break
        
        if not has_error or attempt == max_retries:
            if has_error:
                print(f"\n[FAILED] Max retries exhausted. Final plan still had errors.")
            else:
                print(f"\n[SUCCESS] Plan executed perfectly on attempt {attempt + 1}!")
            return steps, executed_plan
            
        # If error, build a correction prompt
        print(f"\n[ERROR DETECTED] Triggering Self-Correction LLM Judge...")
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

def main():
    print("==================================================")
    print("Testing Recursive Self-Correction Loop")
    print("==================================================")
    
    # We use a prompt that is known to cause a hallucinated tool or parameter.
    # The "$PREV" bug is tricky to reliably trigger in 1 try. Let's use a prompt that forces it to cross-reference.
    prompt = "Find the municipality with the highest flood risk from the local csv files, and then check its weather forecast."
    
    run_agent_sync_test(prompt)

if __name__ == "__main__":
    main()
