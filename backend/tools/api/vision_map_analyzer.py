import requests
from backend.core.base_tool import BaseTool
from backend.core.registry import register_tool
from backend.core.llm import LLMClient

@register_tool(name="vision_map_analyzer", category="ANALYSIS")
class VisionMapAnalyzerTool(BaseTool):
    name = "vision_map_analyzer"
    description = (
        "A Multimodal Vision AI tool that reads and analyzes image maps. "
        "Use this tool when you need to answer a user's question about an image map you just fetched "
        "(like AEMET Fire Risk or Lightning maps). "
        "Arguments: "
        "- image_url (str): The direct URL to the image map. "
        "- question (str): The specific question you want the Vision AI to answer about the map."
    )
    category = "ANALYSIS"
    cacheable = False

    def execute(self, image_url: str, question: str) -> dict:
        try:
            # 1. Download the image bytes
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(image_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                return {
                    "status": "error",
                    "message": f"Expected an image, but received {content_type}. URL might be expired or invalid."
                }
                
            image_bytes = response.content
            
            if not image_bytes:
                return {
                    "status": "error",
                    "message": "Failed to download image bytes: Empty response."
                }
                
            # 2. Feed to LLM Vision model
            # We specifically request Gemini here as it has strong native vision capabilities
            llm = LLMClient(role="synthesizer", models=["gemini-3.5-flash", "gemini-2.5-flash", "gemini-2.0-flash"])
            
            prompt = (
                f"You are an expert geospatial map analyst.\n"
                f"Analyze the attached image map to answer the following question:\n"
                f"QUESTION: {question}\n\n"
                f"Provide a highly detailed and reasoned answer based ONLY on what you can visually see in the map."
            )
            
            analysis = llm.generate(prompt, image_bytes=image_bytes)
            
            return {
                "status": "success",
                "image_url": image_url,
                "question": question,
                "analysis": analysis
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"Network error downloading the image: {str(e)}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Vision analysis failed: {str(e)}"
            }
