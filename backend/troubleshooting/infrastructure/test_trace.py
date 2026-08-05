import os
import logging
from dotenv import load_dotenv

# Enable langsmith debug logging
os.environ["LANGSMITH_TRACING_DEBUG"] = "true"

load_dotenv(".env")
os.environ["LANGCHAIN_PROJECT"] = "default"  # override project

from langchain_google_genai import ChatGoogleGenerativeAI
import time

llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0)

print("Invoking LLM with project 'default'...")
response = llm.invoke("say 'tracing works'")
print("Response:", response.content)
print("Waiting a few seconds for trace to flush...")
time.sleep(5)
print("Done.")
