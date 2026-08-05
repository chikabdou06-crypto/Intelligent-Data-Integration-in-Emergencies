import os
from google import genai
from pinecone import Pinecone
from backend.core.base_tool import BaseTool
from backend.core.registry import register_tool
from backend.core.catalog_loader import load_pdfs_catalog
from backend.core.vault_paths import get_pinecone_index_name, get_pinecone_namespace

@register_tool(name="vault_pdf_search", category="DATA")
class VaultPdfSearchTool(BaseTool):
    name = "vault_pdf_search"
    description = "Search ALL company PDFs/TXT in the vault (Pinecone)."
    category = "DATA"

    def execute(self, query: str, top_k: int = 4) -> dict:
        if not query or not query.strip():
            return {"status": "error", "message": "Query is required."}

        catalog = load_pdfs_catalog()
        if not catalog.get("files"):
            return {
                "status": "error",
                "message": "No indexed PDFs available. Drop files in backend/vault/pdfs/ and ingest.",
            }

        api_key = os.environ.get("PINECONE_API_KEY")
        if not api_key:
            return {
                "status": "error", 
                "message": "PINECONE_API_KEY not set. Semantic search requires Pinecone."
            }
            
        google_api_key = os.environ.get("GOOGLE_API_KEY")
        if not google_api_key:
            return {"status": "error", "message": "GOOGLE_API_KEY not set for embeddings."}

        try:
            # 1. Embed query using raw Google GenAI SDK
            client = genai.Client(api_key=google_api_key)
            embed_model = os.environ.get("GEMINI_EMBED_MODEL", "text-embedding-004")
            embed_dim = int(os.environ.get("GEMINI_EMBED_DIM", "768"))
            
            response = client.models.embed_content(
                model=embed_model,
                contents=query,
                config={"output_dimensionality": embed_dim}
            )
            embedding = response.embeddings[0].values
            
            # 2. Query Pinecone
            pc = Pinecone(api_key=api_key)
            index = pc.Index(get_pinecone_index_name())
            
            res = index.query(
                vector=embedding,
                top_k=top_k,
                include_metadata=True,
                namespace=get_pinecone_namespace()
            )
            
            results = []
            for match in res.matches:
                results.append({
                    "text": match.metadata.get("text", "")[:2000],
                    "source": match.metadata.get("source", "unknown"),
                    "chunk_index": match.metadata.get("chunk_index", 0),
                    "retrieval": "pinecone",
                    "score": match.score
                })
                
            return {
                "status": "success",
                "retrieval_mode": "pinecone",
                "pinecone_index": get_pinecone_index_name(),
                "results": results,
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": f"Pinecone search failed: {str(e)}"}
