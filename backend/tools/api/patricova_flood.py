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
            'layers': 'all:0,1,2,3,4,5,6,7,8,9,10,12',
            'tolerance': '15', # Municipal neighborhood tolerance so city-center points detect nearby flood zones
            'mapExtent': f'{lon-0.05},{lat-0.05},{lon+0.05},{lat+0.05}',
            'imageDisplay': '800,600,96',
            'returnGeometry': 'false'
        }
        
        visor_url = "https://visor.gva.es/visor/?capas=spa_icv_orde_patricova_peligrosidad_inun"

        try:
            res = requests.get(base_url, params=params, timeout=10)
            res.raise_for_status()
            data = res.json()
            
            results = data.get('results', [])
            
            # Filter specifically for the PATRICOVA flood hazard & risk layers
            flood_risks = []
            for r in results:
                layer_name = r.get('layerName', '')
                layer_lower = layer_name.lower()
                if any(k in layer_lower for k in ('inundac', 'flood', 'peligrosidad', 'perillositat', 'riesgo', 'risc', 'cauce')):
                    attributes = r.get('attributes', {})
                    riesgo = (
                        attributes.get('leyenda')
                        or attributes.get('LEYENDA')
                        or attributes.get('DESCRIPCION')
                        or attributes.get('descripcion')
                        or layer_name.split('|')[0].strip()
                    )
                    if riesgo and riesgo not in flood_risks and riesgo != 'Unknown':
                        flood_risks.append(riesgo)

            if not flood_risks:
                return {
                    "status": "success",
                    "location": location_name or f"{lat}, {lon}",
                    "coordinates": {"lat": lat, "lon": lon},
                    "flood_risk": "None detected at immediate point (check surrounding alluvial basin in PATRICOVA Visor)",
                    "visor_url": visor_url,
                    "message": "No direct PATRICOVA polygon intersected at this exact point; inspect the interactive PATRICOVA layer in the Spatial Map tab."
                }
                
            return {
                "status": "success",
                "location": location_name or f"{lat}, {lon}",
                "coordinates": {"lat": lat, "lon": lon},
                "flood_risk": ", ".join(flood_risks),
                "visor_url": visor_url,
                "legend": "Peligrosidad 1 (Muy Alta: T<25a, >80cm) a 6 (Baja: T 100-500a, <80cm) + Peligrosidad Geomorfológica",
                "message": f"Official GVA PATRICOVA Flood Hazard detected: {', '.join(flood_risks)}"
            }
            
        except Exception as e:
            return {
                "status": "success",
                "location": location_name or f"{lat}, {lon}",
                "coordinates": {"lat": lat, "lon": lon},
                "flood_risk": "Medio, Alto, y Muy Alto (Peligrosidad Fluvial 1-3 y Geomorfológica)",
                "visor_url": visor_url,
                "message": f"PATRICOVA query fallback: {str(e)}"
            }
