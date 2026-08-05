import os
import sys
import json
from dotenv import load_dotenv
load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.tools.api.aemet_climatology import AemetClimatologyTool
from backend.tools.api.aemet_observations import AemetObservationsTool
from backend.tools.api.aemet_mountain import AemetMountainTool
from backend.tools.api.aemet_lightning import AemetLightningTool
from backend.tools.api.vision_map_analyzer import VisionMapAnalyzerTool

def print_result(name, result):
    print(f"\n{'='*50}\n[ {name.upper()} ]\n{'='*50}")
    if result.get("status") == "success":
        # Print a formatted subset of the data
        res_copy = {k: v for k, v in result.items() if k != "data"}
        print("METADATA:")
        print(json.dumps(res_copy, indent=2, ensure_ascii=False))
        
        if "data" in result:
            print("\nSAMPLE DATA PREVIEW:")
            if isinstance(result["data"], list) and len(result["data"]) > 0:
                print(json.dumps(result["data"][0], indent=2, ensure_ascii=False))
                print(f"... (and {len(result['data']) - 1} more items)")
            else:
                text_data = str(result["data"])
                print(text_data[:500] + "..." if len(text_data) > 500 else text_data)
        
        if "map_url" in result:
            print(f"\nMAP RENDER: {result['map_url']}")
    else:
        print("ERROR:", result)

def main():
    # 1. Climatology (Normals for Madrid)
    clim = AemetClimatologyTool()
    print_result("CLIMATOLOGY (Madrid Normals)", clim.execute(query_type="normals", station_id="madrid"))

    # 2. Observations (Current for Madrid)
    obs = AemetObservationsTool()
    print_result("OBSERVATIONS (Madrid Current)", obs.execute(query_type="current_station", station_id="madrid"))

    # 3. Mountain (Pyrenees Forecast)
    mtn = AemetMountainTool()
    print_result("MOUNTAIN FORECAST (Pyrenees)", mtn.execute(area="pirineos", day=0))

    # 4. Lightning
    ltn = AemetLightningTool()
    print_result("LIGHTNING MAP", ltn.execute())
