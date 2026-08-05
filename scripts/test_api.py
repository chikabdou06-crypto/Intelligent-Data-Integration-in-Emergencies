import os
from dotenv import load_dotenv
load_dotenv()
from google import genai

client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

try:
    print("Testing gemini-2.5-flash...")
    resp = client.models.generate_content(model="gemini-2.5-flash", contents="hello")
    print("Success!", resp.text)
except Exception as e:
    print("Error:", str(e))
    
try:
    print("Testing gemini-2.5-pro...")
    resp = client.models.generate_content(model="gemini-2.5-pro", contents="hello")
    print("Success!", resp.text)
except Exception as e:
    print("Error:", str(e))
