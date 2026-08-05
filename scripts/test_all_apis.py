import os
import sys
import json
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

def test_tool(tool_instance, **kwargs):
    print(f"\n--- Testing {tool_instance.name} ---")
    try:
        result = tool_instance.execute(**kwargs)
        if isinstance(result, dict) and result.get("status") == "error":
            print(f"[ERROR]: {result.get('message')}")
        elif isinstance(result, dict) and "error" in result:
             print(f"[ERROR]: {result.get('error')}")
        else:
            print(f"[SUCCESS]")
            # print a small snippet
            res_str = str(result)[:300].replace("\n", " ")
            print(f"   Snippet: {res_str}...")
    except Exception as e:
        print(f"[EXCEPTION]: {str(e)}")

def main():
    print("Testing AEMET APIs...")
    from backend.tools.api.aemet_fire_risk import AemetFireRiskTool
    from backend.tools.api.aemet_forecast import AemetForecastTool
    from backend.tools.api.aemet_historical import AemetHistoricalTool
    from backend.tools.api.aemet_marine import AemetMarineTool
    from backend.tools.api.aemet_warnings import AemetWarningsTool
    
    # aemet_fire_risk takes query_type, area, day
    test_tool(AemetFireRiskTool(), query_type="uvi", area="peninsula", day=0)
    
    # aemet_forecast takes municipio, mode
    test_tool(AemetForecastTool(), municipio="valencia", mode="daily") 
    
    # aemet_historical (Climatology focus)
    # We will test daily, normals, and extremes to verify climatology
    print("\n--- Testing aemet_historical (Climatology endpoints) ---")
    tool = AemetHistoricalTool()
    test_tool(tool, query_type="normals", station_id="valencia")
    test_tool(tool, query_type="extremes", station_id="valencia", parameter="T")
    test_tool(tool, query_type="monthly", station_id="valencia", anio_ini="2020", anio_fin="2022")
    
    # aemet_marine takes zone, forecast_type
    test_tool(AemetMarineTool(), zone="valencia", forecast_type="coastal")
    
    # aemet_warnings takes no area (just api_key)
    test_tool(AemetWarningsTool())
    
    print("\nTesting ICV / Patricova...")
    from backend.tools.api.icv_wms_search import ICVWmsSearchTool
    from backend.tools.api.patricova_flood import PatricovaFloodRiskTool
    test_tool(ICVWmsSearchTool(), query="valencia")
    test_tool(PatricovaFloodRiskTool(), location_name="valencia")
    
    print("\nTesting Siscova...")
    from backend.tools.api.siscova_api import SiscovaEarthquakesTool
    from backend.tools.api.siscova_scraper import SiscovaScraperTool
    test_tool(SiscovaEarthquakesTool(), limit=2)
    test_tool(SiscovaScraperTool())
    
if __name__ == "__main__":
    main()
