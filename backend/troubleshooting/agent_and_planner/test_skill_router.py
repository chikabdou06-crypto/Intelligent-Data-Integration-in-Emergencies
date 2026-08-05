import sys
from pathlib import Path

# Add project root to path (4 levels up)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from backend.core.planner import discover_skills, select_relevant_skills

skills = discover_skills()
print(f"Total skills found: {len(skills)}")
for s in skills:
    print(f"  - {s['name']}: {s['description'][:70]}...")

print()

prompts = [
    "What is the price of Bitcoin?",
    "Find the municipality with the highest viviendas_totales in Info_Municipios.csv",
    "What nodes are connected in the Neo4j graph?",
    "Can I go to work today in Madrid?",
]

for p in prompts:
    selected = select_relevant_skills(p, skills)
    names = [s["name"] for s in selected]
    print(f'Prompt: "{p[:60]}"')
    print(f"  -> Skills injected: {names if names else '[none — clean prompt]'}")
    print()
