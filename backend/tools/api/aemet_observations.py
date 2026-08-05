import requests
import os
import unicodedata
from backend.core.base_tool import BaseTool
from backend.core.registry import register_tool

BASE_URL = "https://opendata.aemet.es/opendata"

def normalize_str(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize('NFD', s.lower().strip())
    return "".join(c for c in s if unicodedata.category(c) != 'Mn')

@register_tool(name="aemet_observations", category="API")
class AemetObservationsTool(BaseTool):
    name = "aemet_observations"
    description = (
        "Fetches LIVE real-time sensor observations from AEMET stations (last 12 hours) across ALL of Spain. "
        "DO NOT use this for future forecasts (use aemet_forecast) or historical averages (use aemet_climatology). "
        "Provide 'station_name' (e.g., 'madrid', 'alicante', 'torrevieja') to dynamically search all active Spanish stations."
    )
    category = "API"
    cacheable = False

    def execute(
        self,
        station_name: str = "valencia",
        api_key: str = None,
    ) -> dict:
        key = api_key or os.environ.get("AEMET_API_KEY")
        if not key:
            return {"status": "error", "message": "AEMET API Key missing."}

        headers = {"api_key": key, "Accept": "application/json"}
        search_query = normalize_str(station_name)

        try:
            # We fetch all active observations in Spain to search dynamically
            endpoint = f"{BASE_URL}/api/observacion/convencional/todas"
            res1 = requests.get(endpoint, headers=headers, timeout=10)
            res1.raise_for_status()
            meta = res1.json()

            datos_url = meta.get("datos")
            if not datos_url:
                return {"status": "error", "message": "No data URL returned.", "raw": meta}

            res2 = requests.get(datos_url, timeout=15)
            res2.raise_for_status()
            all_data = res2.json()

            if not isinstance(all_data, list):
                return {"status": "error", "message": "Expected a list of observations."}

            # Search for the best matching station by location name (ubi)
            matched_idema = None
            matched_ubi = None
            
            # Exact match first
            for obs in all_data:
                ubi_norm = normalize_str(obs.get("ubi", ""))
                if search_query == ubi_norm:
                    matched_idema = obs.get("idema")
                    matched_ubi = obs.get("ubi")
                    break
            
            # Partial match fallback
            if not matched_idema:
                for obs in all_data:
                    ubi_norm = normalize_str(obs.get("ubi", ""))
                    if search_query in ubi_norm:
                        matched_idema = obs.get("idema")
                        matched_ubi = obs.get("ubi")
                        break

            if not matched_idema:
                # Provide some examples from the first 5 stations
                examples = ", ".join([obs.get("ubi", "") for obs in all_data[:5]])
                return {
                    "status": "error", 
                    "message": f"Could not find any active station matching '{station_name}'. Examples: {examples}..."
                }

            # Filter data to only the matched station (returns last ~12 hours of data)
            station_data = [obs for obs in all_data if obs.get("idema") == matched_idema]
            
            observations = [{
                "fecha_hora": obs.get("fint", ""),
                "temperatura": obs.get("ta", ""),
                "humedad_relativa": obs.get("hr", ""),
                "viento_velocidad": obs.get("vv", ""),
                "precipitacion": obs.get("prec", "")
            } for obs in station_data]

            return {
                "status": "success",
                "station_name": matched_ubi,
                "station_id": matched_idema,
                "data": observations,
            }

        except Exception as e:
            return {"status": "error", "message": f"Observations API error: {str(e)}"}
