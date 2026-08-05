import unittest
import sys
import os

# Add project root to sys path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.core.registry import list_all_tools, get_tool
from backend.core.base_tool import BaseTool

class TestRegistry(unittest.TestCase):

    def test_list_all_tools(self):
        tools = list_all_tools()
        self.assertIsInstance(tools, list)
        self.assertGreater(len(tools), 0, "No tools found in registry.")
        
        # Verify core tools are present
        self.assertIn("general", tools)
        self.assertIn("aemet_forecast", tools)
        self.assertIn("csv_list", tools)

    def test_tool_instantiation(self):
        tools = list_all_tools()
        for tool_name in tools:
            try:
                tool_instance = get_tool(tool_name)
                self.assertIsInstance(tool_instance, BaseTool)
                self.assertEqual(tool_instance.name, tool_name)
                
                # Check schema generation
                schema = tool_instance.get_schema()
                self.assertIn("name", schema)
                self.assertIn("description", schema)
                self.assertIn("parameters", schema)
            except Exception as e:
                self.fail(f"Failed to instantiate tool '{tool_name}': {e}")

if __name__ == '__main__':
    unittest.main()
