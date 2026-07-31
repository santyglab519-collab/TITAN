import time
from typing import Tuple, List, Dict, Any
from apps.backend.core.interfaces import BaseLLMOrchestrator
from apps.backend.core.schemas import OrchestratedPrompt, TraceLog
from apps.backend.orchestrator.providers import OpenAIProvider, AnthropicProvider

class MockLLMOrchestrator(BaseLLMOrchestrator):
    """
    Decoupled LLM Orchestrator that routes tasks to different providers.
    """
    def __init__(self):
        self._openai = OpenAIProvider()
        self._anthropic = AnthropicProvider()

    async def route_and_optimize(self, task_description: str, domain: str, context: Dict[str, Any]) -> Tuple[OrchestratedPrompt, List[TraceLog]]:
        start_time = time.time()

        # Decide between Claude (Anthropic) or ChatGPT (OpenAI) based on task description keywords
        is_design = any(word in task_description.lower() for word in ["diseñar", "architect", "investigar", "redactar", "verificar"])

        if is_design:
            model_name = "claude-3-opus-20240229"
            system_prompt = f"Eres un Agente Experto de Claude optimizado para {domain}. Tu fortaleza es el diseño conceptual y análisis profundo."
        else:
            model_name = "gpt-4-turbo-preview"
            system_prompt = f"Eres un Agente Experto de ChatGPT optimizado para {domain}. Tu fortaleza es la ejecución técnica precisa y eficiente."

        orchestrated_prompt = OrchestratedPrompt(
            model_name=model_name,
            system_prompt=system_prompt,
            user_prompt=f"Por favor ejecuta la siguiente tarea considerando el contexto:\nTarea: {task_description}\nContexto: {str(context)}"
        )

        latency = (time.time() - start_time) * 1000
        trace = TraceLog(
            step_name="OrchestratorRouteAndOptimize",
            latency_ms=latency,
            token_count=150,
            cost_usd=0.00030,
            quality_score=0.97,
            metadata={"selected_model": model_name}
        )

        return orchestrated_prompt, [trace]

    async def call_model(self, orchestrated_prompt: OrchestratedPrompt) -> Tuple[str, List[TraceLog]]:
        start_time = time.time()

        # Route execution dynamically to the correct provider
        if "claude" in orchestrated_prompt.model_name.lower():
            output, tokens, cost = await self._anthropic.generate_response(orchestrated_prompt)
        else:
            output, tokens, cost = await self._openai.generate_response(orchestrated_prompt)

        latency = (time.time() - start_time) * 1000
        trace = TraceLog(
            step_name="LLMModelCall",
            latency_ms=latency,
            token_count=tokens,
            cost_usd=cost,
            quality_score=0.94,
            metadata={"model": orchestrated_prompt.model_name}
        )

        return output, [trace]
