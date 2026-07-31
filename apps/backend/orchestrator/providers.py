from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
from apps.backend.core.schemas import OrchestratedPrompt

class BaseLLMProvider(ABC):
    """
    Abstract interface for LLM model providers (OpenAI, Anthropic, Local models).
    """
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    async def generate_response(self, prompt: OrchestratedPrompt) -> Tuple[str, int, float]:
        """
        Calls the LLM provider.
        Returns a tuple: (generated_text, token_count, estimated_cost_usd)
        """
        pass


class OpenAIProvider(BaseLLMProvider):
    """
    Concrete implementation of OpenAI LLM Provider.
    """
    @property
    def provider_name(self) -> str:
        return "OpenAI"

    async def generate_response(self, prompt: OrchestratedPrompt) -> Tuple[str, int, float]:
        # Simulated API call to OpenAI (gpt-4-turbo)
        generated_text = f"[OpenAI Response via {prompt.model_name}] Generación técnica y de código correcta para:\n'{prompt.user_prompt[:80]}...'"
        tokens = len(prompt.system_prompt + prompt.user_prompt) // 4 + 100
        cost = tokens * 0.00001 # mock rate
        return generated_text, tokens, cost


class AnthropicProvider(BaseLLMProvider):
    """
    Concrete implementation of Anthropic LLM Provider.
    """
    @property
    def provider_name(self) -> str:
        return "Anthropic"

    async def generate_response(self, prompt: OrchestratedPrompt) -> Tuple[str, int, float]:
        # Simulated API call to Anthropic (claude-3-opus)
        generated_text = f"[Anthropic Response via {prompt.model_name}] Análisis conceptual estructurado detallado para:\n'{prompt.user_prompt[:80]}...'"
        tokens = len(prompt.system_prompt + prompt.user_prompt) // 4 + 150
        cost = tokens * 0.000015 # mock rate
        return generated_text, tokens, cost
