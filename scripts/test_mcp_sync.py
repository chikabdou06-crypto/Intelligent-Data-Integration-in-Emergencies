import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.mcp_core.mcp_client import get_mcp_client, close_mcp_client

def test_mcp_client():
    client = get_mcp_client()
    
    print("Fetching tools...")
    tools_response = client.get_tools()
    print(f"Found {len(tools_response.tools)} tools.")
    
    print("\nCalling tool (e.g. math_calculator)...")
    result = client.call_tool("math_calculator", {"expression": "2 + 2"})
    print(f"Result: {result.content}")
    
    close_mcp_client()

if __name__ == "__main__":
    test_mcp_client()
