"""
Base Tool Abstraction & Schema Introspection Framework.
======================================================

Academic Framework & Systemic Context:
--------------------------------------
In an autonomous agentic architecture, tools constitute the operational interface between the
symbolic planner and the external physical environment (APIs, geospatial layers, local file vaults).
To prevent cascading failures across multi-step execution Directed Acyclic Graphs (DAGs),
tool execution must be strictly standardized and fail-safe.

This module formalizes:

1. Canonical Contract & Error Boundary (`safe_execute`):
   Autonomous tool calling can encounter transient network drops, socket timeouts, invalid
   parameter types, or upstream API rate limits. Instead of propagating unhandled Python
   exceptions up the call stack, `safe_execute` catches all runtime errors and encapsulates
   them into a deterministic JSON schema:
     $$\\mathcal{R} = \\langle \\text{status}, \\text{source}, \\text{data}, \\text{metadata}, \\text{error\\_message} \\rangle$$
   This contract ensures the Orchestrator and Reflection Loop can inspect execution outcomes
   symbolically without crashing.

2. Dynamic Reflection-Based Schema Synthesis (`get_schema`):
   Rather than manually writing redundant JSON schemas for each tool, `BaseTool` uses Python
   runtime type introspection (`inspect.signature`) to derive OpenAPI / JSON-Schema compliant
   parameter specifications directly from Python type hints (`int`, `str`, `float`, `list`, `bool`).
   These schemas are harvested by the Planner and exported to the Model Context Protocol (MCP) server.

3. Cache Invariance:
   Each tool subclass declares its memoization policy via `cacheable` and `cache_ttl_hours`,
   enabling the orchestrator to consult the deterministic SQLite cache before initiating
   expensive network I/O.
"""

import inspect
import traceback
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseTool(ABC):
    """
    Abstract Base Class for all Municipal Intelligence Agent Tools.
    
    Subclasses must implement `execute(**kwargs)` with explicit type annotations.
    """
    
    name: str = "BaseTool"
    description: str = "Base description for tool capabilities and usage context."
    category: str = "general"
    cacheable: bool = True
    cache_ttl_hours: int = 6  # Temporal invalidation window (0 = infinite / immutable)
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        Execute the tool's core logic with the provided arguments.
        
        Must be implemented by concrete subclasses. May raise exceptions freely,
        as calls are routed through `safe_execute()`.
        
        Args:
            **kwargs: Dynamically supplied parameters validated against `get_schema()`.
            
        Returns:
            Structured payload (dictionary, list, or primitive) representing tool output.
        """
        pass
    
    def safe_execute(self, **kwargs) -> Dict[str, Any]:
        """
        Executes `execute()` within an isolated error boundary and enforces a canonical schema.
        
        Standard Output Schema:
        -----------------------
        {
            "status": "success" | "error",
            "source": "<tool_name>",
            "data": { ... },
            "metadata": { ... },       # Key-value pairs for easy downstream dependency piping
            "error_message": None | "Detailed string description of failure"
        }
        
        Returns:
            Canonical dictionary guaranteed to match the agent pipeline's expectations.
        """
        try:
            raw_result = self.execute(**kwargs)
            
            # If the tool implementation already returns a conformant schema, normalize & return
            if isinstance(raw_result, dict) and "status" in raw_result:
                raw_result.setdefault("source", self.name)
                raw_result.setdefault("data", raw_result.get("data", {}))
                raw_result.setdefault("metadata", {})
                raw_result.setdefault("error_message", None)
                
                if raw_result["status"] == "error":
                    raw_result.setdefault(
                        "error_message",
                        raw_result.get("message", "Tool signaled an unspecified error condition")
                    )
                return raw_result
            
            # Wrap raw dictionary or primitive into standard schema
            return {
                "status": "success",
                "source": self.name,
                "data": raw_result if isinstance(raw_result, (dict, list)) else {"value": raw_result},
                "metadata": {},
                "error_message": None
            }
            
        except Exception as e:
            error_trace = traceback.format_exc()
            # Log failure trace to stderr for operational monitoring without breaking JSON protocols
            print(f"  [BaseTool.safe_execute] {self.name} FAILED: {e}\n{error_trace}")
            return {
                "status": "error",
                "source": self.name,
                "data": {},
                "metadata": {},
                "error_message": f"{type(e).__name__}: {str(e)}"
            }
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """
        Dynamically synthesize an OpenAPI / JSON-Schema specification from `execute` type hints.
        
        Inspects parameter names, annotations, and defaults to construct the formal
        parameter validation dictionary used by LLM function calling and MCP clients.
        
        Returns:
            JSON-Schema dictionary with keys `name`, `description`, and `parameters`.
        """
        sig = inspect.signature(cls.execute)
        properties: Dict[str, Dict[str, str]] = {}
        required: List[str] = []
        
        for name, param in sig.parameters.items():
            # Exclude instance reference and variadic kwargs
            if name == "self" or param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue
                
            # Map Python types to standard JSON Schema primitive types
            param_type = "string"
            if param.annotation == int:
                param_type = "integer"
            elif param.annotation == bool:
                param_type = "boolean"
            elif param.annotation == float:
                param_type = "number"
            elif param.annotation in (list, List) or getattr(param.annotation, "__origin__", None) in (list, List):
                param_type = "array"
            elif param.annotation in (dict, Dict) or getattr(param.annotation, "__origin__", None) in (dict, Dict):
                param_type = "object"
                
            properties[name] = {"type": param_type}
            
            # If no default value is defined, designate as mandatory
            if param.default == inspect.Parameter.empty:
                required.append(name)
                
        return {
            "name": cls.name,
            "description": cls.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
