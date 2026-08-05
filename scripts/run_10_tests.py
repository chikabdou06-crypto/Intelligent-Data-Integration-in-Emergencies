import os
import sys
import json
import time
from dotenv import load_dotenv

# Load env vars
load_dotenv(".env")

# Add backend to path
sys.path.insert(0, os.path.abspath("."))
from backend.core.planner import generate_plan
from backend.core.orchestrator import execute_plan
from backend.core.synthesis import generate_synthesis

prompts = [
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

output_file = os.path.abspath("docs/test_suite_results.md")
with open(output_file, "w", encoding="utf-8") as f:
    f.write("# Agent 10-Test Execution Suite\n\n")

for idx, p in enumerate(prompts):
    print(f"\nRunning {p['test_name']}...")
    try:
        steps = generate_plan(p['prompt'])
        executed_plan = execute_plan(steps)
        reply = generate_synthesis(p['prompt'], executed_plan)
        
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"## {p['test_name']}\n")
            f.write(f"**Prompt:** {p['prompt']}\n\n")
            f.write("### Generated Plan\n```json\n")
            f.write(json.dumps(steps, indent=2))
            f.write("\n```\n\n### Synthesized Reply\n")
            f.write(reply + "\n\n---\n\n")
            
        print(f"Success! {p['test_name']} saved to docs.")
    except Exception as e:
        print(f"Error in {p['test_name']}: {e}")
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"## {p['test_name']}\n**ERROR:** {str(e)}\n\n---\n\n")
            
    # Sleep to avoid hitting rate limits too fast
    time.sleep(10)

print(f"\nAll 10 tests completed! Results saved to {output_file}")
