import requests
from html.parser import HTMLParser
from backend.core.base_tool import BaseTool
from backend.core.registry import register_tool

@register_tool(name="siscova_scraper", category="SCRAPER")
class SiscovaScraperTool(BaseTool):
    name = "siscova_scraper"
    description = "Scrapes live seismic station data (locations, sensor types) from the SISCOVA HTML web portal."
    category = "SCRAPER"

    def execute(self) -> dict:
        url = "https://www.siscova.es/es/estaciones-sismicas"
        
        # We must use a browser User-Agent to bypass their basic bot protection
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            html = response.text
            
            # A very simple built-in parser to extract the table rows
            class TableParser(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.in_td = False
                    self.current_data = []
                    self.rows = []
                    
                def handle_starttag(self, tag, attrs):
                    if tag == 'tr':
                        self.current_data = []
                    elif tag == 'td':
                        self.in_td = True
                        
                def handle_data(self, data):
                    if self.in_td:
                        clean = data.strip()
                        if clean:
                            self.current_data.append(clean)
                            
                def handle_endtag(self, tag):
                    if tag == 'td':
                        self.in_td = False
                    elif tag == 'tr':
                        if self.current_data:
                            self.rows.append(self.current_data)

            parser = TableParser()
            parser.feed(html)
            
            # Filter out empty rows, keep only valid station rows (which have 5 columns)
            valid_rows = [r for r in parser.rows if len(r) >= 5]
            
            # Format the data cleanly
            stations = []
            for row in valid_rows:
                stations.append({
                    "code": row[0],
                    "name": row[1],
                    "latitude": float(row[2]),
                    "longitude": float(row[3]),
                    "altitude": int(row[4]),
                    "sensor_type": row[5] if len(row) > 5 else "Unknown"
                })
                
            return {
                "status": "success",
                "source": url,
                "count": len(stations),
                "data": stations
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to scrape SISCOVA: {str(e)}"
            }
