import json
import os
from backend.core.vault_paths import (
    APIS_CATALOG_PATH,
    CSVS_CATALOG_PATH,
    PDFS_CATALOG_PATH,
    ensure_vault_dirs,
)


def _read_json(path: str, default: dict) -> dict:
    if not os.path.isfile(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def load_pdfs_catalog() -> dict:
    ensure_vault_dirs()
    return _read_json(PDFS_CATALOG_PATH, {"files": {}, "pinecone_index": None})


def load_csvs_catalog() -> dict:
    ensure_vault_dirs()
    return _read_json(CSVS_CATALOG_PATH, {"files": {}})


def save_pdfs_catalog(data: dict) -> None:
    ensure_vault_dirs()
    with open(PDFS_CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_csvs_catalog(data: dict) -> None:
    ensure_vault_dirs()
    with open(CSVS_CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_pdfs_catalog_text() -> str:
    cat = load_pdfs_catalog()
    files = cat.get("files") or {}
    if not files:
        return "  (no PDFs indexed yet — drop files in backend/vault/pdfs/ and run: python backend/ingest/index_all.py)"
    lines = []
    for fname, meta in sorted(files.items()):
        resume = meta.get("resume", "No summary")
        chunks = meta.get("chunk_count", 0)
        lines.append(f'  - "{fname}": {resume} [{chunks} chunks]')
    return "\n".join(lines)


def get_csvs_catalog_text() -> str:
    cat = load_csvs_catalog()
    files = cat.get("files") or {}
    if not files:
        return "  (no CSVs — use backend/vault/csvs/)"
    lines = []
    for fname, meta in sorted(files.items()):
        cols = meta.get("columns") or []
        lines.append(f'  - "{fname}": columns [{", ".join(cols)}]')
    return "\n".join(lines)
