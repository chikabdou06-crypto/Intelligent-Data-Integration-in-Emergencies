import asyncio
import threading
import sys
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClientManager:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        
        self.session = None
        self.stdio_cm = None
        self.session_cm = None
        self._connected_event = threading.Event()
        
        self._shutdown_event = asyncio.Event()
        
        # Schedule startup
        asyncio.run_coroutine_threadsafe(self._startup(), self.loop)
        
        # Wait for the client to be ready
        if not self._connected_event.wait(timeout=30):
            raise RuntimeError("MCP Client failed to start within 30 seconds.")
        
    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
        
    async def _startup(self):
        try:
            mcp_server_path = os.path.join(os.path.dirname(__file__), "mcp_server.py")
            server_params = StdioServerParameters(
                command=sys.executable,
                args=[mcp_server_path],
                env=os.environ.copy()
            )
            self.stdio_cm = stdio_client(server_params)
            self.read, self.write = await self.stdio_cm.__aenter__()
            
            self.session_cm = ClientSession(self.read, self.write)
            self.session = await self.session_cm.__aenter__()
            await self.session.initialize()
            print("[MCP Client] Initialized successfully.")
            self._connected_event.set()
            
            # Wait until shutdown is signaled
            await self._shutdown_event.wait()
            
            # Perform cleanup inside the same task
            await self.session_cm.__aexit__(None, None, None)
            await self.stdio_cm.__aexit__(None, None, None)
        except Exception as e:
            print(f"[MCP Client] Startup error: {e}")
            self._connected_event.set()
        
    def get_tools(self):
        """Synchronously fetch tools from the MCP server."""
        future = asyncio.run_coroutine_threadsafe(self.session.list_tools(), self.loop)
        return future.result(timeout=10)
        
    def call_tool(self, name: str, arguments: dict):
        """Synchronously execute a tool via the MCP server."""
        future = asyncio.run_coroutine_threadsafe(self.session.call_tool(name, arguments), self.loop)
        return future.result(timeout=120)
        
    def close(self):
        """Signal the background task to close and stop the loop."""
        self.loop.call_soon_threadsafe(self._shutdown_event.set)
        
        # Wait a bit for cleanup
        try:
            self.thread.join(timeout=2)
        except Exception:
            pass
        finally:
            self.loop.call_soon_threadsafe(self.loop.stop)


# Global singleton
_mcp_manager = None

def init_mcp_client():
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MCPClientManager()

def get_mcp_client() -> MCPClientManager:
    global _mcp_manager
    if _mcp_manager is None:
        init_mcp_client()
    return _mcp_manager

def close_mcp_client():
    global _mcp_manager
    if _mcp_manager:
        _mcp_manager.close()
        _mcp_manager = None
