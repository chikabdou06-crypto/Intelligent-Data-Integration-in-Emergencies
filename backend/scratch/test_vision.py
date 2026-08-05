import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.tools.api.aemet_lightning import AemetLightningTool
from backend.tools.api.vision_map_analyzer import VisionMapAnalyzerTool

def main():
    print("==================================================")
    print("[ VISION MAP ANALYZER TEST ]")
    print("==================================================")
    
    pure_url = "https://upload.wikimedia.org/wikipedia/commons/4/47/PNG_transparency_demonstration_1.png"
    print(f"Map URL fetched: {pure_url}")
    print("Feeding to Vision Map Analyzer...\n")
    
    v_tool = VisionMapAnalyzerTool()
    v_res = v_tool.execute(
        image_url=pure_url,
        question="Describe what you see in this image."
    )
    
    print("--- ANALYSIS RESULT ---")
    if "analysis" in v_res:
        print(v_res["analysis"])
    else:
        print(json.dumps(v_res, indent=2))

if __name__ == "__main__":
    main()
