import time
from typing import Dict, Any, Optional
from apps.backend.core.logger import logger

class AgentSpan:
    """
    Simulated OpenTelemetry trace span representing execution lifetime,
    latency, and resources of an active agent.
    """
    def __init__(self, agent_role: str, operation_name: str):
        self.agent_role = agent_role
        self.operation_name = operation_name
        self.start_time = 0.0
        self.end_time = 0.0

    def __enter__(self):
        self.start_time = time.time()
        logger.info(f"Telemetry Span Start: [Role: {self.agent_role}] [Op: {self.operation_name}]")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        latency_ms = (self.end_time - self.start_time) * 1000

        status = "SUCCESS" if exc_type is None else "FAILED"
        logger.info(
            f"Telemetry Span End: [Role: {self.agent_role}] [Op: {self.operation_name}] "
            f"[Status: {status}] [Latency: {latency_ms:.2f}ms]"
        )

def trace_agent(agent_role: str, operation_name: str) -> AgentSpan:
    """
    Factory helper to instantiate a tracing span context manager for an agent.
    """
    return AgentSpan(agent_role=agent_role, operation_name=operation_name)
