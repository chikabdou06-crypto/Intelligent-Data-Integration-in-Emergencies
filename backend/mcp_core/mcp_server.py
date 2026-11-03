"""
Model Context Protocol (MCP) Server: Municipal Emergency Intelligence.
=======================================================================

Academic Framework & Systemic Context:
--------------------------------------
This module implements the server side of the Model Context Protocol (MCP, Anthropic 2024),
establishing a standardized, open inter-process communication protocol between the Municipal
Intelligence agent core and external execution environments.

Key Architectural Pillars:
--------------------------
1. Process Isolation & Fault Boundaries:
   Executing third-party API clients, web scrapers (e.g. SISCOVA), or GIS parsers inside the
   primary web server process risks unhandled crashes, memory leaks, and blocking event loops.
   The MCP server runs as an independent OS process, communicating strictly via standard
   input/output (`stdio`) JSON-RPC messages.

2. Protocol Stream Integrity via Stdout Redirection:
   Standard MCP stdio transport requires `sys.stdout` to remain 100% pristine JSON-RPC frames.
   However, external python dependencies or diagnostic routines frequently write informational
   logging to standard output.
   This implementation utilizes Python's `contextlib.redirect_stdout(sys.stderr)` during tool
   invocation, strictly confining all tool chatter to stderr while preserving pristine JSON-RPC
   framing on stdout.

3. Standard Tool Introspection:
   Exposes dynamic MCP tool descriptors (`handle_list_tools`) generated directly from
   `BaseTool.get_schema()`, bridging the agent's internal tool registry with external
   MCP-compatible LLM orchestration clients (Claude Desktop, Antigravity IDE, custom clients).
"""

import sys
import os
import json
import asyncio
import contextlib
from pathlib import Path
from typing import List

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Ensure backend and repository root reside on sys.path
MCP_CORE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = MCP_CORE_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
for p in [PROJECT_ROOT, BACKEND_DIR]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# Load environment variables (.env) for API credentials (AEMET, HF, etc.)
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

# Apply network security and socket timeout patches
from backend.core.network_patch import apply_network_patches
apply_network_patches()

from backend.core.registry import list_all_tools, get_tool

# Initialize the MCP Server instance
server = Server("Municipal Intelligence Agent")


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """
    Publish available tools to the MCP client by introspecting the registry.
    
    Transforms each registered BaseTool's JSON Schema into the official MCP Tool dataclass.
    
    Returns:
        List of MCP Tool objects containing name, description, and inputSchema.
    """
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
            # Report introspection errors to stderr without crashing the protocol handshake
            print(f"[MCP Server] Error harvesting schema for '{tool_name}': {e}", file=sys.stderr)
    return tools


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
    """
    Execute an agent tool invocation request received across the MCP JSON-RPC protocol.
    
    Enforces stdout redirection to protect the stdio framing and captures all errors
    within the standardized BaseTool safe execution boundary.
    
    Args:
        name: Identifier of the requested tool.
        arguments: Keyword arguments payload parsed from the JSON-RPC request.
        
    Returns:
        List containing a TextContent object with the formatted JSON result payload.
    """
    try:
        t = get_tool(name)
        
        # CRITICAL: Divert standard output to standard error to prevent JSON-RPC framing corruption
        with contextlib.redirect_stdout(sys.stderr):
            result = t.safe_execute(**arguments)
            
        formatted_json = json.dumps(result, indent=2, ensure_ascii=False)
        return [TextContent(type="text", text=formatted_json)]
        
    except Exception as e:
        error_payload = {
            "status": "error",
            "source": name,
            "message": f"MCP tool execution failed: {str(e)}"
        }
        return [TextContent(type="text", text=json.dumps(error_payload, ensure_ascii=False))]


async def main() -> None:
    """
    Launch the MCP server loop over standard input and output (stdio).
    """
    print("[MCP Server] Starting Municipal Intelligence MCP Server (stdio transport)...", file=sys.stderr)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
