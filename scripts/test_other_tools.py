import sys
import os
from dotenv import load_dotenv
import pprint

sys.path.insert(0, '.')
load_dotenv('.env')

from backend.tools.api.aemet_marine import AemetMarineTool
from backend.tools.api.aemet_fire_risk import AemetFireRiskTool
from backend.tools.api.patricova_flood import PatricovaFloodRiskTool
from backend.tools.api.boe_api import BoeGetSummaryTool
from backend.tools.api.icv_wms_search import ICVWmsSearchTool
from backend.tools.api.ine_api import IneSearchOperationsTool
from backend.tools.api.siscova_api import SiscovaEarthquakesTool

def main():
    print("=== TESTING AEMET MARINE ===")
    marine = AemetMarineTool()
    res_marine = marine.execute(zone="castellon", forecast_type="coastal")
    print(f"Status: {res_marine.get('status')}")
    print(f"Message/Url: {res_marine.get('message') or 'Success'}")
    
    print("\n=== TESTING AEMET FIRE RISK ===")
    fire = AemetFireRiskTool()
    res_fire = fire.execute(area="peninsula", query_type="fire_estimated")
    print(f"Status: {res_fire.get('status')}")
    
    print("\n=== TESTING PATRICOVA FLOOD RISK ===")
    flood = PatricovaFloodRiskTool()
    # Let's test the HTTPS geocoding
    res_flood = flood.execute(location_name="San Vicente del Raspeig")
    print(f"Status: {res_flood.get('status')}")
    print(f"Results length: {len(res_flood.get('data', [])) if isinstance(res_flood.get('data'), list) else res_flood.get('message')}")
    
    print("\n=== TESTING BOE API ===")
    boe = BoeGetSummaryTool()
    res_boe = boe.execute(date="20240102")
    # boe returns a dict, let's just see if there's an error
    is_dict = isinstance(res_boe, dict)
    print(f"Success? {is_dict}")

    print("\n=== TESTING ICV WMS SEARCH ===")
    icv = ICVWmsSearchTool()
    res_icv = icv.execute(query="inundacion")
    print(f"Status: {res_icv.get('status')}")
    print(f"Results count: {len(res_icv.get('results', []))}")
    
    print("\n=== TESTING INE API ===")
    ine = IneSearchOperationsTool()
    res_ine = ine.execute(query="poblacion")
    print(f"Results count: {len(res_ine)}")
    
    print("\n=== TESTING SISCOVA EARTHQUAKES ===")
    siscova = SiscovaEarthquakesTool()
    res_siscova = siscova.execute(limit=3)
    print(f"Status: {res_siscova.get('status')}")
    print(f"Earthquakes found: {len(res_siscova.get('data', []))}")

if __name__ == "__main__":
    main()
