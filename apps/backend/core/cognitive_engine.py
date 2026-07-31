import time
from typing import List, Tuple

from apps.backend.core.interfaces import BaseCognitiveEngine
from apps.backend.core.schemas import (
    ClarificationQuestions,
    ComprehensionResult,
    TraceLog,
)


class MockCognitiveEngine(BaseCognitiveEngine):
    """
    Mock implementation of Cognitive Engine for Phase 1 verification.
    """

    async def comprehend(
        self, user_prompt: str
    ) -> Tuple[ComprehensionResult, List[TraceLog]]:
        start_time = time.time()

        # Simple heuristic to simulate comprehension logic
        lowered = user_prompt.lower()
        if "videojuego" in lowered or "game" in lowered:
            domain = "videojuegos"
        elif "app" in lowered or "web" in lowered or "desarrollar" in lowered:
            domain = "desarrollo_software"
        elif "matematica" in lowered or "calcula" in lowered:
            domain = "matematicas"
        else:
            domain = "general"

        # Check if we are missing information (e.g. if the user says "crear una app" without details)
        missing_info = []
        needed_questions = []
        needed = False

        if len(user_prompt.strip()) < 15:
            missing_info.append("La solicitud es demasiado corta o ambigua.")
            needed_questions.append(
                "¿Podrías proporcionar más detalles sobre las funcionalidades deseadas?"
            )
            needed = True

        result = ComprehensionResult(
            intent="create_project",
            implicit_goals=[
                "Organizar estructura de archivos",
                "Garantizar escalabilidad y testing",
            ],
            missing_information=missing_info,
            clarification=ClarificationQuestions(
                needed=needed, questions=needed_questions
            ),
            domain_classified=domain,
        )

        latency = (time.time() - start_time) * 1000
        trace = TraceLog(
            step_name="CognitiveComprehension",
            latency_ms=latency,
            token_count=120,
            cost_usd=0.00024,
            quality_score=0.95,
            metadata={"domain_detected": domain},
        )

        return result, [trace]
