"""
Emergency Data Vault Catalog Manager (Goal 1: Governed Catalog).
================================================================

Academic Framework & Systemic Context:
--------------------------------------
This module directly implements Goal 1 of the Master's Thesis:
"Build a catalog of emergency-related data sources that identifies, organizes, and
standardizes the most relevant information assets available for each scenario. This
catalog should make it possible to locate, understand, and reuse heterogeneous data from
multiple domains in a reliable and traceable way."

Architectural Functions:
------------------------
1. Catalog Persistence:
   Maintains structured JSON manifests representing indexed PDF protocols (emergency action
   plans, civil protection decrees, DANA evacuation directives) and tabular CSV data
   (cadastral census, municipal shelters, hydrological thresholds).
2. Schema & Semantic Summary Injection:
   Provides condensed textual representations of catalog assets (`get_pdfs_catalog_text`,
   `get_csvs_catalog_text`) that are injected into the Planner's closed-world context prompt.
   This informs the LLM about exact filenames, available columns, and document summaries
   before plan synthesis.
"""

import json
import os
from typing import Dict, Any

from backend.core.vault_paths import (
    APIS_CATALOG_PATH,
    CSVS_CATALOG_PATH,
    PDFS_CATALOG_PATH,
    ensure_vault_dirs,
)


def _read_json(path: str, default: Dict[str, Any]) -> Dict[str, Any]:
    """Safely load and parse a JSON catalog file, returning a default dictionary on failure."""
    if not os.path.isfile(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def load_pdfs_catalog() -> Dict[str, Any]:
    """Retrieve the manifest of vectorized emergency plans and protocol documents."""
    ensure_vault_dirs()
    return _read_json(PDFS_CATALOG_PATH, {"files": {}, "pinecone_index": None})


def load_csvs_catalog() -> Dict[str, Any]:
    """Retrieve the manifest of registered tabular CSV emergency datasets and schemas."""
    ensure_vault_dirs()
    return _read_json(CSVS_CATALOG_PATH, {"files": {}})


def save_pdfs_catalog(data: Dict[str, Any]) -> None:
    """Persist updated PDF metadata and chunk summaries into the vault catalog."""
    ensure_vault_dirs()
    with open(PDFS_CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_csvs_catalog(data: Dict[str, Any]) -> None:
    """Persist updated CSV column schemas and record statistics into the vault catalog."""
    ensure_vault_dirs()
    with open(CSVS_CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_pdfs_catalog_text() -> str:
    """
    Format the PDF document catalog into a concise markdown summary for Planner prompt grounding.
    
    Returns:
        Bullet-pointed string listing filenames, semantic resumes, and vector chunk counts.
    """
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
    """
    Format the tabular CSV catalog into a concise schema list for Planner prompt grounding.
    
    Returns:
        Bullet-pointed string listing tabular files and their declared column headers.
    """
    cat = load_csvs_catalog()
    files = cat.get("files") or {}
    if not files:
        return "  (no CSVs — use backend/vault/csvs/)"
    lines = []
    for fname, meta in sorted(files.items()):
        cols = meta.get("columns") or []
        lines.append(f'  - "{fname}": columns [{", ".join(cols)}]')
    return "\n".join(lines)
