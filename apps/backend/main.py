from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import time
import uuid
from typing import List, Dict, Any, Optional

from apps.backend.core.schemas import UserRequest, UserResponse, ExecutionTelemetry, TraceLog
from apps.backend.core.cognitive_engine import MockCognitiveEngine
from apps.backend.agents.planner import MockPlanner
from apps.backend.agents.verifier import MockVerifier
from apps.backend.brain.memory import MockMemorySystem
from apps.backend.orchestrator.llm_orchestrator import MockLLMOrchestrator

app = FastAPI(
    title="TITÁN Core - API Gateway",
    description="The modular, scalable central API for the TITÁN Personal AI Operating System.",
    version="1.0.0"
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate mock modules
cognitive_engine = MockCognitiveEngine()
planner = MockPlanner()
verifier = MockVerifier()
memory_system = MockMemorySystem()
llm_orchestrator = MockLLMOrchestrator()

@app.get("/")
async def root():
    return {
        "status": "healthy",
        "service": "TITÁN Core",
        "version": "1.0.0",
        "message": "Welcome to your Personal AI Operating System Cerebro."
    }

@app.post("/api/v1/process", response_model=UserResponse)
async def process_request(request: UserRequest):
    """
    Main entry point for TITÁN Pipeline.
    """
    session_id = request.session_id or str(uuid.uuid4())
    start_time = time.time()
    telemetry_traces: List[TraceLog] = []

    # 1. Comprehend request and detect missing info / goals
    comprehension, comp_traces = await cognitive_engine.comprehend(request.text_prompt)
    telemetry_traces.extend(comp_traces)

    # If clarification is needed, we return immediately to request user feedback (1-step clarification)
    if comprehension.clarification.needed:
        total_latency = (time.time() - start_time) * 1000
        telemetry = ExecutionTelemetry(
            session_id=session_id,
            total_latency_ms=total_latency,
            total_cost_usd=sum(t.cost_usd or 0.0 for t in telemetry_traces),
            traces=telemetry_traces
        )
        return UserResponse(
            session_id=session_id,
            status="clarification_needed",
            comprehension=comprehension,
            telemetry=telemetry,
            plan=None,
            verification=None,
            output=None
        )

    # 2. Query Memory selectively (GraphRAG)
    memory_nodes, mem_traces = await memory_system.query_relevant_nodes(request.text_prompt)
    telemetry_traces.extend(mem_traces)

    # 3. Create Plan
    plan, plan_traces = await planner.create_plan(comprehension, {"memory_context": memory_nodes})
    telemetry_traces.extend(plan_traces)

    # 4. Orchestrate & Execute (Iterative execution over tasks in the plan)
    task_outputs = []
    for task in plan.tasks:
        # Route to optimal LLM + Prompt Engineering
        orchestrated_prompt, orch_traces = await llm_orchestrator.route_and_optimize(
            task_description=task.description,
            domain=comprehension.domain_classified,
            context={"memory": memory_nodes, "completed_tasks": task_outputs}
        )
        telemetry_traces.extend(orch_traces)

        # Call model
        output, call_traces = await llm_orchestrator.call_model(orchestrated_prompt)
        telemetry_traces.extend(call_traces)

        task.status = "completed"
        task_outputs.append({
            "task_id": task.task_id,
            "description": task.description,
            "output": output
        })

    # 5. Integrate & Verify
    integrated_output = "\n\n".join([f"--- {t['description']} ---\n{t['output']}" for t in task_outputs])
    requirements = [f"Cumplir {task.description}" for task in plan.tasks]

    verification, ver_traces = await verifier.verify(integrated_output, requirements)
    telemetry_traces.extend(ver_traces)

    total_latency = (time.time() - start_time) * 1000
    telemetry = ExecutionTelemetry(
        session_id=session_id,
        total_latency_ms=total_latency,
        total_cost_usd=sum(t.cost_usd or 0.0 for t in telemetry_traces),
        traces=telemetry_traces
    )

    return UserResponse(
        session_id=session_id,
        status="completed" if verification.is_valid else "requires_correction",
        comprehension=comprehension,
        plan=plan,
        output=integrated_output,
        verification=verification,
        telemetry=telemetry
    )
