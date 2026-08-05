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

def test_prompt(prompt_text: str, expected_tool: str = None, expected_param: str = None):
    print(f"\n========================================================")
    print(f"[TEST] Prompt: {prompt_text}")
    print(f"========================================================")
    
    try:
        steps = generate_plan(prompt_text)
        print("\n[PLAN GENERATED]")
        print(json.dumps(steps, indent=2))
        
        # Validation logic
        passed = True
        
        if expected_tool:
            tools_used = [s.get("tool") for s in steps]
            if expected_tool not in tools_used:
                print(f"[FAIL] Expected tool '{expected_tool}' but got {tools_used}")
                passed = False
            else:
                print(f"[PASS] Used expected tool: {expected_tool}")
                
        if expected_param:
            found_param = False
            for s in steps:
                if expected_param in s.get("arguments", {}):
                    found_param = True
                    break
            if not found_param:
                print(f"[FAIL] Expected parameter '{expected_param}' not found in any step.")
                passed = False
            else:
                print(f"[PASS] Used expected parameter: {expected_param}")
                
        if passed:
            print("[OVERALL: PASS]")
            return True
        else:
            print("[OVERALL: FAIL]")
            return False
            
    except Exception as e:
        print(f"[ERROR] Exception during planning: {e}")
        return False

def main():
    print("Starting Phase 2 LLM End-to-End Tests...")
    
    success = 0
    total = 0
    
    # Test 1: Cross-referencing CSV with AEMET (should use $PREV)
    prompt1 = "Find the municipality with the highest flood risk from the local csv files, and then check its weather forecast."
    if test_prompt(prompt1, expected_tool="csv_reader", expected_param="order_by"):
        success += 1
    total += 1
    
    # Test 2: Ensure csv_aggregate uses exact 'aggregate_columns' parameter, not 'column'
    prompt2 = "What is the average magnitude of earthquakes in Valencia? Use the local database."
    if test_prompt(prompt2, expected_tool="csv_aggregate", expected_param="aggregate_columns"):
        success += 1
    total += 1
    
    # Test 3: Google Drive RAG parameter checks
    prompt3 = "Get the employment statistics for San Vicente from Google Drive and filter for 2024."
    if test_prompt(prompt3, expected_tool="drive_read_sheet", expected_param="filename"):
        success += 1
    total += 1

    print(f"\nFinal Results: {success}/{total} tests passed.")
    
    # Write to file
    with open("phase2_test_results.json", "w") as f:
        json.dump({"total": total, "success": success}, f)

if __name__ == "__main__":
    main()
