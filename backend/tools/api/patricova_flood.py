import requests
from backend.core.base_tool import BaseTool
from backend.core.registry import register_tool

@register_tool(name="patricova_flood_risk", category="API")
class PatricovaFloodRiskTool(BaseTool):
    name = "patricova_flood_risk"
    description = "Checks the official PATRICOVA Flood Risk (Riesgo de Inundación) for a location. You can provide either numeric lat/lon coordinates, OR a string location_name (e.g., 'San Vicente del Raspeig') which will be automatically geocoded."
    category = "API"

    def execute(self, lat=None, lon=None, location_name: str = None) -> dict:
        # Gracefully handle stringified numbers from other tools
        if lat is not None and not str(lat).startswith('$PREV'):
            try:
                lat = float(lat)
            except ValueError:
                return {"status": "error", "message": f"Invalid latitude format: {lat}"}
        
        if lon is not None and not str(lon).startswith('$PREV'):
            try:
                lon = float(lon)
            except ValueError:
                return {"status": "error", "message": f"Invalid longitude format: {lon}"}

        # If lat/lon are not provided but location_name is, geocode it
        if not lat or not lon or str(lat).startswith('$PREV'):
            if location_name:
                try:
                    geocode_res = requests.get(
                        f"https://nominatim.openstreetmap.org/search?q={location_name}&format=json&limit=1",
                        headers={"User-Agent": "TFM_RiskApp/1.0"},
                        timeout=5
                    )
                    geocode_res.raise_for_status()
                    geo_data = geocode_res.json()
                    if geo_data:
                        lat = float(geo_data[0]['lat'])
                        lon = float(geo_data[0]['lon'])
                    else:
                        return {"status": "error", "message": f"Could not find coordinates for location: {location_name}"}
                except Exception as e:
                    return {"status": "error", "message": f"Geocoding failed: {str(e)}"}
            else:
                return {"status": "error", "message": "You must provide either lat/lon or a location_name"}

        # We use the native ArcGIS REST API Identify endpoint to let the remote server do the spatial math
        base_url = "https://carto.icv.gva.es/arcgis/rest/services/tm_infraestructuras/ordenacion_territorial/MapServer/identify"
        
        params = {
            'f': 'json',
            'geometry': f'{lon},{lat}',
            'geometryType': 'esriGeometryPoint',
            'sr': '4326', # WGS84 Lat/Lon
            'layers': 'all',
            'tolerance': '1', # Strict tolerance
            'mapExtent': '-1,38,1,40', # Required dummy extent
            'imageDisplay': '800,600,96', # Required dummy display
            'returnGeometry': 'false'
        }
        
        try:
            res = requests.get(base_url, params=params, timeout=10)
            res.raise_for_status()
            data = res.json()
            
            results = data.get('results', [])
            
            # Filter specifically for the flood risk layer
            flood_risks = []
            for r in results:
                layer_name = r.get('layerName', '').lower()
                if 'inundac' in layer_name or 'flood' in layer_name:
                    attributes = r.get('attributes', {})
                    riesgo = attributes.get('leyenda', 'Unknown')
                    if riesgo not in flood_risks and riesgo != 'Unknown':
                        flood_risks.append(riesgo)
            
            if not flood_risks:
                return {
                    "status": "success",
                    "coordinates": {"lat": lat, "lon": lon},
                    "flood_risk": "None / Out of Zone",
                    "message": "No official PATRICOVA flood risk detected for these coordinates."
                }
                
            # If multiple overlapping polygons, we could sort by severity, but for now just list them
            return {
                "status": "success",
                "coordinates": {"lat": lat, "lon": lon},
                "flood_risk": ", ".join(flood_risks),
                "message": f"PATRICOVA Flood Risk detected: {', '.join(flood_risks)}"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to check PATRICOVA flood risk: {str(e)}"
            }
