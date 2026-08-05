import sys
import os
import asyncio

# Ensure backend imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.mcp_core.mcp_client import get_mcp_client, close_mcp_client

def list_tools():
    print("Connecting to MCP Server...\n")
    client = get_mcp_client()
    
    try:
        async def fetch():
            return await client.session.list_tools()

        tools = asyncio.run_coroutine_threadsafe(fetch(), client.loop).result()
        
        print("=== ACTIVE MCP TOOLS ===")
        for tool in tools.tools:
            print(f"\n* Tool: {tool.name}")
            print(f"  Description: {tool.description.strip()}")
            
            schema = tool.inputSchema or {}
            params = schema.get("properties", {})
            required = schema.get("required", [])
            
            if not params:
                print("  Arguments: None")
            else:
                print("  Arguments:")
                for param, detail in params.items():
                    req_str = "REQUIRED" if param in required else "optional"
                    ptype = detail.get("type", "string")
                    print(f"    - {param} ({ptype}) [{req_str}]")
                    
        print(f"\nTotal: {len(tools.tools)} tools actively loaded.")
    finally:
        close_mcp_client()

if __name__ == "__main__":
    list_tools()
