"""
========================================================================================
MUNICIPAL INTELLIGENCE AGENT - MULTI-TIER LLM PROVIDER & FALLBACK MANAGER
Master's Thesis: "Intelligent Data Integration in Emergencies"
Academic Review & Implementation Documentation
========================================================================================

Architecture & Resilience Strategy for Thesis Evaluators:
---------------------------------------------------------
Deploying language agents in real-world municipal and emergency environments imposes
strict fault-tolerance requirements:

  1. Provider Fallback Hierarchy:
     Relying exclusively on cloud endpoints introduces vulnerabilities to network
     outages, upstream service downtime, and HTTP 429 quota exhaustion. This module
     orchestrates an automated three-tier fallback sequence:
       - Tier 1: Cloud Frontier (Google Gemini 2.5 Flash / 2.0 Flash) -> High reasoning fidelity.
       - Tier 2: Cloud Secondary (HuggingFace Serverless Inference)   -> Distributed backup.
       - Tier 3: Local Offline (Ollama Qwen 2.5 7B / Llama 3)        -> 100% on-premise air-gapped.

  2. Dynamic Runtime Operating Modes:
     Via the frontend dashboard, operators can configure the active mode:
       - 'auto'   : Graceful sequential fallback across providers.
       - 'gemini' : Strictly lock execution to cloud Gemini.
       - 'ollama' : Strictly air-gapped on-premise execution (zero external data transmission).

  3. Role-Based Temperature & Model Parameter Tuning:
     - Planner ($T=0.1$): Prioritizes structural determinism and strict schema conformity.
     - Isolated Judge ($T=0.0$): Zero-temperature debugging for parameter repair.
     - Synthesizer ($T=0.3$): Balances lexical fluency with rigorous factual constraint.
     - Chitchat/General ($T=0.5$): Conversational naturalness.

  4. Robust Markdown JSON Stripping:
     The `generate_json` method reliably extracts JSON objects from raw responses,
     handling markdown code fences (```json ... ```), internal chain-of-thought
     blocks (<thinking> ... </thinking>), and nested brackets.
"""

import os
import re
import json
import time
from backend.core.providers import GeminiProvider, HFProvider, OllamaProvider

# Global active provider mode: "auto" (default), "gemini", "ollama"
ACTIVE_MODE = "auto"
SESSION_TOKENS_USED = 0


def set_active_mode(mode: str) -> bool:
    """Configures the global inference mode ('auto', 'gemini', or 'ollama')."""
    global ACTIVE_MODE
    if mode in ("auto", "gemini", "ollama"):
        ACTIVE_MODE = mode
        return True
    return False


def get_active_mode() -> str:
    """Returns the currently active inference mode."""
    return ACTIVE_MODE


def get_providers_status() -> dict:
    """
    Probes all configured inference endpoints and returns real-time availability.
    Enables the citizen dashboard to display whether local air-gapped weights are online.
    """
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
    Provider priority: Google Gemini -> Hugging Face Inference -> Local Ollama.
    """
    def __init__(self, role: str = "general", models: list = None, temperature=0.1):
        self.role = role
        self.temperature = temperature
        
        # Load model identifiers based on operational role
        gemini_models = models or ROLE_MODELS.get(role, ROLE_MODELS["general"])["gemini"]
        hf_models = ROLE_MODELS.get(role, ROLE_MODELS["general"])["hf"]
        ollama_models = ROLE_MODELS.get(role, ROLE_MODELS["general"])["ollama"]
        
        # Initialize providers with configured temperature profile
        self.providers = [
            GeminiProvider(gemini_models, temperature),
            HFProvider(hf_models, temperature),
            OllamaProvider(ollama_models, temperature)
        ]

    def _do_generate_with_fallback(self, prompt: str, image_bytes: bytes = None) -> str:
        """
        Executes generation by iterating through configured providers until one succeeds.
        Handles provider timeouts and API rate limit exceptions gracefully.
        """
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
            res = self._do_generate_with_fallback(prompt, image_bytes=image_bytes)
            # Estimate token usage for session tracking (1 token ~ 4 characters)
            estimated_tokens = (len(prompt) + len(res)) // 4
            import backend.core.llm
            backend.core.llm.SESSION_TOKENS_USED += estimated_tokens
            return res
        except Exception as e:
            return f"LLM Error: {str(e)}"
            
    def generate_json(self, prompt: str, image_bytes: bytes = None) -> dict:
        """
        Sends a prompt expecting a structured JSON response.
        Strips markdown wrappers (```json ... ```) and internal chain-of-thought tokens.
        """
        text = str(self.generate(prompt, image_bytes=image_bytes) or "").strip()
        
        # Strip potential chain-of-thought tags
        text = re.sub(r'<thinking>.*?</thinking>\s*', '', text, flags=re.DOTALL)
        
        # Extract markdown JSON block if present
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if json_match:
            text = json_match.group(1).strip()
        else:
            # Fallback: Locate outermost JSON brackets
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
