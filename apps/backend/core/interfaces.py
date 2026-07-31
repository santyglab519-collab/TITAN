from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

from apps.backend.core.schemas import (
    ComprehensionResult,
    MemoryNode,
    OrchestratedPrompt,
    Plan,
    TraceLog,
    VerificationResult,
)


class BaseAgent(ABC):
    """
    Abstract Base Class for all TITAN Agents.
    """

    @property
    @abstractmethod
    def role(self) -> str:
        pass

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the agent logic given a context and returns updated context.
        """
        pass


class BaseCognitiveEngine(ABC):
    """
    Interface for the Cognitive Engine responsible for raw understanding,
    domain classification, and extracting implicit goals or missing information.
    """

    @abstractmethod
    async def comprehend(
        self, user_prompt: str
    ) -> Tuple[ComprehensionResult, List[TraceLog]]:
        pass


class BasePlanner(ABC):
    """
    Interface for the Planner Agent that breaks down the user request into sequential/parallel tasks.
    """

    @abstractmethod
    async def create_plan(
        self, comprehension: ComprehensionResult, context: Dict[str, Any]
    ) -> Tuple[Plan, List[TraceLog]]:
        pass


class BaseMemorySystem(ABC):
    """
    Interface for multi-level memory system (temporal, permanent, projects, preferences).
    """

    @abstractmethod
    async def query_relevant_nodes(
        self, query: str, limit: int = 5
    ) -> Tuple[List[MemoryNode], List[TraceLog]]:
        pass

    @abstractmethod
    async def save_interaction(self, key: str, value: Any) -> None:
        pass


class BaseLLMOrchestrator(ABC):
    """
    Interface for routing the optimized queries to LLMs and performing Automatic Prompt Engineering.
    """

    @abstractmethod
    async def route_and_optimize(
        self, task_description: str, domain: str, context: Dict[str, Any]
    ) -> Tuple[OrchestratedPrompt, List[TraceLog]]:
        pass

    @abstractmethod
    async def call_model(
        self, orchestrated_prompt: OrchestratedPrompt
    ) -> Tuple[str, List[TraceLog]]:
        pass


class BaseVerifier(ABC):
    """
    Interface for Verifying output quality against completion, consistency, and accuracy scores.
    """

    @abstractmethod
    async def verify(
        self, task_output: Any, requirements: List[str]
    ) -> Tuple[VerificationResult, List[TraceLog]]:
        pass
