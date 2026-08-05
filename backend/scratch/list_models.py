import os
from dotenv import load_dotenv

load_dotenv()

try:
    from google import genai
except ImportError:
    print("google-genai SDK not installed.")
    exit(1)

api_key = os.environ.get("GEMINI_API_KEY", os.environ.get("GOOGLE_API_KEY", ""))
if not api_key:
    print("No GEMINI_API_KEY or GOOGLE_API_KEY found.")
    exit(1)

client = genai.Client(api_key=api_key)

print("Listing available Gemini models:")
try:
    models = client.models.list()
    for m in models:
        if "gemini" in m.name:
            print(f"- {m.name}")
except Exception as e:
    print("Error:", e)
