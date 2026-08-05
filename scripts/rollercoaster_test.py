import os
import sys
import json
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
        "prompt": "I need to analyze the risk in San Vicente del Raspeig. First, find out what the population by gender is. Then, look up the flood hazard mapping data for the same municipality. Finally, check the historical seismic catalog to see if there have been any earthquakes greater than magnitude 2.0 in the ALACANT province. Summarize the combined risk profile.",
        "why": "This forces the agent to cross-reference demographics (Google Drive CSV), natural hazard maps (Google Drive CSV), and the seismic catalog (Local Vault CSV) all in one go.",
        "expected_path": "vault_catalog -> drive_read_sheet (demographics) -> drive_read_sheet (flood hazard) -> csv_reader/aggregate (seismic) -> synthesis.",
        "expected_answer": "Provide the demographic breakdown, the flood hazard levels, the seismic activity count, and a synthesized risk profile."
    },
    {
        "prompt": "Cross-reference the current AEMET daily weather forecast for 'San Vicente del Raspeig' with the 'riesgo_inundaciones.csv' (flood risk) file to tell me if the current weather forecast exacerbates any known flood risks for that municipality.",
        "why": "This combines real-time live data (AEMET API) with static sandboxed data (Google Drive CSV) to assess a dynamic risk scenario.",
        "expected_path": "vault_catalog -> aemet_forecast -> drive_read_sheet (flood risk) -> synthesis.",
        "expected_answer": "Provide the live weather, extract the flood risk level from the CSV, and synthesize if the weather poses an immediate threat based on the static risk."
    }
]

for idx, p in enumerate(prompts):
    print(f"\n{'='*80}")
    print(f"ROLLERCOASTER TEST {idx+1}")
    print(f"{'='*80}")
    print(f"PROMPT: {p['prompt']}")
    print(f"WHY: {p['why']}")
    print(f"EXPECTED PATH: {p['expected_path']}")
    print(f"EXPECTED ANSWER: {p['expected_answer']}")
    print(f"{'-'*80}")
    
    try:
        print("Generating Plan...")
        steps = generate_plan(p['prompt'])
        print(f"Plan Steps Generated:\n{json.dumps(steps, indent=2)}")
        
        print("\nExecuting Plan...")
        executed_plan = execute_plan(steps)
        
        print("\nSynthesizing Reply...")
        reply = generate_synthesis(p['prompt'], executed_plan)
        print(f"\nACTUAL REPLY:\n{reply}\n")
    except Exception as e:
        print(f"Error testing prompt: {e}")

