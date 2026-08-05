import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load env variables
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from backend.tools.local.vault_catalog import VaultCatalogTool

def main():
    print("=" * 60)
    print("Testing Upgraded Vault Catalog Tool")
    print("=" * 60)

    tool = VaultCatalogTool()
    res = tool.execute()

    print(f"Status: {res.get('status')}")
    print("\n[Connections]")
    conn = res.get("connections", {})
    
    neo = conn.get("neo4j", {})
    print(f"Neo4j:")
    print(f"  Status: {neo.get('status')}")
    print(f"  Node Count: {neo.get('node_count')}")
    print(f"  Labels: {neo.get('node_labels')}")

    drive = conn.get("google_drive", {})
    print(f"Google Drive:")
    print(f"  Status: {drive.get('status')}")
    print(f"  Restricted Folder: {drive.get('restricted_sandbox_folder')}")
    print(f"  Files Preview:")
    for f in drive.get("available_files_preview", []):
        print(f"    - {f['name']} (ID: {f['id']})")

    print("\n[Local Vault]")
    vault = res.get("local_vault", {})
    csvs = vault.get("csv_datasets", {})
    print(f"  CSV Count: {csvs.get('count')}")
    pdfs = vault.get("pdf_resumes", {})
    print(f"  PDF Count: {pdfs.get('count')}")
    txts = vault.get("txt_and_md_documents", {})
    print(f"  TXT/MD Count: {txts.get('count')}")

if __name__ == "__main__":
    main()
