"""
Refresh CSV catalog from backend/vault/csvs/
Run: python backend/ingest/index_csvs.py
"""
import csv
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from backend.core.vault_paths import VAULT_CSVS, VAULT_PROCESSED_DATA, LEGACY_DATA, ensure_vault_dirs
from backend.core.catalog_loader import save_csvs_catalog


def scan_folder(folder: str) -> dict:
    files = {}
    if not os.path.isdir(folder):
        return files
    for root, dirs, filenames in os.walk(folder):
        for fn in filenames:
            if not fn.endswith(".csv"):
                continue
            path = os.path.join(root, fn)
            # Use relative path from VAULT_CSVS or other base folder as key if possible,
            # or just the relative path from the scanned folder.
            rel_path = os.path.relpath(path, folder)
            try:
                with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
                    reader = csv.reader(f)
                    headers = next(reader, None)
                    headers = [h.strip() for h in headers] if headers else []
                files[rel_path] = {
                    "columns": headers,
                    "file_size_bytes": os.path.getsize(path),
                    "resume": f"Spreadsheet with columns: {', '.join(headers[:8])}{'...' if len(headers) > 8 else ''}",
                }
            except Exception as e:
                files[rel_path] = {"columns": [], "error": str(e)}
    return files


def run():
    ensure_vault_dirs()
    files = scan_folder(VAULT_CSVS)
    
    processed = scan_folder(VAULT_PROCESSED_DATA)
    for k, v in processed.items():
        files.setdefault(k, v)
        
    legacy = scan_folder(LEGACY_DATA)
    for k, v in legacy.items():
        files.setdefault(k, v)

    save_csvs_catalog({"files": files, "csv_directories": [VAULT_CSVS, VAULT_PROCESSED_DATA, LEGACY_DATA]})
    print(f"CSV catalog updated: {len(files)} file(s)")


if __name__ == "__main__":
    run()

