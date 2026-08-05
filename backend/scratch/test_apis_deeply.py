import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.tools.api.aemet_forecast import AemetForecastTool
from backend.tools.api.aemet_climatology import AemetClimatologyTool
from backend.tools.api.aemet_observations import AemetObservationsTool
from backend.tools.api.aemet_fire_risk import AemetFireRiskTool
from backend.tools.api.aemet_marine import AemetMarineTool
from backend.tools.api.aemet_warnings import AemetWarningsTool
from backend.tools.api.aemet_mountain import AemetMountainTool
from backend.tools.api.aemet_lightning import AemetLightningTool
from backend.tools.api.siscova_api import SiscovaEarthquakesTool
from backend.tools.api.patricova_flood import PatricovaFloodRiskTool

def run_tests():
    print("=== TESTING AEMET FORECAST ===")
    forecast_tool = AemetForecastTool()
    print("Madrid:", forecast_tool.execute(municipio="madrid", mode="daily").get("status"))
    print("Barcelona:", forecast_tool.execute(municipio="barcelona", mode="daily").get("status"))
    
    print("\n=== TESTING AEMET CLIMATOLOGY ===")
    clim_tool = AemetClimatologyTool()
    print("Madrid (Retiro):", clim_tool.execute(query_type="normals", station_id="madrid").get("status"))
    print("Barcelona:", clim_tool.execute(query_type="normals", station_id="barcelona").get("status"))

    print("\n=== TESTING AEMET OBSERVATIONS ===")
    obs_tool = AemetObservationsTool()
    print("Madrid (Retiro) Current:", obs_tool.execute(query_type="current_station", station_id="madrid").get("status"))

    print("\n=== TESTING AEMET FIRE RISK ===")
    fire_tool = AemetFireRiskTool()
    fire_res = fire_tool.execute(query_type="fire_estimated", area="peninsula")
    print("Fire Risk:", fire_res)

    print("\n=== TESTING AEMET MOUNTAIN ===")
    mtn_tool = AemetMountainTool()
    print("Pyrenees:", mtn_tool.execute(area="pirineos", day=0).get("status"))

    print("\n=== TESTING AEMET LIGHTNING ===")
    ltn_tool = AemetLightningTool()
    print("Lightning Map:", ltn_tool.execute().get("map_url"))

    print("\n=== TESTING PATRICOVA ===")
    patricova = PatricovaFloodRiskTool()
    print("Madrid (Out of Valencia):", patricova.execute(lat=40.4168, lon=-3.7038).get("status"))
    
    print("\n=== TESTING SISCOVA ===")
    siscova = SiscovaEarthquakesTool()
    print("Siscova (General):", siscova.execute().get("status"))

if __name__ == "__main__":
    run_tests()
