import sys
import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from backend.tools.api.google_drive import get_google_service

def main():
    service = get_google_service("drive", "v3")
    if not service:
        print("OAuth service failed to build.")
        return

    # Use the ID of TFMCSV_SANTVicente
    folder_id = "13jwbFGIGnEfzfKZxxjAv-hJrVDhml8qs"
    print(f"Listing files in folder ID: {folder_id}")
    q = f"'{folder_id}' in parents and trashed = false"
    try:
        results = service.files().list(q=q, fields="files(id, name, mimeType)").execute()
        files = results.get("files", [])
        print(f"Found {len(files)} files:")
        for f in files:
            name_bytes = f['name'].encode('utf-8', errors='replace')
            name_str = name_bytes.decode('utf-8')
            print(f"  - Name: {name_str} | ID: {f['id']} | MimeType: {f['mimeType']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
