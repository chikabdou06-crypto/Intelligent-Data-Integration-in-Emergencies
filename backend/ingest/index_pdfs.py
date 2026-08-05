"""
Incremental PDF/TXT ingest: chunk -> embed -> Pinecone upsert -> catalog resume.
Run: python backend/ingest/index_pdfs.py
"""
import hashlib
import json
import os
import sys

def get_embeddings():
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    model = os.environ.get("GEMINI_EMBED_MODEL", "models/gemini-embedding-2")
    dim = int(os.environ.get("GEMINI_EMBED_DIM", "768"))
    return GoogleGenerativeAIEmbeddings(model=model, output_dimensionality=dim)
from backend.core.vault_paths import (  # noqa: E402
    INGEST_MANIFEST_PATH,
    VAULT_PDFS,
    ensure_vault_dirs,
    get_pinecone_index_name,
    get_pinecone_namespace,
)
from backend.core.catalog_loader import load_pdfs_catalog, save_pdfs_catalog  # noqa: E402


CHUNK_SIZE = int(os.environ.get("VAULT_CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.environ.get("VAULT_CHUNK_OVERLAP", "150"))


def file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()[:16]


def load_manifest() -> dict:
    ensure_vault_dirs()
    if os.path.isfile(INGEST_MANIFEST_PATH):
        with open(INGEST_MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"files": {}}


def save_manifest(manifest: dict) -> None:
    ensure_vault_dirs()
    with open(INGEST_MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def extract_text(path: str) -> str:
    if path.lower().endswith(".txt"):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    if path.lower().endswith(".pdf"):
        try:
            from langchain_community.document_loaders import PyPDFLoader
            docs = PyPDFLoader(path).load()
            return "\n".join(d.page_content for d in docs if d.page_content)
        except Exception:
            import pypdf
            reader = pypdf.PdfReader(path)
            return "\n".join(p.extract_text() or "" for p in reader.pages)
    return ""


def make_resume(filename: str, text: str) -> str:
    preview = " ".join(text.split())[:400]
    if len(preview) < 20:
        return f"{filename} (empty or unreadable)"
    return f"{filename}: {preview[:220]}..."


def index_file(path: str, filename: str, vectorstore, text_splitter) -> int:
    from langchain_core.documents import Document
    import time

    text = extract_text(path)
    if not text.strip():
        return 0

    docs = text_splitter.split_documents(
        [Document(page_content=text, metadata={"source": filename})]
    )
    ids = []
    for i, doc in enumerate(docs):
        doc.metadata["source"] = filename
        doc.metadata["chunk_index"] = i
        chunk_id = f"{hashlib.md5(filename.encode()).hexdigest()[:12]}_{i}"
        ids.append(chunk_id)

    # Remove prior vectors for this file (best-effort)
    try:
        vectorstore.delete(filter={"source": filename})
    except Exception:
        pass

    # Batching to avoid 429 RESOURCE_EXHAUSTED
    BATCH_SIZE = 50
    for i in range(0, len(docs), BATCH_SIZE):
        batch_docs = docs[i : i + BATCH_SIZE]
        batch_ids = ids[i : i + BATCH_SIZE]
        print(f"    -> embedding batch {i//BATCH_SIZE + 1} / {(len(docs)+BATCH_SIZE-1)//BATCH_SIZE}...")
        vectorstore.add_documents(batch_docs, ids=batch_ids)
        time.sleep(2.0)  # Rate limiting sleep

    return len(docs)


def run():
    if not os.environ.get("GOOGLE_API_KEY"):
        print("GOOGLE_API_KEY is required in .env. Skipping PDFs.")
        return
        
    if not os.environ.get("PINECONE_API_KEY"):
        print("PINECONE_API_KEY is required in .env for PDF indexing. Skipping PDFs.")
        return
    ensure_vault_dirs()

    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from pinecone import Pinecone
    from langchain_pinecone import PineconeVectorStore

    print("Checking Pinecone connection...")
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    idx_name = get_pinecone_index_name()

    if idx_name not in [x.name for x in pc.list_indexes()]:
        from pinecone import ServerlessSpec
        print(f"Creating Pinecone index '{idx_name}'...")
        pc.create_index(
            name=idx_name,
            dimension=int(os.environ.get("GEMINI_EMBED_DIM", "768")),
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        import time
        time.sleep(10)

    index = pc.Index(idx_name)
    vectorstore = PineconeVectorStore(index=index, embedding=get_embeddings(), text_key="text")
    namespace = get_pinecone_namespace()

    # Load states
    manifest = load_manifest()
    tracked_files = manifest.setdefault("files", {})

    # Use a chunker optimized for dense text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""],
    )

    pdf_files = []
    if os.path.isdir(VAULT_PDFS):
        for root, dirs, fns in os.walk(VAULT_PDFS):
            for fn in fns:
                if fn.lower().endswith((".pdf", ".txt")):
                    pdf_files.append(os.path.join(root, fn))

    catalog = []
    processed_count = 0
    skipped_count = 0

    print(f"Found {len(pdf_files)} PDF/TXT files in {VAULT_PDFS}")

    for path in pdf_files:
        filename = os.path.basename(path)
        rel_path = os.path.relpath(path, VAULT_PDFS)
        current_hash = file_hash(path)

        state = tracked_files.get(rel_path, {})
        last_hash = state.get("hash")
        resume = state.get("resume")

        if last_hash == current_hash and resume:
            skipped_count += 1
            print(f"  [SKIP] {filename} (unchanged)")
            catalog.append({
                "file": rel_path,
                "resume": resume,
                "size_bytes": os.path.getsize(path),
            })
            continue

        print(f"  indexing: {filename}")
        text = extract_text(path)
        count = index_file(path, filename, vectorstore, splitter)
        resume = make_resume(filename, text)

        manifest.setdefault("files", {})[filename] = {
            "hash": digest,
            "chunk_count": count,
            "resume": resume,
        }
        catalog["files"][filename] = {
            "resume": resume,
            "chunk_count": count,
            "indexed": True,
        }
        indexed += 1

    save_manifest(manifest)
    save_pdfs_catalog(catalog)
    print(f"Done. Newly indexed: {indexed} file(s). Catalog: backend/catalogs/pdfs_index.json")


if __name__ == "__main__":
    main()
