import os
import sys
import json
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

# Load env variables from .env
load_dotenv()

from backend.tools.local.vault_pdf_search import VaultPdfSearchTool

def main():
    tool = VaultPdfSearchTool()
    query = "According to the dataset, what were the most devastating catastrophes in 2024 and how many lives did they claim?"
    print(f"Query: {query}")
    results = tool.execute(query=query, top_k=5)
    print("RESULTS:")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
