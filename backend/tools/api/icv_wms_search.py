import requests
import xml.etree.ElementTree as ET
from backend.core.base_tool import BaseTool
from backend.core.registry import register_tool

@register_tool(name="icv_wms_search", category="API")
class ICVWmsSearchTool(BaseTool):
    name = "icv_wms_search"
    description = "Searches the Institut Cartogràfic Valencià (ICV) Metadata Catalog for map services, datasets, and WMS links. Useful for finding data on DANA, floods, climate change, or specific maps."
    category = "API"

    def execute(self, query: str) -> dict:
        url = "https://catalogo.icv.gva.es/geonetwork/srv/spa/q"
        params = {"any": query, "fast": "index"}
        headers = {"Accept": "application/xml"}
        
        try:
            res = requests.get(url, params=params, headers=headers, timeout=10)
            res.raise_for_status()
            
            # Simple fallback if encoding is messed up
            res.encoding = res.apparent_encoding
            
            root = ET.fromstring(res.text)
            metadata_list = root.findall(".//metadata")
            
            if not metadata_list:
                return {
                    "status": "success",
                    "query": query,
                    "message": "No map services or datasets found in the ICV catalog for this query.",
                    "results": []
                }
            
            results = []
            for md in metadata_list[:5]:  # Return top 5 results
                title = md.findtext(".//title", default="Unknown Title")
                uuid = md.findtext(".//uuid", default="Unknown UUID")
                abstract = md.findtext(".//abstract", default="")
                
                # Check for WMS links inside the metadata link nodes
                links = []
                for link in md.findall(".//link"):
                    links.append(link.text)
                
                # Try to extract specifically WMS if present, otherwise just keep the UUID
                results.append({
                    "title": title,
                    "uuid": uuid,
                    "abstract": abstract[:200] + "..." if len(abstract) > 200 else abstract,
                    "metadata_url": f"https://catalogo.icv.gva.es/geonetwork/srv/spa/catalog.search#/metadata/{uuid}",
                    "links": links
                })
            
            return {
                "status": "success",
                "query": query,
                "message": f"Found {len(metadata_list)} datasets in the ICV catalog. Showing top {len(results)}.",
                "results": results
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to search the ICV catalog: {str(e)}"
            }
