import sys
import json
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Import the core agent logic
from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")

from backend.core.planner import generate_plan
from backend.core.orchestrator import execute_plan
from backend.core.synthesis import generate_synthesis

def run_e2e_tests():
    questions = [
        "What is the flood risk in Valencia and are there any active AEMET warnings there?",
        "Search the vault for information about 'terremoto' and tell me the latest earthquakes recorded.",
        "Query the clean seismic catalog CSV for the most recent earthquakes in the province of Alicante with magnitude greater than 2.0."
    ]

    results = []

    for idx, q in enumerate(questions):
        print(f"Running Test {idx+1}/{len(questions)}...")
        try:
            # 1. Plan
            steps = generate_plan(q)
            # 2. Execute
            executed_plan = execute_plan(steps)
            # 3. Synthesize
            reply = generate_synthesis(q, executed_plan)
            
            # Extract tools used
            tools_used = [s.get("tool") for s in steps]
            primary_tool = tools_used[0] if tools_used else "general"

            results.append({
                "question": q,
                "plan": steps,
                "execution_trace": executed_plan,
                "final_answer": reply,
                "tools_used": tools_used
            })
        except Exception as e:
            results.append({
                "question": q,
                "error": str(e)
            })

    # Save results to a JSON file to format into markdown later
    with open("e2e_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    print("End-to-End testing complete. Results saved to e2e_results.json.")

if __name__ == "__main__":
    run_e2e_tests()
