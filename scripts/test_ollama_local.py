import os
import requests
import json
import time
import sys

def test_ollama():
    print("1. Pinging Ollama directly...")
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        print(f"   [OK] Ollama is alive! Models: {len(resp.json().get('models', []))}")
    except Exception as e:
        print(f"   [FAIL] Could not reach Ollama at localhost:11434. Error: {e}")
        return False

    print("\n2. Testing direct generation with Ollama...")
    try:
        start = time.time()
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "qwen2.5:7b", "prompt": "Hello! Say 'Testing 123'", "stream": False},
            timeout=600
        )
        dur = time.time() - start
        print(f"   [OK] Generated in {dur:.2f}s: {resp.json().get('response', '').strip()}")
    except Exception as e:
        print(f"   [FAIL] Direct generation failed. Error: {e}")
        return False
        
    print("\n3. Testing FastAPI /api/chat endpoint with force Ollama...")
    try:
        # First, force ollama mode
        requests.post("http://localhost:8001/api/providers/select", json={"mode": "ollama"})
        
        # Now send chat
        start = time.time()
        resp = requests.post(
            "http://localhost:8001/api/chat",
            json={"message": "What is 2+2? Reply short."},
            timeout=600
        )
        dur = time.time() - start
        data = resp.json()
        print(f"   [OK] FastAPI replied in {dur:.2f}s: {data.get('reply', '').strip()[:100]}...")
    except Exception as e:
        print(f"   [FAIL] FastAPI /api/chat failed. Error: {e}")
        return False
        
    print("\nALL TESTS PASSED!")
    return True

if __name__ == "__main__":
    sys.exit(0 if test_ollama() else 1)
