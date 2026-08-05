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

@register_tool(name="aemet_climatology", category="API")
class AemetClimatologyTool(BaseTool):
    name = "aemet_climatology"
    description = (
        "Fetches HISTORICAL climate averages, extremes, or past daily records for any station in Spain. "
        "DO NOT use this tool for live forecasts (use aemet_forecast) or live sensor data (use aemet_observations). "
        "query_type MUST be exactly one of: 'daily', 'normals' (1991-2020 averages), 'monthly', or 'extremes'. "
        "Provide 'station_name' (e.g., 'madrid', 'valencia') to dynamically find the correct station."
    )
    category = "API"
    cacheable = False

    def execute(
        self,
        query_type: str = "normals",
        station_name: str = None,
        fecha_ini: str = None,
        fecha_fin: str = None,
        anio_ini: str = None,
        anio_fin: str = None,
        parameter: str = None,
        api_key: str = None,
    ) -> dict:
        key = api_key or os.environ.get("AEMET_API_KEY")
        if not key:
            return {"status": "error", "message": "AEMET API Key missing."}

        headers = {"api_key": key, "Accept": "application/json"}
        search_query = normalize_str(station_name) if station_name else None

        if not search_query:
            return {"status": "error", "message": "station_name is required."}

        try:
            # Dynamically resolve station name to idema using the /todas endpoint
            obs_url = f"{BASE_URL}/api/observacion/convencional/todas"
            res_obs = requests.get(obs_url, headers=headers, timeout=10)
            res_obs.raise_for_status()
            obs_meta = res_obs.json()
            
            if not obs_meta.get("datos"):
                return {"status": "error", "message": "Failed to fetch station list."}
                
            res_obs_data = requests.get(obs_meta["datos"], timeout=15)
            res_obs_data.raise_for_status()
            all_stations = res_obs_data.json()

            resolved_idema = None
            resolved_ubi = None
            
            if isinstance(all_stations, list):
                # Exact match first
                for obs in all_stations:
                    if search_query == normalize_str(obs.get("ubi", "")):
                        resolved_idema = obs.get("idema")
                        resolved_ubi = obs.get("ubi")
                        break
                
                # Partial match
                if not resolved_idema:
                    for obs in all_stations:
                        if search_query in normalize_str(obs.get("ubi", "")):
                            resolved_idema = obs.get("idema")
                            resolved_ubi = obs.get("ubi")
                            break

            if not resolved_idema:
                # Provide examples
                examples = ", ".join([s.get("ubi", "") for s in all_stations[:5]]) if isinstance(all_stations, list) else ""
                return {"status": "error", "message": f"Could not find station matching '{station_name}'. Examples: {examples}..."}

            # Now proceed with the climatology request using the resolved_idema
            if query_type == "daily":
                if not fecha_ini or not fecha_fin:
                    return {"status": "error", "message": "fecha_ini and fecha_fin required (YYYY-MM-DDTHH:MM:SSUTC)."}
                endpoint = f"{BASE_URL}/api/valores/climatologicos/diarios/datos/fechaini/{fecha_ini}/fechafin/{fecha_fin}/estacion/{resolved_idema}"

            elif query_type == "normals":
                endpoint = f"{BASE_URL}/api/valores/climatologicos/normales/estacion/{resolved_idema}"

            elif query_type == "monthly":
                if not anio_ini or not anio_fin:
                    return {"status": "error", "message": "anio_ini and anio_fin required (YYYY)."}
                endpoint = f"{BASE_URL}/api/valores/climatologicos/mensualesanuales/datos/anioini/{anio_ini}/aniofin/{anio_fin}/estacion/{resolved_idema}"

            elif query_type == "extremes":
                param = (parameter or "T").upper()
                if param not in ("P", "T", "V"):
                    return {"status": "error", "message": "parameter must be 'P' (precip), 'T' (temp), or 'V' (wind)."}
                endpoint = f"{BASE_URL}/api/valores/climatologicos/valoresextremos/parametro/{param}/estacion/{resolved_idema}"
            else:
                return {"status": "error", "message": f"Unknown query_type '{query_type}'."}

            res1 = requests.get(endpoint, headers=headers, timeout=10)
            res1.raise_for_status()
            meta = res1.json()

            datos_url = meta.get("datos")
            if not datos_url:
                if meta.get("estado") == 404:
                    return {"status": "success", "message": f"No historical data available for {resolved_ubi} in this range."}
                return {"status": "error", "message": "No data URL returned.", "raw": meta}

            res2 = requests.get(datos_url, timeout=15)
            res2.raise_for_status()
            data = res2.json()

            if query_type == "daily" and isinstance(data, list):
                daily_records = [{"fecha": r.get("fecha",""), "tmax": r.get("tmax",""), "tmin": r.get("tmin",""), "prec": r.get("prec","")} for r in data]
                return {"status": "success", "query_type": "daily", "station_name": resolved_ubi, "records": daily_records}
                
            return {"status": "success", "query_type": query_type, "station_name": resolved_ubi, "station_id": resolved_idema, "data": data}

        except Exception as e:
            return {"status": "error", "message": f"Climatology API error: {str(e)}"}
