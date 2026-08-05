import requests
import os
from backend.core.base_tool import BaseTool
from backend.core.registry import register_tool

# Coastal area codes from the AEMET OpenAPI spec
COSTA_CODES = {
    "valencia": "46",
    "valencia y murcia": "46",
    "murcia": "46",
    "alicante": "46",
    "castellon": "46",
    "cataluña": "45",
    "baleares": "44",
    "canarias": "43",
    "andalucia occidental": "42",
    "andalucia oriental": "47",
    "galicia": "40",
    "asturias": "41",
    "cantabria": "41",
    "pais vasco": "41",
}

# High-sea area codes
ALTAMAR_CODES = {
    "mediterraneo": "2",
    "atlantico norte": "1",
    "atlantico sur": "0",
}

BASE_URL = "https://opendata.aemet.es/opendata"


@register_tool(name="aemet_marine", category="API")
class AemetMarineTool(BaseTool):
    name = "aemet_marine"
    description = (
        "Fetches live marine/coastal weather predictions from AEMET. "
        "You MUST provide forecast_type as EXACTLY one of: 'coastal' or 'highsea'. "
        "Also requires 'zone' (e.g. 'valencia', 'alicante', 'mediterraneo')."
    )
    category = "API"
    cacheable = False

    def execute(
        self,
        zone: str = "valencia",
        forecast_type: str = "coastal",
        api_key: str = None,
    ) -> dict:
        key = api_key or os.environ.get("AEMET_API_KEY")
        if not key:
            return {
                "status": "error",
                "message": "AEMET API Key is missing. Set AEMET_API_KEY.",
            }

        zone_clean = zone.strip().lower()

        if forecast_type == "highsea":
            code = ALTAMAR_CODES.get(zone_clean)
            if not code:
                return {
                    "status": "error",
                    "message": f"Unknown high-sea zone '{zone}'.",
                    "known_zones": list(ALTAMAR_CODES.keys()),
                }
            endpoint = f"{BASE_URL}/api/prediccion/maritima/altamar/area/{code}"
        else:
            code = COSTA_CODES.get(zone_clean)
            if not code:
                # Allow raw code
                if zone_clean.isdigit() and len(zone_clean) == 2:
                    code = zone_clean
                else:
                    return {
                        "status": "error",
                        "message": f"Unknown coastal zone '{zone}'.",
                        "known_zones": list(COSTA_CODES.keys()),
                    }
            endpoint = f"{BASE_URL}/api/prediccion/maritima/costera/costa/{code}"

        headers = {"api_key": key, "Accept": "application/json"}

        try:
            # Step 1: Get datos URL
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

            # Step 2: Fetch the actual marine forecast
            # Maritime forecasts return plain text, not JSON
            res2 = requests.get(datos_url, timeout=15)
            res2.raise_for_status()

            # Try JSON first, fall back to text
            try:
                data = res2.json()
            except Exception:
                data = res2.text

            return {
                "status": "success",
                "source": "AEMET OpenData REST API (Live)",
                "zone": zone,
                "forecast_type": forecast_type,
                "area_code": code,
                "data": data,
            }

        except Exception as e:
            return {"status": "error", "message": f"AEMET Marine API error: {str(e)}"}
