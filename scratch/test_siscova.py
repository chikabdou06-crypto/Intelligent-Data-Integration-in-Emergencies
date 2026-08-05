import sys
import os

from backend.tools.api.siscova_api import SiscovaEarthquakesTool

tool = SiscovaEarthquakesTool()
res = tool.execute(limit=5)
print("Siscova result:", res)
