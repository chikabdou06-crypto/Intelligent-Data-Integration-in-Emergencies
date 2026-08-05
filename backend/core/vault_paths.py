import os

CORE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CORE_DIR)
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, ".."))

VAULT_DIR = os.path.join(BACKEND_DIR, "vault")
VAULT_PDFS = os.path.join(VAULT_DIR, "pdfs")
VAULT_CSVS = os.path.join(VAULT_DIR, "csvs")
VAULT_PROCESSED_DATA = os.path.join(VAULT_DIR, "processed_data")

# Legacy paths (still scanned as fallback)
LEGACY_DATA = os.path.join(BACKEND_DIR, "data")

CATALOGS_DIR = os.path.join(VAULT_DIR, "catalogs")
PDFS_CATALOG_PATH = os.path.join(CATALOGS_DIR, "pdfs_index.json")
CSVS_CATALOG_PATH = os.path.join(CATALOGS_DIR, "csvs_index.json")
APIS_CATALOG_PATH = os.path.join(CATALOGS_DIR, "apis_index.json")
INGEST_MANIFEST_PATH = os.path.join(CATALOGS_DIR, "ingest_manifest.json")

def get_pinecone_index_name() -> str:
    return os.environ.get("PINECONE_INDEX_NAME", "tfm-vault")


def get_pinecone_namespace() -> str:
    return os.environ.get("PINECONE_NAMESPACE", "vault-pdfs")


def ensure_vault_dirs():
    os.makedirs(VAULT_PDFS, exist_ok=True)
    os.makedirs(VAULT_CSVS, exist_ok=True)
    os.makedirs(VAULT_PROCESSED_DATA, exist_ok=True)
    os.makedirs(CATALOGS_DIR, exist_ok=True)
