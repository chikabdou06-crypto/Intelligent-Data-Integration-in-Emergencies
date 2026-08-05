import sys
from pathlib import Path

# Add project root to path (4 levels up)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from backend.core.planner import generate_plan
from backend.core.orchestrator import execute_plan
from backend.core.synthesis import generate_synthesis

prompts = [
    # ULTIMATE CSV BOSS TEST: 3-CSV Join & Logic
    "Find the municipality ('nombre') with the highest number of 'viviendas_totales' in Info_Municipios.csv. Then calculate its total sum of 'total Paro Registrado' in paro_2008_2025.csv using the 'Municipio' column. Finally, look up the demographic data for that exact same municipality in poblacion_segun_sexo.csv using the 'municipio' column, and tell me exactly how many 'hombres' (men) lived there in the year 2024."
]

import time
for p in prompts:
    print("\n" + "="*80)
    print(f"PROMPT: {p}")
    print("="*80)
    
    try:
        print("\n[1] GENERATING PLAN...")
        plan = generate_plan(p)
        for step in plan:
            print(f"  -> {step}")
            
        print("\n[2] EXECUTING PLAN...")
        results = execute_plan(plan)
        for res in results:
            tool = res.get('tool')
            args = res.get('arguments')
            out = res.get('result')
            print(f"  -> [{tool}] called with args {args}")
            print(f"     Output: {str(out)[:200]}...")
            
        print("\n[3] SYNTHESIZING RESPONSE...")
        synth = generate_synthesis(p, results)
        print(f"\nFINAL OUTPUT:\n{synth}")
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
    time.sleep(35)
