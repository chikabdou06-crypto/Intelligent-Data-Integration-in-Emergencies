import os
from typing import Optional, List
from backend.core.providers.base import BaseLLMProvider

class HFProvider(BaseLLMProvider):
    def __init__(self, models: List[str], temperature: float = 0.1):
        super().__init__(models, temperature)
        hf_token = os.environ.get("HF_TOKEN", "")
        
        self.client = None
        if hf_token:
            try:
                from huggingface_hub import InferenceClient
                self.client = InferenceClient(token=hf_token)
                self.is_configured = True
                print("[LLM] Hugging Face fallback provider initialized.")
            except ImportError:
                print("[WARNING] huggingface_hub not installed. Run: pip install huggingface_hub")
        else:
            print("[WARNING] HF_TOKEN is not set. Hugging Face fallback disabled.")

    def generate(self, prompt: str, image_bytes: Optional[bytes] = None) -> str:
        if not self.is_configured:
            raise Exception("Hugging Face provider is not configured.")
        if image_bytes:
            raise Exception("Hugging Face provider does not currently support image inputs in this implementation.")
            
        last_error = None
        for model in self.models:
            print(f"[LLM] Attempting HF model: {model}")
            try:
                result = self.client.chat_completion(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=4096,
                    temperature=self.temperature,
                )
                return result.choices[0].message.content
            except Exception as e:
                err = str(e)
                print(f"[LLM] HF {model} failed: {err[:200]}... Falling back.")
                last_error = e
                
        raise Exception(f"All HF models failed. Last error: {last_error}")
