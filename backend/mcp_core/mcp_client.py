"""
Model Context Protocol (MCP) Client Manager & Event Loop Bridge.
================================================================

Academic Framework & Systemic Context:
--------------------------------------
The Model Context Protocol (MCP) client library (`mcp.client.stdio`) requires an active
`asyncio` event loop for its asynchronous stream readers and writers. However, the agent's
core planning, orchestration, and evaluation pipelines often operate in synchronous worker
threads or synchronous test harnesses.

This module provides a thread-safe singleton manager (`MCPClientManager`):
1. Background Async Event Loop:
   Spawns an isolated daemon OS thread running a dedicated `asyncio` event loop.
2. Cross-Thread Coroutine Dispatch:
   Dispatches asynchronous MCP requests (`session.list_tools`, `session.call_tool`) from any
   calling thread using `asyncio.run_coroutine_threadsafe()`, blocking with deterministic timeouts.
3. Process Supervision:
   Launches the companion `mcp_server.py` as a managed subprocess via `StdioServerParameters`,
   passing parent environment variables (including API tokens).
4. Graceful Teardown:
   Ensures subprocess pipes, context managers, and event loops are cleanly flushed and closed
   on application shutdown (`lifespan` in `app.py`).
"""

import asyncio
import threading
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClientManager:
    """
    Supervises a background asyncio event loop and client session connected to the local MCP server.
    """
    
    def __init__(self, timeout_sec: float = 30.0):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True, name="MCPClientWorker")
        self.thread.start()
        
        self.session: Optional[ClientSession] = None
        self.stdio_cm = None
        self.session_cm = None
        self._connected_event = threading.Event()
        self._shutdown_event = asyncio.Event()
        
        # Schedule asynchronous client startup inside the worker event loop
        asyncio.run_coroutine_threadsafe(self._startup(), self.loop)
        
        # Await connection initialization with watchdog timeout
        if not self._connected_event.wait(timeout=timeout_sec):
            raise RuntimeError(f"MCP Client failed to establish stdio connection within {timeout_sec}s.")
        
    def _run_loop(self) -> None:
        """Dedicated thread target maintaining the asyncio event loop."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
        
    async def _startup(self) -> None:
        """
        Subprocess launcher and MCP handshake task executing inside the background event loop.
        """
        try:
            mcp_server_path = os.path.join(os.path.dirname(__file__), "mcp_server.py")
            server_params = StdioServerParameters(
                command=sys.executable,
                args=[mcp_server_path],
                env=os.environ.copy()
            )
            
            # Establish stdio pipes with the subprocess
            self.stdio_cm = stdio_client(server_params)
            self.read, self.write = await self.stdio_cm.__aenter__()
            
            # Initialize the MCP JSON-RPC protocol session
            self.session_cm = ClientSession(self.read, self.write)
            self.session = await self.session_cm.__aenter__()
            await self.session.initialize()
            
            print("[MCP Client] Successfully connected to Municipal Intelligence MCP Server.", file=sys.stderr)
            self._connected_event.set()
            
            # Await termination signal
            await self._shutdown_event.wait()
            
            # Graceful cleanup inside the owning event loop
            await self.session_cm.__aexit__(None, None, None)
            await self.stdio_cm.__aexit__(None, None, None)
            
        except Exception as e:
            print(f"[MCP Client] Startup or protocol handshake error: {e}", file=sys.stderr)
            self._connected_event.set()
        
    def get_tools(self, timeout_sec: float = 10.0) -> Any:
        """
        Synchronously fetch the catalog of registered tools from the MCP server.
        
        Args:
            timeout_sec: Maximum wait duration before raising TimeoutError.
            
        Returns:
            List of Tool objects exported by the MCP server.
        """
        if not self.session:
            raise RuntimeError("MCP Client is not connected to a server session.")
        future = asyncio.run_coroutine_threadsafe(self.session.list_tools(), self.loop)
        return future.result(timeout=timeout_sec)
        
    def call_tool(self, name: str, arguments: Dict[str, Any], timeout_sec: float = 120.0) -> Any:
        """
        Synchronously invoke a tool over the MCP JSON-RPC protocol.
        
        Args:
            name: Identifier of the tool to execute.
            arguments: Dictionary of arguments to pass to the tool.
            timeout_sec: Execution deadline in seconds.
            
        Returns:
            Tool call response payload returned by the MCP server.
        """
        if not self.session:
            raise RuntimeError("MCP Client is not connected to a server session.")
        future = asyncio.run_coroutine_threadsafe(self.session.call_tool(name, arguments), self.loop)
        return future.result(timeout=timeout_sec)
        
    def close(self) -> None:
        """
        Signal the background task to release subprocess handles and stop the event loop.
        """
        self.loop.call_soon_threadsafe(self._shutdown_event.set)
        
        # Give subprocess resources 2 seconds to cleanly exit
        try:
            self.thread.join(timeout=2.0)
        except Exception:
            pass
        finally:
            self.loop.call_soon_threadsafe(self.loop.stop)


# ---------------------------------------------------------------------------
# Global Singleton Lifecycle Management
# ---------------------------------------------------------------------------
_mcp_manager: Optional[MCPClientManager] = None


def init_mcp_client() -> None:
    """Initialize the singleton MCP client instance if not already running."""
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MCPClientManager()


def get_mcp_client() -> MCPClientManager:
    """Retrieve the active MCP client manager, initializing it lazily if needed."""
    global _mcp_manager
    if _mcp_manager is None:
        init_mcp_client()
    return _mcp_manager


def close_mcp_client() -> None:
    """Tear down and terminate the MCP client manager and child subprocess."""
    global _mcp_manager
    if _mcp_manager is not None:
        try:
            _mcp_manager.close()
        except Exception as e:
            print(f"[MCP Client] Warning during shutdown: {e}", file=sys.stderr)
        finally:
            _mcp_manager = None
