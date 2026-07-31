import time
from typing import Tuple, List, Dict, Any
from apps.backend.core.interfaces import BaseVerifier
from apps.backend.core.schemas import VerificationResult, TraceLog

class MockVerifier(BaseVerifier):
    """
    Mock Verifier Agent for Phase 1 that computes quality scores.
    """
    async def verify(self, task_output: Any, requirements: List[str]) -> Tuple[VerificationResult, List[TraceLog]]:
        start_time = time.time()

        # In a real implementation, we would call an LLM Verifier Agent with these metrics
        # Here we simulate with mock scores based on simple heuristics
        output_str = str(task_output).lower()

        completeness = 0.95
        consistency = 0.90
        accuracy = 0.92

        if len(output_str) < 10:
            completeness = 0.40
            consistency = 0.50
            accuracy = 0.60

        # Calculate consolidated confidence score
        confidence = (completeness + consistency + accuracy) / 3.0
        is_valid = confidence >= 0.85

        feedback = "El resultado cumple con los requisitos del sistema." if is_valid else "El resultado es demasiado corto y no cumple con los estándares mínimos de calidad."

        result = VerificationResult(
            is_valid=is_valid,
            completeness_score=completeness,
            consistency_score=consistency,
            accuracy_score=accuracy,
            confidence_score=confidence,
            feedback=feedback
        )

        latency = (time.time() - start_time) * 1000
        trace = TraceLog(
            step_name="VerifierAgent",
            latency_ms=latency,
            token_count=150,
            cost_usd=0.00030,
            quality_score=0.98,
            metadata={"is_valid": is_valid, "confidence": confidence}
        )

        return result, [trace]
