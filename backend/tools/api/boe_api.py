import requests
from typing import Dict, Any
from backend.core.base_tool import BaseTool
from backend.core.registry import register_tool

BOE_BASE_URL = "https://www.boe.es/datosabiertos/api/"

def _boe_request(endpoint: str, params: dict = None) -> Any:
    """Helper to make requests to the BOE API."""
    url = f"{BOE_BASE_URL}{endpoint}"
    # BOE API returns XML by default unless we specify Accept: application/json
    headers = {"Accept": "application/json"}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise RuntimeError(f"BOE API Error: {e}")

@register_tool("boe_get_summary", category="api")
class BoeGetSummaryTool(BaseTool):
    name = "boe_get_summary"
    description = "Retrieves the summary of the BOE (Boletín Oficial del Estado) for a specific date."
    
    def execute(self, date: str) -> Dict[str, Any]:
        """
        :param date: The date for the summary in YYYYMMDD format (e.g. '20240102')
        """
        return _boe_request(f"boe/sumario/{date}")

@register_tool("boe_get_document", category="api")
class BoeGetDocumentTool(BaseTool):
    name = "boe_get_document"
    description = "Retrieves the metadata, summary, and URLs to the PDF/XML versions of a specific BOE document by its ID (e.g., 'BOE-A-2024-12345')."
    
    def execute(self, document_id: str) -> Dict[str, Any]:
        """
        :param document_id: The BOE identifier of the document
        """
        return _boe_request(f"boe/documento/{document_id}")
