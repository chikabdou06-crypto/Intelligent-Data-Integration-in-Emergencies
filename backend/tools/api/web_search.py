from duckduckgo_search import DDGS
from backend.core.base_tool import BaseTool
from backend.core.registry import register_tool

@register_tool(name="web_search", category="API")
class WebSearchTool(BaseTool):
    name = "web_search"
    description = (
        "Searches the live internet using DuckDuckGo to answer general questions or find recent news. "
        "Returns short snippets of text from the top search results. "
        "Use this as a fallback if the local vault or other specialized APIs don't have the answer."
    )
    category = "API"

    def execute(self, query: str, max_results: int = 3) -> dict:
        """
        Executes a web search for the given query.
        Limits the results to a small number to save tokens.
        """
        if not query:
            return {"status": "error", "message": "Query cannot be empty."}

        # Hardcap the results to 5 to prevent token explosion
        limit = min(max(1, max_results), 5)

        try:
            results = []
            # We use DDGS context manager to properly close the session
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=limit):
                    results.append({
                        "title": r.get("title"),
                        "snippet": r.get("body"),
                        "url": r.get("href")
                    })
            
            if not results:
                return {
                    "status": "success", 
                    "query": query, 
                    "message": "No search results found.",
                    "data": []
                }

            return {
                "status": "success",
                "source": "DuckDuckGo Web Search",
                "query": query,
                "data": results
            }

        except Exception as e:
            return {"status": "error", "message": f"Web search failed: {str(e)}"}
