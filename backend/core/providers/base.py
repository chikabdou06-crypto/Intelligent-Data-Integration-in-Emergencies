from abc import ABC, abstractmethod
from typing import Optional, List

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, models: List[str], temperature: float = 0.1):
        self.models = models
        self.temperature = temperature
        self.is_configured = False
        
    @abstractmethod
    def generate(self, prompt: str, image_bytes: Optional[bytes] = None) -> str:
        """
        Generates text given a prompt. Should try models in fallback order.
        Raises an exception if all models fail.
        """
        pass
