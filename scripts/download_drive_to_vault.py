import os
import io
import json
import requests
from backend.core.vault_paths import VAULT_CSVS, CATALOGS_DIR
from backend.tools.api.google_drive import get_google_service

def download_all():
    print(f"Downloading Google Drive CSVs into {VAULT_CSVS}...")
    os.makedirs(VAULT_CSVS, exist_ok=True)
    
    catalog_path = os.path.join(CATALOGS_DIR, "drive_catalog.json")
    if not os.path.exists(catalog_path):
        print(f"Error: {catalog_path} not found.")
        return
        
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)
        
    files = catalog.get("files", [])
    print(f"Found {len(files)} files in drive_catalog.json")
    
    service = get_google_service("drive", "v3")
    if not service:
        print("Error: Could not authenticate with Google Drive service.")
        return
        
    downloaded = 0
    for f in files:
        f_id = f.get("id")
        fname = f.get("name", "")
        f_type = f.get("type", "")
        
        if not fname or not f_id:
            continue
            
        dest_path = os.path.join(VAULT_CSVS, fname)
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
            print(f"  [Skipping] Already exists: {fname}")
            downloaded += 1
            continue
            
        print(f"  [Downloading] {fname} ({f_id})...")
        try:
            # Check if it's a google spreadsheet or plain csv
            if f_type == "csv" or fname.endswith(".csv"):
                # Use get_media
                content = service.files().get_media(fileId=f_id).execute()
            else:
                content = service.files().export_media(fileId=f_id, mimeType="text/csv").execute()
                
            with open(dest_path, "wb") as out:
                out.write(content)
            downloaded += 1
        except Exception as e:
            # Try export if get_media failed, or vice-versa
            try:
                content = service.files().export_media(fileId=f_id, mimeType="text/csv").execute()
                with open(dest_path, "wb") as out:
                    out.write(content)
                downloaded += 1
            except Exception as e2:
                print(f"  [Error downloading {fname}]: {e} | {e2}")
                
    print(f"Finished downloading {downloaded}/{len(files)} files into {VAULT_CSVS}.")

if __name__ == "__main__":
    download_all()
