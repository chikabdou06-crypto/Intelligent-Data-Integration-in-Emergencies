import os
import sys
import json
from pprint import pprint

# Ensure the backend is in path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from backend.tools.local.vault_pdf_search import VaultPdfSearchTool

def main():
    print("="*60)
    print("Pinecone PDF RAG Tester (Bypassing Planner)")
    print("="*60)
    
    # Initialize the tool
    tool = VaultPdfSearchTool()
    
    # Define test queries
    queries = [
        "What are the building regulations for seismic zones according to PELSISCAV?",
        "What is the protocol for emergency communication during a severe flood in PATRICOVA?"
    ]
    
    for q in queries:
        print(f"\n[Query] {q}")
        print("Searching Pinecone...")
        
        try:
            result = tool.execute(query=q, top_k=3)
            
            if result.get("status") == "error":
                print(f"[ERROR] {result.get('message')}")
                continue
            
            matches = result.get("results", [])
            print(f"Found {len(matches)} chunks:")
            
            for i, match in enumerate(matches):
                source = match.get('source', 'unknown')
                score = match.get('score', 0)
                text = match.get('text', '').replace('\n', ' ')[:150]
                
                print(f"  {i+1}. [{source}] (Score: {score:.3f})")
                print(f"     => \"{text}...\"")
                
        except Exception as e:
            print(f"[FATAL] {e}")

if __name__ == "__main__":
    main()
