import os
import time
from typing import Optional, List
from backend.core.providers.base import BaseLLMProvider

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

class GeminiProvider(BaseLLMProvider):
    def __init__(self, models: List[str], temperature: float = 0.1):
        super().__init__(models, temperature)
        api_key = os.environ.get("GEMINI_API_KEY", os.environ.get("GOOGLE_API_KEY", ""))
        
        if not api_key:
            print("[WARNING] GEMINI_API_KEY is not set.")
            self.client = None
        elif not genai:
            print("[WARNING] google-genai SDK not installed.")
            self.client = None
        else:
            self.client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(
                    retry_options=types.HttpRetryOptions(attempts=1),
                    timeout=30000
                )
            )
            self.is_configured = True

    def generate(self, prompt: str, image_bytes: Optional[bytes] = None) -> str:
        if not self.is_configured:
            raise Exception("Gemini provider is not configured.")
            
        last_error = None
        for model in self.models:
            print(f"[LLM] Attempting Gemini model: {model}")
            try:
                if image_bytes:
                    contents = [
                        prompt,
                        types.Part.from_bytes(data=image_bytes, mime_type='image/png')
                    ]
                else:
                    contents = prompt
                    
                response = self.client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(temperature=self.temperature)
                )
                text_res = response.text
                if not text_res:
                    raise Exception("Gemini API returned an empty or None response.")
                return str(text_res)
            except Exception as e:
                err = str(e)
                print(f"[LLM] Gemini {model} failed: {err[:200]}... Falling back.")
                last_error = e
                
        raise Exception(f"All Gemini models failed. Last error: {last_error}")

    def generate_with_schema(self, prompt: str, response_schema: dict) -> str:
        """
        Generates a response constrained to the provided JSON schema.
        Uses Gemini's native structured output — the model cannot output
        values outside the schema's enum constraints.
        """
        if not self.is_configured:
            raise Exception("Gemini provider is not configured.")

        last_error = None
        for model in self.models:
            print(f"[LLM] Attempting schema-constrained Gemini model: {model}")
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=self.temperature,
                        response_mime_type="application/json",
                        response_schema=response_schema,
                    )
                )
                text_res = response.text
                if not text_res:
                    raise Exception("Gemini schema-constrained API returned empty response.")
                return str(text_res)
            except Exception as e:
                err = str(e)
                print(f"[LLM] Gemini schema {model} failed: {err[:200]}... Falling back.")
                last_error = e

        raise Exception(f"All Gemini schema models failed. Last error: {last_error}")
