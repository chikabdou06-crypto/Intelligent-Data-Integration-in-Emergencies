"""
Unified CLI for Vault Ingestion Pipeline.
Usage:
    python backend/ingest.py [target]
    
Targets:
    all         - Runs all ingest pipelines
    csvs        - Generates the local CSV catalog
    pdfs        - Uploads PDFs to Pinecone and updates local PDF catalog
    drive       - Scans Google Drive and updates the Drive catalog
    pelsiscav   - Preprocesses the PELSISCAV catalog
"""

import sys
import argparse
from pathlib import Path

# Setup paths so ingest modules can import backend components cleanly
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
    
# Load .env variables cleanly once
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from backend.ingest import index_csvs, index_pdfs, index_drive

def run_all():
    print("=== Running All Ingestion Pipelines ===")
    
    print("\n--- Indexing CSVs ---")
    try:
        index_csvs.run()
    except Exception as e:
        print(f"Error in CSV pipeline: {e}")
        
    print("\n--- Indexing PDFs ---")
    try:
        index_pdfs.run()
    except Exception as e:
        print(f"Error in PDF pipeline: {e}")
        
    print("\n--- Indexing Google Drive ---")
    try:
        index_drive.run()
    except Exception as e:
        print(f"Error in Drive pipeline: {e}")

    print("\n=== Ingestion Complete ===")


def main():
    parser = argparse.ArgumentParser(description="Vault Ingestion CLI")
    parser.add_argument("target", choices=["all", "csvs", "pdfs", "drive"], help="The ingestion pipeline to run")
    args = parser.parse_args()

    if args.target == "all":
        run_all()
    elif args.target == "csvs":
        index_csvs.run()
    elif args.target == "pdfs":
        index_pdfs.run()
    elif args.target == "drive":
        index_drive.run()

if __name__ == "__main__":
    main()
