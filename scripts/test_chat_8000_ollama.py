import requests
import time

print("Sending POST /api/chat to http://localhost:8000 with message 'hello'...")
t0 = time.time()
try:
    r = requests.post(
        "http://localhost:8000/api/chat",
        json={"message": "hello"},
        timeout=600
    )
    dur = time.time() - t0
    print(f"Completed in {dur:.2f}s - Status: {r.status_code}")
    print("Response JSON:", r.json())
except Exception as e:
    dur = time.time() - t0
    print(f"FAILED after {dur:.2f}s:", e)
