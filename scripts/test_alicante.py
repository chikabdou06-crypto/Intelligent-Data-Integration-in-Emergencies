import sys
import os
from dotenv import load_dotenv

sys.path.insert(0, '.')
load_dotenv('.env')

from backend.tools.api.aemet_warnings import AemetWarningsTool

warn_tool = AemetWarningsTool()
res = warn_tool.execute(region='comunitat valenciana')

if res['status'] == 'success':
    warnings = res.get('data', [])
    alicante_warnings = []
    for w in warnings:
        desc = w.get('description', '').lower()
        headline = w.get('headline', '').lower()
        area = w.get('area', '').lower()
        # Alicante is written as Alicante or Alacant
        if 'alicant' in desc or 'alicant' in headline or 'alicant' in area or 'alacant' in desc or 'alacant' in headline or 'alacant' in area:
            alicante_warnings.append(w)
    
    print(f'Total Warnings in Valencia: {len(warnings)}')
    print(f'Alicante Warnings: {len(alicante_warnings)}\n')
    for i, w in enumerate(alicante_warnings):
        print(f'--- Warning {i+1} ---')
        print(f"Event: {w.get('event')}")
        print(f"Headline: {w.get('headline')}")
        print(f"Severity/Color: {w.get('severity')}")
        print(f"Onset (Activated): {w.get('onset')}")
        print(f"Expires (Ends): {w.get('expires')}")
        print(f"Area: {w.get('area')}")
        print(f"Description: {w.get('description')}")
else:
    print(res)
