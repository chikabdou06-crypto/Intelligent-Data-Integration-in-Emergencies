import os
import re
import json
import time
from backend.core.providers import GeminiProvider, HFProvider, OllamaProvider

# Global active provider mode: "auto" (default), "gemini", "ollama"
ACTIVE_MODE = "auto"

def set_active_mode(mode: str) -> bool:
    global ACTIVE_MODE
    if mode in ("auto", "gemini", "ollama"):
        ACTIVE_MODE = mode
        return True
    return False

def get_active_mode() -> str:
    return ACTIVE_MODE

def get_providers_status() -> dict:
    import urllib.request
    gemini_ready = bool(os.getenv("GEMINI_API_KEY", "").strip())
    ollama_ready = False
    ollama_models = []
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags", headers={"User-Agent": "Agent/1.0"})
        with urllib.request.urlopen(req, timeout=0.8) as resp:
            data = json.loads(resp.read().decode())
            ollama_ready = True
            ollama_models = [m["name"] for m in data.get("models", [])]
    except Exception:
        pass
        
    return {
        "mode": ACTIVE_MODE,
        "gemini": {
            "available": gemini_ready,
            "name": "Google Gemini (Cloud)"
        },
        "ollama": {
            "available": ollama_ready,
            "models": ollama_models,
            "name": "Ollama (Local Offline)"
        }
    }

# Role-based model configurations
ROLE_MODELS = {
    "planner": {
        "gemini": ["gemini-flash-latest", "gemini-flash-lite-latest", "gemini-2.5-flash", "gemini-2.0-flash"],
        "hf": ["Qwen/Qwen2.5-72B-Instruct", "meta-llama/Meta-Llama-3-8B-Instruct"],
        "ollama": ["qwen2.5:7b", "llama3"]
    },
    "synthesizer": {
        "gemini": ["gemini-flash-latest", "gemini-flash-lite-latest", "gemini-2.5-flash", "gemini-2.0-flash"],
        "hf": ["Qwen/Qwen2.5-7B-Instruct", "meta-llama/Meta-Llama-3-8B-Instruct"],
        "ollama": ["qwen2.5:7b", "llama3"]
    },
    "general": {
        "gemini": ["gemini-flash-latest", "gemini-flash-lite-latest", "gemini-2.5-flash", "gemini-2.0-flash"],
        "hf": ["Qwen/Qwen2.5-7B-Instruct", "meta-llama/Meta-Llama-3-8B-Instruct"],
        "ollama": ["qwen2.5:7b", "llama3"]
    }
}

class LLMClient:
    """
    Multi-provider LLM client with automatic fallback and role-based model selection.
    Provider priority: Google Gemini -> Hugging Face Inference -> Ollama.
    """
    def __init__(self, role: str = "general", models: list = None, temperature=0.1):
        self.role = role
        self.temperature = temperature
        
        # Load models based on role
        gemini_models = models or ROLE_MODELS.get(role, ROLE_MODELS["general"])["gemini"]
        hf_models = ROLE_MODELS.get(role, ROLE_MODELS["general"])["hf"]
        ollama_models = ROLE_MODELS.get(role, ROLE_MODELS["general"])["ollama"]
        
        # Initialize providers
        self.providers = [
            GeminiProvider(gemini_models, temperature),
            HFProvider(hf_models, temperature),
            OllamaProvider(ollama_models, temperature)
        ]

    def _do_generate_with_fallback(self, prompt: str, image_bytes: bytes = None) -> str:
        """Tries providers in sequence (Gemini -> HF -> Ollama) with retries."""
        last_error = None
        
        mode = get_active_mode()
        for provider in self.providers:
            provider_name = provider.__class__.__name__
            if mode == "gemini" and "Gemini" not in provider_name:
                continue
            if mode == "ollama" and "Ollama" not in provider_name:
                continue
            if not provider.is_configured:
                continue
                
            try:
                return provider.generate(prompt, image_bytes=image_bytes)
            except Exception as e:
                print(f"[LLM] Provider {provider_name} failed: {e}")
                last_error = e
                if mode != "auto":
                    raise Exception(f"Provider {provider_name} failed: {e}")
                continue

        raise Exception(f"All configured providers failed for mode '{mode}'. Last error: {last_error}")

    def generate(self, prompt: str, image_bytes: bytes = None) -> str:
        """Sends a raw prompt to the LLM and returns the text response."""
        configured_providers = [p for p in self.providers if p.is_configured]
        if not configured_providers:
            return "Error: No LLM provider configured. Set GEMINI_API_KEY, HF_TOKEN, or start OLLAMA."
            
        try:
            return self._do_generate_with_fallback(prompt, image_bytes=image_bytes)
        except Exception as e:
            return f"LLM Error: {str(e)}"
            
    def generate_json(self, prompt: str, image_bytes: bytes = None) -> dict:
        """Sends a prompt expecting a JSON response, automatically parsing it."""
        text = str(self.generate(prompt, image_bytes=image_bytes) or "").strip()
        
        # Strip potential <thinking> blocks (if any)
        text = re.sub(r'<thinking>.*?</thinking>\s*', '', text, flags=re.DOTALL)
        
        # Look for markdown JSON block
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if json_match:
            text = json_match.group(1).strip()
        else:
            # Fallback: find first { or [
            start_idx = text.find('{')
            start_idx_arr = text.find('[')
            
            if start_idx == -1 and start_idx_arr == -1:
                return {"error": "No JSON payload found", "raw": text}
                
            if start_idx == -1 or (start_idx_arr != -1 and start_idx_arr < start_idx):
                start_idx = start_idx_arr
                end_idx = text.rfind(']')
            else:
                end_idx = text.rfind('}')
                
            if start_idx != -1 and end_idx != -1:
                text = text[start_idx:end_idx+1]
                
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"[LLM JSON Error] Could not parse: {text}")
            return {"error": f"Invalid JSON response: {e}", "raw": text}
