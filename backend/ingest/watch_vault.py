import os
import sys
import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Resolve paths
INGEST_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = INGEST_DIR.parent.parent
VAULT_DIR = PROJECT_ROOT / "backend" / "vault"

class VaultWatchHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.last_trigger = 0
        self.debounce_seconds = 2.0

    def on_any_event(self, event):
        # We only care about file creations, modifications, and moves
        if event.is_directory:
            return

        if event.event_type not in ("created", "modified", "moved"):
            return

        # Get file path
        dest_path = getattr(event, "dest_path", event.src_path)
        ext = os.path.splitext(dest_path)[1].lower()

        # Only care about our supported formats
        if ext not in (".csv", ".pdf", ".txt", ".md", ".xlsx", ".json"):
            return

        # Ignore temporary files or changes inside cache/catalogs
        parts = Path(dest_path).parts
        if "cache" in parts or "catalogs" in parts:
            return

        # Debounce rapid successive events (like when saving/writing files)
        now = time.time()
        if now - self.last_trigger < self.debounce_seconds:
            return
        self.last_trigger = now

        print(f"\n[Watcher] Vault file change detected: {event.event_type} - {os.path.basename(dest_path)}")
        
        # Trigger indexers based on extension
        if ext == ".csv":
            print("[Watcher] Triggering CSV catalog rebuild...")
            self.run_script("csvs")
        elif ext in (".pdf", ".txt", ".md"):
            print("[Watcher] Triggering PDF/Text semantic index rebuild...")
            self.run_script("pdfs")
        elif ext == ".json":
            # Rebuild both to be safe
            print("[Watcher] JSON file changed. Rebuilding catalogs...")
            self.run_script("csvs")

    def run_script(self, target: str):
        try:
            subprocess.run([sys.executable, "backend/ingest.py", target], cwd=str(PROJECT_ROOT))
        except Exception as e:
            print(f"[Watcher Error] Failed to run indexer for {module_name}: {e}")

def main():
    print("=" * 60)
    print("Vault Auto-Catalog Watcher Daemon")
    print("=" * 60)
    print(f"Monitoring folder: {VAULT_DIR}")
    print("Waiting for file drops (CSV, PDF, TXT, Excel)... Press Ctrl+C to exit.\n")

    if not VAULT_DIR.exists():
        print(f"[Warning] Vault folder not found. Creating it at: {VAULT_DIR}")
        VAULT_DIR.mkdir(parents=True, exist_ok=True)

    event_handler = VaultWatchHandler()
    observer = Observer()
    observer.schedule(event_handler, path=str(VAULT_DIR), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping vault watcher...")
        observer.stop()
    observer.join()
    print("Vault watcher stopped.")

if __name__ == "__main__":
    main()
