import inspect
import traceback
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BaseTool(ABC):
    """
    Abstract base class for all RAG Agent Tools.
    Enforces a strict interface for parameter validation and execution.
    """
    
    name: str = "BaseTool"
    description: str = "Base description"
    category: str = "general"
    cacheable: bool = True
    cache_ttl_hours: int = 6  # Default TTL for cached results (0 = infinite)
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        Execute the tool with the given arguments.
        Must be implemented by subclasses.
        """
        pass
    
    def safe_execute(self, **kwargs) -> Dict[str, Any]:
        """
        Wraps execute() with error handling and forces a standardized response schema.
        Every tool response is guaranteed to have the same shape, preventing
        cascade failures in $PREV placeholder resolution.
        
        Standard Response Schema:
        {
            "status": "success" | "error",
            "source": "<tool_name>",
            "data": { ... },
            "metadata": { "key": "value", ... },  # Flat dict for easy $PREV access
            "error_message": None | "description of failure"
        }
        """
        try:
            raw_result = self.execute(**kwargs)
            
            # If the tool already returns our standard format, pass it through
            if isinstance(raw_result, dict) and "status" in raw_result:
                # Ensure required fields exist
                raw_result.setdefault("source", self.name)
                raw_result.setdefault("data", raw_result.get("data", {}))
                raw_result.setdefault("metadata", {})
                raw_result.setdefault("error_message", None)
                
                # If the tool reported its own error, preserve it
                if raw_result["status"] == "error":
                    raw_result.setdefault("error_message", raw_result.get("message", "Tool reported an error"))
                
                return raw_result
            
            # Wrap non-standard results into standard schema
            return {
                "status": "success",
                "source": self.name,
                "data": raw_result if isinstance(raw_result, (dict, list)) else {"value": raw_result},
                "metadata": {},
                "error_message": None
            }
            
        except Exception as e:
            error_trace = traceback.format_exc()
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
        Dynamically generate a JSON schema from the execute method's type hints.
        """
        sig = inspect.signature(cls.execute)
        properties = {}
        required = []
        
        for name, param in sig.parameters.items():
            if name == "self":
                continue
                
            # Basic type mapping
            param_type = "string"
            if param.annotation == int:
                param_type = "integer"
            elif param.annotation == bool:
                param_type = "boolean"
            elif param.annotation == float:
                param_type = "number"
            elif param.annotation == list or param.annotation == List:
                param_type = "array"
                
            properties[name] = {"type": param_type}
            
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
