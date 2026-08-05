import sys
import os
import json
import asyncio
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Load Env
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from backend.core.network_patch import apply_network_patches
apply_network_patches()

from backend.core.registry import list_all_tools, get_tool

server = Server("ToolUniverse")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    tools = []
    for tool_name in list_all_tools():
        try:
            t = get_tool(tool_name)
            schema = t.get_schema()
            tools.append(Tool(
                name=schema["name"],
                description=schema.get("description", ""),
                inputSchema=schema.get("parameters", {"type": "object", "properties": {}})
            ))
        except Exception as e:
            print(f"[MCP] Error loading tool schema {tool_name}: {e}", file=sys.stderr)
    return tools

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        t = get_tool(name)
        # Using safe_execute to ensure exceptions are caught inside the tool logic
        result = t.safe_execute(**arguments)
        return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
    except Exception as e:
        return [TextContent(type="text", text=f'{{"status": "error", "message": "Failed to call MCP tool: {str(e)}"}}')]

async def main():
    print("[MCP] Starting ToolUniverse RAG MCP Server...", file=sys.stderr)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
