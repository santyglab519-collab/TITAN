from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# --- Observabilidad (Observability) ---
class TraceLog(BaseModel):
    step_name: str
    latency_ms: float
    token_count: Optional[int] = 0
    cost_usd: Optional[float] = 0.0
    quality_score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionTelemetry(BaseModel):
    session_id: str
    total_latency_ms: float = 0.0
    total_cost_usd: float = 0.0
    traces: List[TraceLog] = Field(default_factory=list)


# --- Cognitive Engine & Input Comprehension ---
class UserRequest(BaseModel):
    user_id: str
    session_id: str
    text_prompt: str


class ClarificationQuestions(BaseModel):
    needed: bool
    questions: List[str] = Field(default_factory=list)


class ComprehensionResult(BaseModel):
    intent: str
    implicit_goals: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    clarification: ClarificationQuestions
    domain_classified: str


# --- Planner ---
class TaskNode(BaseModel):
    task_id: str
    agent_role: str
    description: str
    dependencies: List[str] = Field(default_factory=list)
    status: str = "pending"  # pending, running, completed, failed


class Plan(BaseModel):
    plan_id: str
    tasks: List[TaskNode] = Field(default_factory=list)


# --- Memory ---
class MemoryQuery(BaseModel):
    session_id: str
    query_text: str
    limit: int = 5


class MemoryNode(BaseModel):
    node_id: str
    concept: str
    weight: float = 1.0
    relations: List[Dict[str, Any]] = Field(default_factory=list)


# --- LLM Orchestration ---
class OrchestratedPrompt(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_name: str  # e.g. "gpt-4-turbo", "claude-3-opus"
    system_prompt: str
    user_prompt: str


# --- Verifier ---
class VerificationResult(BaseModel):
    is_valid: bool
    completeness_score: float = Field(
        ...,
        description="Score from 0.0 to 1.0 representing completeness of requirements",
    )
    consistency_score: float = Field(
        ...,
        description="Score from 0.0 to 1.0 representing architectural/code consistency",
    )
    accuracy_score: float = Field(
        ...,
        description="Score from 0.0 to 1.0 representing factual accuracy / no hallucination",
    )
    confidence_score: float = Field(
        ..., description="Overall confidence score (computed or aggregated)"
    )
    feedback: str


# --- API Response ---
class UserResponse(BaseModel):
    session_id: str
    status: str  # "clarification_needed", "completed", "requires_correction"
    comprehension: ComprehensionResult
    plan: Optional[Plan] = None
    output: Optional[str] = None
    verification: Optional[VerificationResult] = None
    telemetry: ExecutionTelemetry
