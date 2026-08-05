import os
import sys
import json
import argparse
from typing import Dict, Any
from dotenv import load_dotenv

# Load env vars
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.core.planner import generate_plan
from backend.core.orchestrator import execute_plan
from backend.core.synthesis import generate_synthesis
from backend.core.llm import LLMClient

# Tests definition
TESTS = [
    {
        "test_name": "Test 1: Multi-Hazard Municipal Profile",
        "prompt": "Analyze the risk in San Vicente del Raspeig: Find the population by gender, look up the flood hazard mapping data (PATRICOVA), and check the historical seismic catalog for earthquakes greater than magnitude 2.0 in the ALACANT province. Summarize the combined risk profile."
    },
    {
        "test_name": "Test 2: Live Weather vs Static Risk",
        "prompt": "Cross-reference the current AEMET daily weather forecast for 'San Vicente del Raspeig' with the 'riesgo_inundaciones.csv' file to see if the current weather exacerbates any known flood risks."
    },
    {
        "test_name": "Test 3: Graph Reasoning (Neo4j)",
        "prompt": "Query the Neo4j graph database to find all emergency policies or nodes that are connected to 'Flood' or 'Inundacion' risks."
    },
    {
        "test_name": "Test 4: Seismic Statistical Aggregation",
        "prompt": "Using the local historical seismic catalog, what is the highest magnitude earthquake ever recorded in the 'ALACANT' province?"
    },
    {
        "test_name": "Test 5: Cadastral Extrema (Google Drive)",
        "prompt": "Check the Catastro CSV file on Google Drive for San Vicente. Sort the file to find the row with the highest value (e.g., largest parcel or highest value) and tell me its details."
    },
    {
        "test_name": "Test 6: Live Seismic vs Historical",
        "prompt": "Check the live SISCOVA earthquakes API for any recent events. Then, compare the magnitude of the most recent live event with the average magnitude of historical earthquakes in the ALACANT province."
    },
    {
        "test_name": "Test 7: Budget Analysis (Google Drive)",
        "prompt": "Find the Presupuestos (Budgets) CSV file in Google Drive. Tell me what the highest budget allocation is for San Vicente."
    },
    {
        "test_name": "Test 8: Unemployment Demographics (Google Drive)",
        "prompt": "Look at the 'paro' (unemployment) statistics on Google Drive for San Vicente. Extract the most recent unemployment figures."
    },
    {
        "test_name": "Test 9: Emergency Protocol (PDF Search)",
        "prompt": "Search the local vault for the exact evacuation protocols or safety guidelines during a Wildfire (Incendio Forestal) according to the PAM documents."
    },
    {
        "test_name": "Test 10: Multi-CSV Math (Google Drive)",
        "prompt": "Fetch the total population of San Vicente from the demographics CSV on Google Drive, and cross-reference it with the number of homes or parcels from the Viviendas/Catastro CSV to summarize the housing density."
    }
]

def evaluate_run(prompt: str, plan: list, execution: list, answer: str) -> Dict[str, Any]:
    llm = LLMClient(models=["gemini-2.5-flash", "gemini-2.5-pro"])
    
    eval_prompt = f"""You are an expert evaluator grading an AI agent's execution.
Please evaluate if the agent correctly answered the user prompt by successfully pulling the right data using tools, executing without errors, and synthesizing a correct answer.

User Prompt: "{prompt}"

Generated Plan:
{json.dumps(plan, indent=2)}

Execution Results (Tool Outputs):
{json.dumps(execution, indent=2)}

Synthesized Answer:
{answer}

Evaluate based on:
1. Did the plan correctly identify the right tools to use?
2. Did the execution complete without Python/Tool errors? (Look closely at Execution Results for "error" or traceback).
3. Did the Synthesized Answer directly and factually address the User Prompt based on the data pulled?

Respond in the following JSON format ONLY:
```json
{{
  "is_correct": true/false,
  "feedback": "Detailed explanation of why it passed or failed. If it failed, state exactly what went wrong (e.g., wrong tool used, tool returned error, synthesis hallucinated)."
}}
```
"""
    try:
        return llm.generate_json(eval_prompt)
    except Exception as e:
        return {"is_correct": False, "feedback": f"Evaluator failed to run: {e}"}

def run_single_test(test_idx: int):
    if test_idx < 1 or test_idx > len(TESTS):
        print(f"Invalid test index {test_idx}. Must be between 1 and {len(TESTS)}.")
        return
        
    test = TESTS[test_idx - 1]
    print(f"\n========== RUNNING {test['test_name']} ==========")
    print(f"Prompt: {test['prompt']}\n")
    
    try:
        print("[1] Generating Plan...")
        steps = generate_plan(test['prompt'])
        print(f"Plan steps generated: {len(steps)}")
        
        print("\n[2] Executing Plan...")
        executed_plan = execute_plan(steps)
        
        print("\n[3] Synthesizing Answer...")
        reply = generate_synthesis(test['prompt'], executed_plan)
        print(f"\nFinal Answer:\n{reply}\n")
        
        print("\n[4] Evaluating Result...")
        evaluation = evaluate_run(test['prompt'], steps, executed_plan, reply)
        
        print("\n========== EVALUATION RESULT ==========")
        print(f"Passed: {evaluation.get('is_correct', False)}")
        print(f"Feedback: {evaluation.get('feedback', 'No feedback provided.')}")
        
    except Exception as e:
        print(f"\n[!] CRITICAL FAILURE DURING EXECUTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", type=int, required=True, help="Test number to run (1-10)")
    args = parser.parse_args()
    
    run_single_test(args.test)
