import requests
import os
import time
from backend.core.base_tool import BaseTool
from backend.core.registry import register_tool

# Mountain area codes from the AEMET OpenAPI spec
MOUNTAIN_AREA_CODES = {
    "pirineo aragones": "pir1",
    "pirineo aragonés": "pir1",
    "pirineos": "pir1",
    "pirineo catalan": "pir2",
    "pirineo catalán": "pir2",
    "pirineo navarro": "pir3",
    "picos de europa": "peu1",
    "sierra de gredos": "gre1",
    "gredos": "gre1",
    "sierra nevada": "nev1",
    "sierras de guadarrama": "gua1",
    "guadarrama": "gua1",
    "somosierra": "gua1",
    "iberica aragonesa": "ibe1",
}

BASE_URL = "https://opendata.aemet.es/opendata"

@register_tool(name="aemet_mountain", category="API")
class AemetMountainTool(BaseTool):
    name = "aemet_mountain"
    description = (
        "Fetches mountain weather forecasts from AEMET. "
        "Requires 'area' (e.g. 'pirineos', 'sierra nevada', 'picos de europa') and 'day' (0 for today, 1 for tomorrow, etc. up to 3)."
    )
    category = "API"
    cacheable = False

    def execute(
        self,
        area: str = "pirineos",
        day: int = 0,
        api_key: str = None,
    ) -> dict:
        key = api_key or os.environ.get("AEMET_API_KEY")
        if not key:
            return {
                "status": "error",
                "message": "AEMET API Key is missing. Set AEMET_API_KEY.",
            }

        area_clean = area.strip().lower()
        code = MOUNTAIN_AREA_CODES.get(area_clean)
        
        # Fallback to direct code if provided
        if not code and len(area_clean) == 4 and area_clean.isalnum():
            code = area_clean
            
        if not code:
            return {
                "status": "error",
                "message": f"Unknown mountain area '{area}'.",
                "known_areas": list(MOUNTAIN_AREA_CODES.keys()),
            }

        day_val = max(0, min(3, int(day)))
        endpoint = f"{BASE_URL}/api/prediccion/especifica/montaña/pasada/area/{code}/dia/{day_val}"

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

            # Step 2: Fetch the actual mountain forecast (it might be plain text or JSON)
            forecast_data = None
            for attempt in range(3):
                res2 = requests.get(datos_url, timeout=15)
                if res2.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                res2.raise_for_status()
                try:
                    forecast_data = res2.json()
                except Exception:
                    forecast_data = res2.text
                break
                
            if not forecast_data:
                return {"status": "error", "message": "AEMET API error on data fetch"}

            return {
                "status": "success",
                "source": "AEMET OpenData REST API (Live)",
                "area": area,
                "day_offset": day_val,
                "data": forecast_data,
            }

        except Exception as e:
            return {"status": "error", "message": f"AEMET Mountain API error: {str(e)}"}
