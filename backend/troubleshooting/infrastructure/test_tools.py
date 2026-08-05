import unittest
import sys
import os
from dotenv import load_dotenv

# Add project root to sys path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", ".."))
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

    def test_neo4j_query_schema(self):
        # We assume Neo4j credentials might not be configured in the test environment
        # so we just test that the tool exists and doesn't crash before execution.
        tool = get_tool("neo4j_query")
        self.assertEqual(tool.name, "neo4j_query")

if __name__ == '__main__':
    unittest.main()
