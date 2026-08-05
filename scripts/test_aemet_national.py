import sys
import os
from dotenv import load_dotenv

sys.path.insert(0, '.')
load_dotenv('.env')

from backend.tools.api.aemet_warnings import AemetWarningsTool
from backend.tools.api.aemet_observations import AemetObservationsTool
from backend.tools.api.aemet_climatology import AemetClimatologyTool

def main():
    print('--- TESTING WARNINGS (Madrid) ---')
    warn_tool = AemetWarningsTool()
    res_warn = warn_tool.execute(region='madrid')
    print(f"Status: {res_warn.get('status')}")
    print(f"Region: {res_warn.get('region')}")
    print(f"Active Warnings: {res_warn.get('active_warnings_count')}")

    print('\n--- TESTING OBSERVATIONS (Sevilla) ---')
    obs_tool = AemetObservationsTool()
    res_obs = obs_tool.execute(station_name='sevilla')
    print(f"Status: {res_obs.get('status')}")
    print(f"Matched Station: {res_obs.get('station_name')} (ID: {res_obs.get('station_id')})")
    
    data = res_obs.get('data', [])
    if data:
        print(f"Latest Temp: {data[-1].get('temperatura')} C") # Fetch latest available

    print('\n--- TESTING CLIMATOLOGY (Barcelona) ---')
    clim_tool = AemetClimatologyTool()
    res_clim = clim_tool.execute(query_type='normals', station_name='barcelona')
    print(f"Status: {res_clim.get('status')}")
    print(f"Matched Station: {res_clim.get('station_name')} (ID: {res_clim.get('station_id')})")
    
if __name__ == "__main__":
    main()
