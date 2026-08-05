import importlib
import logging

logger = logging.getLogger(__name__)

# The map of tool_name -> (module_path, class_name)
_LAZY_REGISTRY = {}

try:
    from backend.core._lazy_registry_static import STATIC_TOOL_MAP
    _LAZY_REGISTRY = STATIC_TOOL_MAP
except ImportError:
    logger.warning("_lazy_registry_static.py not found. Run generate_lazy_registry.py to build it.")
    STATIC_TOOL_MAP = {}

def register_tool(name: str, category: str = "general"):
    """
    Decorator to mark a BaseTool subclass as an official agent tool.
    During runtime, tools are lazily loaded from the static map.
    """
    def decorator(cls):
        cls.name = name
        cls.category = category
        return cls
    return decorator

def get_tool(tool_name: str):
    """
    Lazily imports the python module and returns an instantiated Tool object.
    """
    if tool_name not in _LAZY_REGISTRY:
        raise ValueError(f"Tool '{tool_name}' not found in lazy registry.")
    
    module_path, class_name = _LAZY_REGISTRY[tool_name]
    module = importlib.import_module(module_path)
    tool_class = getattr(module, class_name)
    return tool_class()

def list_all_tools():
    """
    Returns a list of all registered tool names instantly without importing them.
    """
    return list(_LAZY_REGISTRY.keys())
