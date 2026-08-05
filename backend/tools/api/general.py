from backend.core.base_tool import BaseTool
from backend.core.registry import register_tool

@register_tool(name="general", category="GENERAL")
class GeneralTool(BaseTool):
    name = "general"
    description = "Chit-chat, math, programming, and general reasoning without external data sources."
    category = "GENERAL"

    def execute(self) -> dict:
        return {"status": "success", "message": "General reasoning handled by synthesis engine."}


