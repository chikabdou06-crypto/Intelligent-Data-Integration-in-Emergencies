"""
One-time Google OAuth authentication script.
Run this ONCE to generate token.json.
After that, the Drive tools will work automatically forever
(the token auto-refreshes in the background).

Usage:
    python backend/scripts/authenticate_drive.py
"""
import os
import sys
from pathlib import Path

# Project root is two levels up from this script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token.json"

# Scopes — what we're asking permission to access
SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",    # Read all Drive files (includes Sheets)
]


def main():
    print("=" * 60)
    print("Google Drive OAuth Setup")
    print("=" * 60)

    # Check credentials file exists
    if not CREDENTIALS_FILE.exists():
        print(f"\n[ERROR] credentials.json not found at: {CREDENTIALS_FILE}")
        print("Download it from: Google Cloud Console → APIs & Services → Credentials")
        sys.exit(1)

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
    except ImportError:
        print("\n[ERROR] Missing Google auth libraries. Install them:")
        print("  pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        sys.exit(1)

    creds = None

    # Check if we already have a valid token
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    # If no valid credentials, run the OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("\nRefreshing expired token...")
            creds.refresh(Request())
        else:
            print("\nOpening browser for Google login...")
            print("(A browser window will open — log in with the Google account that owns the Drive)")
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the token for future use
        TOKEN_FILE.write_text(creds.to_json())
        print(f"\n[OK] Token saved to: {TOKEN_FILE}")

    print("\n[SUCCESS] Google Drive authentication complete!")
    print(f"  credentials.json : {CREDENTIALS_FILE}")
    print(f"  token.json       : {TOKEN_FILE}")
    print("\nYou can now use drive_list, drive_read, and drive_read_sheet tools.")
    print("The token auto-refreshes — you never need to run this again.")

    # Quick validation: try listing a few files
    try:
        from googleapiclient.discovery import build
        service = build("drive", "v3", credentials=creds)
        results = service.files().list(pageSize=5, fields="files(id, name, mimeType)").execute()
        files = results.get("files", [])
        print(f"\n[Validation] Found {len(files)} file(s) in your Drive:")
        for f in files:
            print(f"  - {f['name']} ({f['mimeType'].split('.')[-1]})")
    except Exception as e:
        print(f"\n[Warning] Could not validate Drive access: {e}")


if __name__ == "__main__":
    main()
