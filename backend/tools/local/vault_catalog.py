import os
from backend.core.base_tool import BaseTool
from backend.core.registry import register_tool
from backend.core.catalog_loader import load_pdfs_catalog, load_csvs_catalog
from backend.core.vault_paths import VAULT_DIR
# from backend.clients.neo4j_client import run_cypher

@register_tool(name="vault_catalog", category="DATA")
class VaultCatalogTool(BaseTool):
    name = "vault_catalog"
    description = "Discovers all available data sources across local files (CSVs, PDFs, TXT) and Neo4j knowledge graph."
    category = "DATA"

    def execute(self, *args, **kwargs) -> dict:
        # 1. Load Local CSVs
        csvs_cat = load_csvs_catalog()
        raw_csvs = csvs_cat.get("files", {})
        
        # Filter out overly massive/legacy CSVs to keep catalog token footprint small
        csvs = {
            k: v for k, v in raw_csvs.items() 
            if "CHJ_OpenData" not in k 
            and "Sismicidad_Historica" not in k 
            and "RESUM_RISCS_CV_page_" not in k
        }

        # 2. Load Local PDFs (semantic vector store files)
        pdfs_cat = load_pdfs_catalog()
        pdfs = pdfs_cat.get("files", {})

        # 3. Scan Local TXT/MD Files in Vault
        txt_files = {}
        if os.path.exists(VAULT_DIR):
            for root, dirs, files in os.walk(VAULT_DIR):
                # Skip cache and catalogs directories
                if "cache" in root or "catalogs" in root:
                    continue
                for fn in files:
                    if fn.endswith((".txt", ".md")):
                        path = os.path.join(root, fn)
                        rel_path = os.path.relpath(path, VAULT_DIR)
                        txt_files[rel_path] = {
                            "file_size_bytes": os.path.getsize(path)
                        }

        # 4. Check Neo4j Knowledge Graph Status
        neo4j_status = "Disconnected"
        neo4j_node_count = 0
        neo4j_labels = []
        try:
            # Check schema labels
            labels_res = run_cypher("CALL db.labels()")
            if labels_res is not None:
                neo4j_status = "Connected"
                neo4j_labels = [row.get("label", "") for row in labels_res if "label" in row]
                # Fallback to older neo4j labels column naming if key is empty
                if not neo4j_labels and labels_res:
                    neo4j_labels = [list(row.values())[0] for row in labels_res if row.values()]

                # Count nodes
                count_res = run_cypher("MATCH (n) RETURN count(n) as count")
                if count_res and len(count_res) > 0:
                    neo4j_node_count = count_res[0].get("count", 0)
        except Exception:
            pass

        return {
            "status": "success",
            "connections": {
                "neo4j": {
                    "status": neo4j_status,
                    "node_count": neo4j_node_count,
                    "node_labels": neo4j_labels
                }
            },
            "local_vault": {
                "csv_datasets": {
                    "count": len(csvs),
                    "files": csvs
                },
                "pdf_resumes": {
                    "count": len(pdfs),
                    "files": pdfs,
                    "pinecone_index": pdfs_cat.get("pinecone_index")
                },
                "txt_and_md_documents": {
                    "count": len(txt_files),
                    "files": txt_files
                }
            },
            "ingest_command": "python -m backend.ingest.index_all"
        }
