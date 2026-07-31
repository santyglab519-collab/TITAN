from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import time
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from contextlib import asynccontextmanager

from apps.backend.core.schemas import UserRequest, UserResponse, ExecutionTelemetry, TraceLog
from apps.backend.core.cognitive_engine import MockCognitiveEngine
from apps.backend.agents.planner import MockPlanner
from apps.backend.agents.verifier import MockVerifier
from apps.backend.brain.memory import MockMemorySystem
from apps.backend.orchestrator.llm_orchestrator import MockLLMOrchestrator
from apps.backend.core.config import settings
from apps.backend.core.logger import CorrelationIdMiddleware, logger
from apps.backend.core.metrics import setup_metrics
from apps.backend.brain.database import get_db, Base, engine, ProjectModel, TaskModel

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager replacing deprecated startup/shutdown events.
    Ensures database schemas are created automatically on startup.
    """
    logger.info("Initializing database schemas...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schemas initialized successfully!")
    except Exception as e:
        logger.error(f"Failed to automatically initialize database schemas: {str(e)}")

    yield  # Runs the application

app = FastAPI(
    title=settings.app_name,
    description="The modular, scalable central API for the TITÁN Personal AI Operating System.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enable Correlation ID Middleware for request tracing
app.add_middleware(CorrelationIdMiddleware)

# Initialize Prometheus instrumentation and /metrics route
setup_metrics(app)

# Instantiate mock modules
cognitive_engine = MockCognitiveEngine()
planner = MockPlanner()
verifier = MockVerifier()
memory_system = MockMemorySystem()
llm_orchestrator = MockLLMOrchestrator()

@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": "1.0.0",
        "message": "Welcome to your Personal AI Operating System Cerebro."
    }

@app.post("/api/v1/process", response_model=UserResponse)
async def process_request(request: UserRequest, db: AsyncSession = Depends(get_db)):
    """
    Main entry point for TITÁN Pipeline.
    """
    session_id = request.session_id or str(uuid.uuid4())
    logger.info(f"Starting pipeline processing for session {session_id}")
    start_time = time.time()
    telemetry_traces: List[TraceLog] = []

    # 1. Comprehend request and detect missing info / goals
    logger.info("Running Input Comprehension Engine")
    comprehension, comp_traces = await cognitive_engine.comprehend(request.text_prompt)
    telemetry_traces.extend(comp_traces)

    # Create/save Project record in DB for traceability
    project_id = str(uuid.uuid4())
    db_project = ProjectModel(
        id=project_id,
        user_id=request.user_id,
        session_id=session_id,
        intent=comprehension.intent,
        domain_classified=comprehension.domain_classified,
        status="pending"
    )

    # If clarification is needed, we return immediately to request user feedback (1-step clarification)
    if comprehension.clarification.needed:
        logger.warning(f"Clarification needed for session {session_id}")
        db_project.status = "clarification_needed"
        try:
            db.add(db_project)
            await db.commit()
        except Exception as e:
            logger.error(f"Error persisting project for clarification: {str(e)}")

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
    logger.info("Querying Memory systems (GraphRAG)")
    memory_nodes, mem_traces = await memory_system.query_relevant_nodes(request.text_prompt)
    telemetry_traces.extend(mem_traces)

    # 3. Create Plan
    logger.info("Generating Execution Plan")
    plan, plan_traces = await planner.create_plan(comprehension, {"memory_context": memory_nodes})
    telemetry_traces.extend(plan_traces)

    # Persist Project and Task definitions to DB
    try:
        db_project.status = "running"
        db.add(db_project)

        for task in plan.tasks:
            db_task = TaskModel(
                id=task.task_id,
                project_id=project_id,
                agent_role=task.agent_role,
                description=task.description,
                dependencies=task.dependencies,
                status="pending"
            )
            db.add(db_task)
        await db.commit()
    except Exception as e:
        logger.error(f"Error persisting project and initial tasks: {str(e)}")

    # 4. Orchestrate & Execute (Iterative execution over tasks in the plan)
    task_outputs = []
    for task in plan.tasks:
        logger.info(f"Orchestrating task {task.task_id}: {task.description}")
        db_task: Optional[TaskModel] = None

        # Update task status to running in DB
        try:
            db_task_query = await db.execute(select(TaskModel).filter_by(id=task.task_id))
            db_task = db_task_query.scalars().first()
            if db_task:
                db_task.status = "running"
                await db.commit()
        except Exception as e:
            logger.error(f"Error updating task status to running: {str(e)}")

        # Route to optimal LLM + Prompt Engineering
        orchestrated_prompt, orch_traces = await llm_orchestrator.route_and_optimize(
            task_description=task.description,
            domain=comprehension.domain_classified,
            context={"memory": memory_nodes, "completed_tasks": task_outputs}
        )
        telemetry_traces.extend(orch_traces)

        # Call model
        logger.info(f"Calling LLM provider model {orchestrated_prompt.model_name}")
        output, call_traces = await llm_orchestrator.call_model(orchestrated_prompt)
        telemetry_traces.extend(call_traces)

        task.status = "completed"
        task_outputs.append({
            "task_id": task.task_id,
            "description": task.description,
            "output": output
        })

        # Update task status to completed and persist generated output in DB
        try:
            if db_task:
                db_task.status = "completed"
                db_task.output = output
                await db.commit()
        except Exception as e:
            logger.error(f"Error persisting task output: {str(e)}")

    # 5. Integrate & Verify
    logger.info("Integrating task outputs and initiating quality verification")
    integrated_output = "\n\n".join([f"--- {t['description']} ---\n{t['output']}" for t in task_outputs])
    requirements = [f"Cumplir {task.description}" for task in plan.tasks]

    verification, ver_traces = await verifier.verify(integrated_output, requirements)
    telemetry_traces.extend(ver_traces)

    # Save final status to Project model
    try:
        final_status = "completed" if verification.is_valid else "requires_correction"
        db_project.status = final_status
        await db.commit()
    except Exception as e:
        logger.error(f"Error updating project final status: {str(e)}")

    total_latency = (time.time() - start_time) * 1000
    telemetry = ExecutionTelemetry(
        session_id=session_id,
        total_latency_ms=total_latency,
        total_cost_usd=sum(t.cost_usd or 0.0 for t in telemetry_traces),
        traces=telemetry_traces
    )

    logger.info(f"Finished pipeline processing for session {session_id} with status: {verification.is_valid}")
    return UserResponse(
        session_id=session_id,
        status="completed" if verification.is_valid else "requires_correction",
        comprehension=comprehension,
        plan=plan,
        output=integrated_output,
        verification=verification,
        telemetry=telemetry
    )
