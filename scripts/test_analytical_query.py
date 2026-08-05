import requests
import time

prompt = "Can you list what columns are in the paro_2008_2025.csv unemployment dataset?"
print(f"Sending POST /api/chat to http://localhost:8000 with message '{prompt}'...")
t0 = time.time()
try:
    r = requests.post(
        "http://localhost:8000/api/chat",
        json={"message": prompt},
        timeout=300
    )
    dur = time.time() - t0
    print(f"Completed in {dur:.2f}s - Status: {r.status_code}")
    data = r.json()
    print("Plan:", data.get("plan"))
    print("Tools used:", data.get("tools_used"))
    print("Reply:\n", data.get("reply"))
except Exception as e:
    dur = time.time() - t0
    print(f"FAILED after {dur:.2f}s:", e)
