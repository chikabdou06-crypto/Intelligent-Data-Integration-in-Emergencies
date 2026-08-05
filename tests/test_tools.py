import unittest
import sys
import os
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Load env variables from .env file
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from backend.core.registry import get_tool

class TestTools(unittest.TestCase):

    def test_general_tool(self):
        tool = get_tool("general")
        result = tool.execute()
        self.assertEqual(result.get("status"), "success")

    def test_weather_tool(self):
        tool = get_tool("aemet_forecast")
        result = tool.execute(municipio="benidorm", mode="daily")
        self.assertIn("status", result)
        self.assertEqual(result.get("status"), "success")
        self.assertIn("municipality", result)
        self.assertIn("data", result)

    def test_boe_tool_schema(self):
        tool = get_tool("boe_get_summary")
        self.assertEqual(tool.name, "boe_get_summary")
        schema = tool.get_schema()
        self.assertIn("parameters", schema)

    def test_ine_tool_schema(self):
        tool = get_tool("ine_search_operations")
        self.assertEqual(tool.name, "ine_search_operations")
        schema = tool.get_schema()
        self.assertIn("parameters", schema)

if __name__ == '__main__':
    unittest.main()
