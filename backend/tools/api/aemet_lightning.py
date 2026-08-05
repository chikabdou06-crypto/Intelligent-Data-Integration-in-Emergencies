import requests
import os
import time
from backend.core.base_tool import BaseTool
from backend.core.registry import register_tool

BASE_URL = "https://opendata.aemet.es/opendata"

@register_tool(name="aemet_lightning", category="API")
class AemetLightningTool(BaseTool):
    name = "aemet_lightning"
    description = (
        "Fetches the latest lightning strike observation map from AEMET. "
        "Returns a viewable image URL showing recent lightning activity."
    )
    category = "API"
    cacheable = False

    def execute(self, api_key: str = None) -> dict:
        key = api_key or os.environ.get("AEMET_API_KEY")
        if not key:
            return {
                "status": "error",
                "message": "AEMET API Key is missing. Set AEMET_API_KEY.",
            }

        endpoint = f"{BASE_URL}/api/red/rayos/mapa"
        headers = {"api_key": key, "Accept": "application/json"}

        try:
            # Step 1: Get datos URL with retry for 429
            meta = None
            for attempt in range(3):
                res1 = requests.get(endpoint, headers=headers, timeout=10)
                if res1.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                res1.raise_for_status()
                meta = res1.json()
                break
                
            if not meta:
                return {"status": "error", "message": "AEMET API error: 429 Too Many Requests"}

            datos_url = meta.get("datos")
            if not datos_url:
                return {
                    "status": "error",
                    "message": "AEMET returned no data URL.",
                    "raw": meta,
                }

            # Return markdown-formatted image
            return {
                "status": "success",
                "source": "AEMET OpenData REST API (Live)",
                "map_url": f"![AEMET Lightning Map]({datos_url})",
                "message": "Lightning map is an image file formatted as markdown so it will display directly in chat.",
            }

        except Exception as e:
            return {"status": "error", "message": f"AEMET Lightning API error: {str(e)}"}
