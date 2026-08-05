import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load env
project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(project_root / ".env")

print("1. Env loaded.")

from backend.core.planner import generate_plan
from backend.core.orchestrator import execute_plan

print("2. Imports done.")

def test():
    print("3. Starting generate_plan...")
    steps = generate_plan('Show me the lightning map in Spain')
    print(f"4. Plan generated: {steps}")
    
    print("5. Starting execute_plan...")
    executed = execute_plan(steps)
    print(f"6. Execution complete: {executed}")

if __name__ == "__main__":
    test()
