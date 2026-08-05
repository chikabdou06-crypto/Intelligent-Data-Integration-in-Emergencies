import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from backend.tools.api.google_drive import DriveListTool, DriveReadTool

def main():
    print("=" * 60)
    print("Testing Google Drive OAuth Tools")
    print("=" * 60)

    # 1. Test Listing Files
    print("\n[Step 1] Executing drive_list...")
    list_tool = DriveListTool()
    res_list = list_tool.execute()
    print(f"Status: {res_list.get('status')}")
    print(f"Source: {res_list.get('source')}")
    
    if res_list.get("status") != "success":
        print(f"Error: {res_list.get('message')}")
        return

    files = res_list.get("files", [])
    print(f"Found {len(files)} files.")
    for f in files[:5]:
        print(f"  - Name: {f['name']} | ID: {f['id']} | MimeType: {f['mimeType']}")

    if not files:
        print("No files available to test read.")
        return

    # Find the docx file or any doc
    target_file = None
    for f in files:
        if "document" in f["mimeType"] or "docx" in f["name"].lower():
            target_file = f
            break
            
    if not target_file:
        target_file = files[0]

    # 2. Test Reading File
    print(f"\n[Step 2] Executing drive_read on file: '{target_file['name']}' (ID: {target_file['id']})...")
    read_tool = DriveReadTool()
    res_read = read_tool.execute(file_id=target_file["id"])
    print(f"Status: {res_read.get('status')}")
    if res_read.get("status") == "success":
        print(f"Length: {res_read.get('length')} characters")
        print("Preview:")
        print("-" * 40)
        print(res_read.get("preview"))
        print("-" * 40)
    else:
        print(f"Error: {res_read.get('message')}")

    # 3. Test Security Boundary (Read file outside restricted folder)
    blocked_file_id = "1X07VBGV7Kw6vjyOsoz-Mmcf5UEV5tOhp" # 2026-tfm-unified-rag.docx
    print(f"\n[Step 3] TESTING SECURITY BOUNDARY: Attempting to read file outside folder (ID: {blocked_file_id})...")
    res_blocked = read_tool.execute(file_id=blocked_file_id)
    print(f"Status: {res_blocked.get('status')}")
    print(f"Message: {res_blocked.get('message')}")

if __name__ == "__main__":
    main()
