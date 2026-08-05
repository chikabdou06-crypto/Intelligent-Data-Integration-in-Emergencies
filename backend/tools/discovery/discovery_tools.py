"""
Discovery tools for the RAG Agent.

These tools allow the agent to introspect its own capabilities:
  - vault_discover:  Full scan of all data sources (files, connections, preprocessing).
  - tool_discover:   Lists every registered tool with its schema & parameters.
"""
import os
import glob
from backend.core.base_tool import BaseTool
from backend.core.registry import register_tool, list_all_tools, get_tool
from backend.core.catalog_loader import load_pdfs_catalog, load_csvs_catalog
from backend.core.vault_paths import (
    VAULT_DIR, VAULT_PDFS, VAULT_CSVS, VAULT_PROCESSED_DATA,
    CATALOGS_DIR, ensure_vault_dirs,
)


# ────────────────────────────────────────────────────────────────
#  Tool 1: vault_discover — "What data do I have access to?"
# ────────────────────────────────────────────────────────────────

def _scan_dir(path: str, extensions: tuple = None) -> list[dict]:
    """Return a list of {name, size_bytes} for every file in *path*."""
    results = []
    if not os.path.isdir(path):
        return results
    for fn in sorted(os.listdir(path)):
        fp = os.path.join(path, fn)
        if not os.path.isfile(fp):
            continue
        if extensions and not fn.lower().endswith(extensions):
            continue
        results.append({"name": fn, "size_bytes": os.path.getsize(fp)})
    return results


@register_tool(name="vault_discover", category="DISCOVERY")
class VaultDiscoverTool(BaseTool):
    name = "vault_discover"
    description = (
        "Scans the entire vault and returns a structured inventory of all "
        "available data: raw PDFs, indexed PDFs (Pinecone), raw CSVs, "
        "processed data (extracted tables), text/markdown files, "
        "and preprocessing scripts. Use this FIRST when unsure which "
        "file or tool to use."
    )
    category = "DISCOVERY"

    def execute(self, section: str = "all") -> dict:
        """
        Parameters
        ----------
        section : str
            Which section to return.  One of:
            'all', 'pdfs', 'csvs', 'processed', 'text', 'preprocessing'.
            Defaults to 'all'.
        """
        ensure_vault_dirs()
        out: dict = {"status": "success"}
        sec = (section or "all").strip().lower()

        # ── Raw PDFs ──────────────────────────────────────────
        if sec in ("all", "pdfs"):
            raw_pdfs = _scan_dir(VAULT_PDFS, (".pdf", ".txt"))
            indexed_catalog = load_pdfs_catalog()
            indexed_files = list(indexed_catalog.get("files", {}).keys())
            out["pdfs"] = {
                "raw_files": raw_pdfs,
                "indexed_in_pinecone": indexed_files,
                "pinecone_index": indexed_catalog.get("pinecone_index"),
                "pinecone_namespace": indexed_catalog.get("pinecone_namespace"),
            }

        # ── Raw CSVs ──────────────────────────────────────────
        if sec in ("all", "csvs"):
            csv_catalog = load_csvs_catalog()
            csv_files = csv_catalog.get("files", {})
            # Just names + column count to keep payload small
            summary = {
                fn: {
                    "columns": meta.get("columns", []),
                    "column_count": len(meta.get("columns", [])),
                }
                for fn, meta in csv_files.items()
            }
            out["csvs"] = {
                "count": len(summary),
                "directories": csv_catalog.get("csv_directories", []),
                "files": summary,
            }

        # ── Processed Data (extracted tables) ─────────────────
        if sec in ("all", "processed"):
            processed_files = _scan_dir(VAULT_PROCESSED_DATA, (".csv", ".json", ".txt"))
            out["processed_data"] = {
                "directory": VAULT_PROCESSED_DATA,
                "count": len(processed_files),
                "files": processed_files,
            }

        # ── Text / Markdown docs ──────────────────────────────
        if sec in ("all", "text"):
            txt_files = []
            for root, _dirs, files in os.walk(VAULT_DIR):
                # Skip internal folders
                if any(skip in root for skip in ("cache", "catalogs", "__pycache__")):
                    continue
                for fn in files:
                    if fn.lower().endswith((".txt", ".md")):
                        fp = os.path.join(root, fn)
                        txt_files.append({
                            "name": os.path.relpath(fp, VAULT_DIR).replace("\\", "/"),
                            "size_bytes": os.path.getsize(fp),
                        })
            out["text_files"] = {"count": len(txt_files), "files": txt_files}

        # ── Preprocessing scripts available ───────────────────
        if sec in ("all", "preprocessing"):
            preproc_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "preprocessing",
            )
            scripts = _scan_dir(preproc_dir, (".py",))
            out["preprocessing_scripts"] = {
                "directory": preproc_dir,
                "scripts": scripts,
            }

        return out


# ────────────────────────────────────────────────────────────────
#  Tool 2: tool_discover — "What tools can I use?"
# ────────────────────────────────────────────────────────────────

@register_tool(name="tool_discover", category="DISCOVERY")
class ToolDiscoverTool(BaseTool):
    name = "tool_discover"
    description = (
        "Lists every registered agent tool with its full schema "
        "(name, description, parameters, required fields). "
        "Use to understand what tools are available and how to call them."
    )
    category = "DISCOVERY"

    def execute(self, category_filter: str = None) -> dict:
        """
        Parameters
        ----------
        category_filter : str, optional
            Filter tools by category (e.g. 'DATA', 'API', 'DISCOVERY').
            Case-insensitive. Returns all tools if omitted.
        """
        tool_names = list_all_tools()
        schemas = []

        for t_name in sorted(tool_names):
            try:
                t = get_tool(t_name)
                schema = t.get_schema()
                cat = getattr(t, "category", "general").upper()

                if category_filter and cat != category_filter.strip().upper():
                    continue

                schemas.append({
                    "name": schema.get("name", t_name),
                    "category": cat,
                    "description": schema.get("description", ""),
                    "parameters": schema.get("parameters", {}),
                })
            except Exception as e:
                schemas.append({
                    "name": t_name,
                    "error": str(e),
                })

        return {
            "status": "success",
            "total_tools": len(schemas),
            "tools": schemas,
        }
