import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.tools.api.google_drive import DriveListTool, DriveSheetTool
from googleapiclient.discovery import build
from backend.tools.api.google_drive import get_google_service

def main():
    print("=" * 60)
    print("Testing Google Drive Sheet Tool")
    print("=" * 60)

    # 1. Search for Spreadsheets
    service = get_google_service("drive", "v3")
    if not service:
        print("OAuth service failed to build. Verify token.json.")
        return

    print("\n[Step 1] Searching for spreadsheets in Drive...")
    try:
        q = "mimeType = 'application/vnd.google-apps.spreadsheet' or mimeType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' and trashed = false"
        results = service.files().list(q=q, pageSize=10, fields="files(id, name, mimeType)").execute()
        files = results.get("files", [])
        
        print(f"Found {len(files)} spreadsheets:")
        for f in files:
            print(f"  - Name: {f['name']} | ID: {f['id']}")
            
        if not files:
            print("No spreadsheets found in your Drive to test.")
            return

        target_sheet = files[0]
        print(f"\n[Step 2] Executing drive_read_sheet on: '{target_sheet['name']}' (ID: {target_sheet['id']})...")
        
        sheet_tool = DriveSheetTool()
        res = sheet_tool.execute(file_id=target_sheet["id"])
        
        print(f"Status: {res.get('status')}")
        if res.get("status") == "success":
            print(f"Sheet Name: {res.get('sheet_name')}")
            print(f"Headers: {res.get('headers')}")
            print(f"Total Rows: {res.get('total_rows')}")
            print(f"Returned Rows: {res.get('returned_rows')}")
            print("First Row Data Preview:")
            data = res.get("data", [])
            if data:
                print(str(data[0])[:200]) # Safe printable representation
            else:
                print("No data rows.")
        else:
            print(f"Error: {res.get('message')}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    main()
