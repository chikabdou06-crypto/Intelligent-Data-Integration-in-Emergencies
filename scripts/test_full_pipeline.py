import sys
from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from backend.app import app

def run_test_prompts():
    print("Initializing FastAPI TestClient (this will start the MCP server via lifespan)...")
    with TestClient(app) as client:
        prompts = [
            "What is the average magnitude of earthquakes in Valencia according to the local CSV data?",
            "Search for 'DANA' in the BOE summary for 20240102.",
        ]
        
        results = []
        for p in prompts:
            print(f"\n========================================================")
            print(f"USER PROMPT: {p}")
            print(f"========================================================")
            
            response = client.post("/api/chat", json={"message": p, "session_id": "test_session_123"})
            
            if response.status_code == 200:
                data = response.json()
                print("\n[AGENT SYNTHESIS REPLY]")
                print(data.get("reply"))
                print("\n[PLAN]")
                print(json.dumps(data.get("plan"), indent=2))
                
                results.append({
                    "prompt": p,
                    "reply": data.get("reply"),
                    "plan": data.get("plan")
                })
            else:
                print(f"[ERROR] HTTP {response.status_code}: {response.text}")
                
        # Write results to a markdown file for the user to see easily
        with open(PROJECT_ROOT / "pipeline_test_results.md", "w", encoding="utf-8") as f:
            f.write("# Full Pipeline Test Results\n\n")
            for r in results:
                f.write(f"## Prompt\n> {r['prompt']}\n\n")
                f.write(f"### Generated Plan\n```json\n{json.dumps(r['plan'], indent=2)}\n```\n\n")
                f.write(f"### Final Answer\n{r['reply']}\n\n")
                f.write("---\n")
                
    print("\nTest completed. Results saved to pipeline_test_results.md")

if __name__ == "__main__":
    run_test_prompts()
