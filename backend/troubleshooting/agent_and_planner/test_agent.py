import subprocess
import time
import requests
import json

print("1. Starting Agent Server in background...")
server_proc = subprocess.Popen(
    ["python", "backend/app.py"],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
)
time.sleep(6)

def ask_agent(prompt, label=""):
    print(f"\n{'='*70}")
    if label:
        print(f"TEST: {label}")
    print(f"USER PROMPT: {prompt}")
    print(f"{'='*70}")
    try:
        resp = requests.post(
            "http://localhost:8000/api/chat",
            json={"message": prompt},
            timeout=120,
        )
        if resp.status_code != 200:
            print(f"HTTP Error {resp.status_code}: {resp.text[:500]}")
            return

        data = resp.json()
        print("\n[AGENT REPLY]")
        print(data.get("reply", "No reply field")[:2000])
        print("\n[TOOLS USED]", data.get("tools_used", []))
        print("[PLAN]")
        for step in data.get("plan", []):
            print(f"  - {step.get('tool')}: {json.dumps(step.get('arguments', {}), ensure_ascii=False)}")
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to server.")
    except Exception as e:
        print(f"ERROR: {e}")


# ── TEST 1: Geometry-heavy CSV that previously crashed ──
ask_agent(
    "Read 2 rows from codigos_postales.csv and show me the postal codes.",
    "GEOMETRY FIX — codigos_postales.csv should no longer crash"
)

# ── TEST 2: Aggregation using the new csv_aggregate tool ──
ask_agent(
    "What is the total number of robberies across all municipalities in criminalidad_convencional_robos.csv? Sum up q1, q2, q3, and q4 for all rows.",
    "AGGREGATION — csv_aggregate should process ALL 208 rows"
)

# ── TEST 3: Aggregation with group_by ──
ask_agent(
    "In criminalidad_convencional_robos.csv, give me the total robberies (sum of q1+q2+q3+q4) grouped by tipologia_penal.",
    "GROUPED AGGREGATION — csv_aggregate with group_by"
)

# ── TEST 4: Cross-file chaining with $PREV placeholder ──
ask_agent(
    "First, read 1 row from Distritos_censales_San_Vicente.csv to get a district name. Then search for that district name in Indicadores_demograficos_secciones.csv using the appropriate column.",
    "CROSS-REFERENCE — $PREV placeholder chaining"
)


print("\n\n3. Shutting down server...")
server_proc.terminate()
server_proc.wait()
print("All tests completed.")
