import os
import requests
from typing import Optional, List
from backend.core.providers.base import BaseLLMProvider

class OllamaProvider(BaseLLMProvider):
    def __init__(self, models: List[str], temperature: float = 0.1):
        super().__init__(models, temperature)
        self.ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
        self.is_configured = True # Ollama is locally hosted, assume configured

    def generate(self, prompt: str, image_bytes: Optional[bytes] = None) -> str:
        if image_bytes:
            raise Exception("Ollama provider does not currently support image inputs in this implementation.")
            
        last_error = None
        for model in self.models:
            print(f"[LLM] Attempting Ollama model: {model}")
            try:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "keep_alive": -1,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": 1024
                    }
                }
                if "JSON Response:" in prompt or "```json" in prompt:
                    payload["format"] = "json"

                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()
                return response.json().get("response", "")
            except Exception as e:
                err = str(e)
                print(f"[LLM] Ollama {model} failed: {err[:200]}... Falling back.")
                last_error = e
                
        raise Exception(f"All Ollama models failed. Last error: {last_error}")
