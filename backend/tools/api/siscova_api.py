import requests
import csv
from io import StringIO
from backend.core.base_tool import BaseTool
from backend.core.registry import register_tool

@register_tool(name="siscova_earthquakes", category="API")
class SiscovaEarthquakesTool(BaseTool):
    name = "siscova_earthquakes"
    description = "Fetches a live feed of recent seismic events (earthquakes) from the SISCOVA Open Data CKAN API. Returns data array with fields: date, time_utc, magnitude, depth_km, latitude, longitude, municipality, province, zone."
    category = "API"

    def execute(self, limit: int = 10) -> dict:
        url = "https://terramapas.icv.gva.es/31_SISCOVA?request=GetFeature&service=WFS&version=2.0.0&typename=SISCOVA.Sismos&outputformat=csv"
        
        try:
            # 10 second timeout for the live API call
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse the CSV data
            csv_data = StringIO(response.text)
            reader = csv.DictReader(csv_data)
            
            # Convert to a list of rows
            rows = list(reader)
            
            if not rows:
                return {
                    "status": "success",
                    "message": "Connected successfully, but no earthquake records found.",
                    "data": []
                }
                
            from datetime import datetime
            
            # Parse dates, filter future events, and sort descending
            valid_rows = []
            now = datetime.now()
            
            for row in rows:
                date_str = row.get('fecha', '')
                if not date_str:
                    continue
                
                # Try to filter out future dates (e.g., test entries for 2025/2026)
                try:
                    clean_date = date_str.split(' ')[0].split('T')[0]
                    year = int(clean_date[:4])
                    if year > now.year:
                        continue
                    if year == now.year:
                        row_date = datetime.strptime(clean_date, "%Y-%m-%d")
                        if row_date > now:
                            continue
                except (ValueError, IndexError):
                    pass # Ignore parse errors and keep the row
                    
                valid_rows.append(row)
                
            # Sort chronologically (newest first)
            valid_rows.sort(key=lambda r: (r.get('fecha', ''), r.get('hora_utc', '')), reverse=True)
            recent_rows = valid_rows[:limit]
            
            earthquakes = []
            for row in recent_rows:
                earthquakes.append({
                    "date": row.get('fecha', ''),
                    "time_utc": row.get('hora_utc', ''),
                    "magnitude": row.get('magnitud', ''),
                    "depth_km": row.get('profundidad', ''),
                    "latitude": row.get('latitud', ''),
                    "longitude": row.get('longitud', ''),
                    "municipality": row.get('municipio', ''),
                    "province": row.get('provincia', ''),
                    "zone": row.get('zona', '')
                })
                
            return {
                "status": "success",
                "source": "GVA Open Data API (Live)",
                "total_records_in_db": len(rows),
                "returned_records": len(earthquakes),
                "data": earthquakes
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to fetch live seismic data from GVA CKAN API: {str(e)}"
            }
