import os
import requests
from dotenv import load_dotenv

load_dotenv(".env")
api_key = os.environ.get("LANGCHAIN_API_KEY")

endpoints = [
    "https://api.smith.langchain.com",
    "https://eu.api.smith.langchain.com"
]

for endpoint in endpoints:
    print(f"Testing projects on {endpoint}...")
    headers = {"x-api-key": api_key}
    try:
        response = requests.get(f"{endpoint}/sessions", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            projects = response.json()
            print(f"Found {len(projects)} projects.")
            for p in projects[:3]:
                print(f" - {p.get('name')}")
        else:
            print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 40)
