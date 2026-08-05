import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.core.planner import generate_plan
from backend.core.orchestrator import execute_plan
from backend.core.synthesis import generate_synthesis

def main():
    prompt = (
        "Check the historical normal temperature (normals) for Madrid and Barcelona, "
        "and also check their current live temperatures right now. "
        "Can you compare them and tell me which one is historically hotter in August (month 8), "
        "and which one is hotter right now?"
    )
    
    print(f"\n[USER PROMPT]: {prompt}\n")
    
    print("1. LLM PLANNER is thinking...")
    try:
        plan_json, raw_reply = generate_plan(prompt)
    except Exception as e:
        print(f"Error in planner: {e}")
        return
        
    print("\n--- RAW LLM PLANNER REASONING ---")
    print(raw_reply)
    print("---------------------------------\n")
    
    print("2. ORCHESTRATOR is executing tools...")
    try:
        executed_plan = execute_plan(plan_json.get("steps", []))
    except Exception as e:
        print(f"Error in orchestrator: {e}")
        return
    
    print("\n3. LLM SYNTHESIS is writing the final response...")
    try:
        final_markdown = generate_synthesis(prompt, executed_plan)
    except Exception as e:
        print(f"Error in synthesis: {e}")
        return
        
    print("\n==================================================")
    print("[ FINAL SYNTHESIZED RESPONSE ]")
    print("==================================================")
    print(final_markdown)

if __name__ == "__main__":
    main()
