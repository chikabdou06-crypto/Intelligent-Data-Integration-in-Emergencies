import requests
from typing import Dict, Any, List
from backend.core.base_tool import BaseTool
from backend.core.registry import register_tool

INE_BASE_URL = "https://servicios.ine.es/wstempus/js/"

def _ine_request(endpoint: str, params: dict = None) -> Any:
    """Helper to make requests to the INE API."""
    url = f"{INE_BASE_URL}{endpoint}"
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        text = response.text.strip()
        if not text:
            return []
        return response.json()
    except Exception as e:
        raise RuntimeError(f"INE API Error: {e}")

@register_tool("ine_search_operations", category="api")
class IneSearchOperationsTool(BaseTool):
    name = "ine_search_operations"
    description = "Searches for statistical operations in the Spanish INE (Instituto Nacional de Estadística) database by keyword (e.g., 'paro', 'IPC', 'poblacion'). Returns a list of matching operations with their IDs."
    
    def execute(self, query: str) -> List[Dict[str, Any]]:
        operations = _ine_request("ES/OPERACIONES_DISPONIBLES")
        query_lower = query.lower()
        
        results = []
        for op in operations:
            if query_lower in op.get("Nombre", "").lower():
                results.append({
                    "id": op.get("Id"),
                    "name": op.get("Nombre"),
                    "code": op.get("Codigo")
                })
        
        return results[:20]  # Limit to top 20 to save context

@register_tool("ine_list_tables", category="api")
class IneListTablesTool(BaseTool):
    name = "ine_list_tables"
    description = "Lists all available data tables for a specific INE statistical operation. Requires the operation_id (e.g., obtained from ine_search_operations)."
    
    def execute(self, operation_id: int) -> List[Dict[str, Any]]:
        # INE API sometimes uses strings/ints interchangeably. We cast to str for the URL.
        tables = _ine_request(f"ES/TABLAS_OPERACION/{operation_id}")
        
        results = []
        for table in tables:
            results.append({
                "id": table.get("Id"),
                "name": table.get("Nombre"),
                "code": table.get("Codigo")
            })
            
        return results[:30]  # Limit to top 30 tables

@register_tool("ine_get_table_data", category="api")
class IneGetTableDataTool(BaseTool):
    name = "ine_get_table_data"
    description = "Fetches actual statistical data for a specific INE table. Returns the last N periods of data (default 5). Requires the table_id (e.g., obtained from ine_list_tables)."
    
    def execute(self, table_id: int, n_last: int = 5) -> Dict[str, Any]:
        params = {"nult": n_last}
        data = _ine_request(f"ES/DATOS_TABLA/{table_id}", params=params)
        
        # Data comes back as a list of series, each with a list of Data
        # We simplify the structure slightly for the LLM
        simplified_series = []
        for series in data:
            simplified_series.append({
                "series_name": series.get("Nombre"),
                "data": [
                    {
                        "period": f"{d.get('Anyo')}-{d.get('FK_Periodo')}",
                        "value": d.get("Valor"),
                        "notes": d.get("Notas")
                    }
                    for d in series.get("Data", [])
                ]
            })
            
        return {
            "table_id": table_id,
            "series": simplified_series
        }
