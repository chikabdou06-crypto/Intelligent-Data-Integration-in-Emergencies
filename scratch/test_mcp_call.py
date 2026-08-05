from backend.mcp_core.mcp_client import get_mcp_client

mcp = get_mcp_client()
print("Calling siscova_earthquakes via MCP...")
try:
    res = mcp.call_tool("siscova_earthquakes", {"limit": 5})
    print("MCP Result:", res)
except Exception as e:
    import traceback
    traceback.print_exc()
    print("MCP Error:", e)
