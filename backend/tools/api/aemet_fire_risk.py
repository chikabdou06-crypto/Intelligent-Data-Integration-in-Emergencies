import requests
import os
from backend.core.base_tool import BaseTool
from backend.core.registry import register_tool

BASE_URL = "https://opendata.aemet.es/opendata"

# Area codes for fire risk maps
FIRE_AREA_CODES = {
    "peninsula": "p",
    "baleares": "p",
    "canarias": "c",
}


@register_tool(name="aemet_fire_risk", category="API")
class AemetFireRiskTool(BaseTool):
    name = "aemet_fire_risk"
    description = (
        "Fetches wildfire risk probability maps and UV radiation index predictions "
        "from the AEMET OpenData API. "
        "You MUST provide query_type as EXACTLY one of: 'fire_estimated', 'fire_forecast', or 'uvi'. "
        "Fire risk area covers 'peninsula' or 'canarias'."
    )
    category = "API"
    cacheable = False

    def execute(
        self,
        query_type: str = "fire_estimated",
        area: str = "peninsula",
        day: int = 0,
        api_key: str = None,
    ) -> dict:
        """
        query_type:
            - 'fire_estimated': current estimated fire risk level map
            - 'fire_forecast': forecast fire risk for day 1-7
            - 'uvi': UV radiation index prediction for day 0-4
        area: 'peninsula' or 'canarias' (for fire risk)
        day: day offset (1-7 for fire forecast, 0-4 for UVI)
        """
        key = api_key or os.environ.get("AEMET_API_KEY")
        if not key:
            return {
                "status": "error",
                "message": "AEMET API Key is missing. Set AEMET_API_KEY.",
            }

        headers = {"api_key": key, "Accept": "application/json"}

        try:
            if query_type == "fire_estimated":
                area_code = FIRE_AREA_CODES.get(area.strip().lower(), "p")
                endpoint = f"{BASE_URL}/api/incendios/mapasriesgo/estimado/area/{area_code}"

            elif query_type == "fire_forecast":
                area_code = FIRE_AREA_CODES.get(area.strip().lower(), "p")
                day_val = max(1, min(7, day))
                endpoint = f"{BASE_URL}/api/incendios/mapasriesgo/previsto/dia/{day_val}/area/{area_code}"

            elif query_type == "uvi":
                day_val = max(0, min(4, day))
                endpoint = f"{BASE_URL}/api/prediccion/especifica/uvi/{day_val}"

            else:
                return {
                    "status": "error",
                    "message": f"Unknown query_type '{query_type}'. Use: fire_estimated, fire_forecast, or uvi.",
                }

            # Step 1: Get datos URL
            res1 = requests.get(endpoint, headers=headers, timeout=10)
            res1.raise_for_status()
            meta = res1.json()
            
            # Fallback to fire_forecast if estimated map is 404 in the payload
            if meta.get("estado") == 404 and query_type == "fire_estimated":
                query_type = "fire_forecast"
                day = 1
                area_code = FIRE_AREA_CODES.get(area.strip().lower(), "p")
                endpoint = f"{BASE_URL}/api/incendios/mapasriesgo/previsto/dia/1/area/{area_code}"
                res1 = requests.get(endpoint, headers=headers, timeout=10)
                res1.raise_for_status()
                meta = res1.json()

            datos_url = meta.get("datos")
            if not datos_url:
                return {
                    "status": "error",
                    "message": "AEMET returned no data URL.",
                    "raw": meta,
                }

            # Step 2: Fetch actual data
            res2 = requests.get(datos_url, timeout=15)
            res2.raise_for_status()

            # Fire risk maps return image data (PNG), UVI returns JSON
            if query_type == "uvi":
                try:
                    data = res2.json()
                except Exception:
                    data = res2.text

                # Format UVI data for readability
                if isinstance(data, list):
                    uvi_entries = []
                    for entry in data:
                        uvi_entries.append({
                            "fecha": entry.get("fecha", ""),
                            "localidad": entry.get("localidad", ""),
                            "provincia": entry.get("provincia", ""),
                            "uvi_max": entry.get("uvi_max", ""),
                        })
                    return {
                        "status": "success",
                        "source": "AEMET OpenData REST API (Live)",
                        "query_type": "uvi",
                        "day_offset": day,
                        "entries_count": len(uvi_entries),
                        "data": uvi_entries[:50],  # Limit to 50 entries
                    }

                return {
                    "status": "success",
                    "source": "AEMET OpenData REST API (Live)",
                    "query_type": "uvi",
                    "data": data,
                }
            else:
                # Fire risk maps are image/PDF — return the URL formatted as markdown for the agent
                return {
                    "status": "success",
                    "source": "AEMET OpenData REST API (Live)",
                    "query_type": query_type,
                    "area": area,
                    "day": day if query_type == "fire_forecast" else "current",
                    "map_url": f"![AEMET Fire Risk Map]({datos_url})",
                    "message": (
                        "Fire risk map is an image file. It has been formatted as markdown so it will display in the chat. Use UVI query_type for structured UV index data."
                    ),
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"AEMET Fire/UV API error: {str(e)}",
            }
