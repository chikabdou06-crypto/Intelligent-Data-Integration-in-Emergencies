import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import sys
import os

async def main():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", "mcp", "mcp_server.py")],
        env=os.environ.copy()
    )

    print("Starting client...")
    async with stdio_client(server_params) as (read, write):
        print("Connected to stdio.")
        async with ClientSession(read, write) as session:
            print("Session created. Initializing...")
            await session.initialize()
            print("Initialized. Listing tools...")
            tools = await session.list_tools()
            print(f"Found {len(tools.tools)} tools.")
            
if __name__ == "__main__":
    asyncio.run(main())
