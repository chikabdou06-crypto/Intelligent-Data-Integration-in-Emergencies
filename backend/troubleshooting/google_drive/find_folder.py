import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from backend.tools.api.google_drive import get_google_service

def main():
    service = get_google_service("drive", "v3")
    if not service:
        print("OAuth service failed to build.")
        return

    q = "mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    try:
        results = service.files().list(q=q, fields="files(id, name)").execute()
        folders = results.get("files", [])
        print(f"Found {len(folders)} folders in your Drive:")
        for f in folders:
            print(f"  - Name: {f['name']} | ID: {f['id']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
