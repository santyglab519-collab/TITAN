import time
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from apps.backend.agents.planner import MockPlanner
from apps.backend.agents.verifier import MockVerifier
from apps.backend.brain.database import ProjectModel, TaskModel
from apps.backend.brain.memory import MockMemorySystem
from apps.backend.core.cognitive_engine import MockCognitiveEngine
from apps.backend.core.logger import logger
from apps.backend.core.schemas import (
    ExecutionTelemetry,
    TraceLog,
    UserRequest,
    UserResponse,
)
from apps.backend.orchestrator.llm_orchestrator import MockLLMOrchestrator


class PipelineOrchestrator:
    """
    Dedicated orchestrator service that coordinates the entire cognitive multi-agent pipeline.
    Prevents main.py from accumulating business logic or becoming bloated.
    """

    def __init__(self):
        self.cognitive_engine = MockCognitiveEngine()
        self.planner = MockPlanner()
        self.verifier = MockVerifier()
        self.memory_system = MockMemorySystem()
        self.llm_orchestrator = MockLLMOrchestrator()

    async def process(self, request: UserRequest, db: AsyncSession) -> UserResponse:
        session_id = request.session_id or str(uuid.uuid4())
        logger.info(
            f"Orchestrator: Starting pipeline processing for session {session_id}"
        )
        start_time = time.time()
        telemetry_traces: List[TraceLog] = []

        # 1. Comprehend request and detect missing info / goals
        logger.info("Orchestrator: Running Input Comprehension Engine")
        comprehension, comp_traces = await self.cognitive_engine.comprehend(
            request.text_prompt
        )
        telemetry_traces.extend(comp_traces)

        # Create/save Project record in DB for traceability
        project_id = str(uuid.uuid4())
        db_project = ProjectModel(
            id=project_id,
            user_id=request.user_id,
            session_id=session_id,
            intent=comprehension.intent,
            domain_classified=comprehension.domain_classified,
            status="pending",
        )

        # If clarification is needed, we return immediately to request user feedback (1-step clarification)
        if comprehension.clarification.needed:
            logger.warning(
                f"Orchestrator: Clarification needed for session {session_id}"
            )
            db_project.status = "clarification_needed"
            try:
                db.add(db_project)
                await db.commit()
            except Exception as e:
                logger.error(
                    f"Orchestrator Error persisting project for clarification: {str(e)}"
                )

            total_latency = (time.time() - start_time) * 1000
            telemetry = ExecutionTelemetry(
                session_id=session_id,
                total_latency_ms=total_latency,
                total_cost_usd=sum(t.cost_usd or 0.0 for t in telemetry_traces),
                traces=telemetry_traces,
            )
            return UserResponse(
                session_id=session_id,
                status="clarification_needed",
                comprehension=comprehension,
                telemetry=telemetry,
                plan=None,
                verification=None,
                output=None,
            )

        # 2. Query Memory selectively (GraphRAG)
        logger.info("Orchestrator: Querying Memory systems (GraphRAG)")
        memory_nodes, mem_traces = await self.memory_system.query_relevant_nodes(
            request.text_prompt
        )
        telemetry_traces.extend(mem_traces)

        # 3. Create Plan
        logger.info("Orchestrator: Generating Execution Plan")
        plan, plan_traces = await self.planner.create_plan(
            comprehension, {"memory_context": memory_nodes}
        )
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
                    status="pending",
                )
                db.add(db_task)
            await db.commit()
        except Exception as e:
            logger.error(
                f"Orchestrator Error persisting project and initial tasks: {str(e)}"
            )

        # 4. Orchestrate & Execute (Iterative execution over tasks in the plan)
        task_outputs: List[Dict[str, Any]] = []
        for task in plan.tasks:
            logger.info(
                f"Orchestrator: Executing task {task.task_id}: {task.description}"
            )
            db_task_model: Optional[TaskModel] = None

            # Update task status to running in DB
            try:
                db_task_query = await db.execute(
                    select(TaskModel).filter_by(id=task.task_id)
                )
                db_task_model = db_task_query.scalars().first()
                if db_task_model:
                    db_task_model.status = "running"
                    await db.commit()
            except Exception as e:
                logger.error(
                    f"Orchestrator Error updating task status to running: {str(e)}"
                )

            # Route to optimal LLM + Prompt Engineering
            orchestrated_prompt, orch_traces = (
                await self.llm_orchestrator.route_and_optimize(
                    task_description=task.description,
                    domain=comprehension.domain_classified,
                    context={"memory": memory_nodes, "completed_tasks": task_outputs},
                )
            )
            telemetry_traces.extend(orch_traces)

            # Call model
            logger.info(
                f"Orchestrator: Calling LLM provider model {orchestrated_prompt.model_name}"
            )
            output, call_traces = await self.llm_orchestrator.call_model(
                orchestrated_prompt
            )
            telemetry_traces.extend(call_traces)

            task.status = "completed"
            task_outputs.append(
                {
                    "task_id": task.task_id,
                    "description": task.description,
                    "output": output,
                }
            )

            # Update task status to completed and persist generated output in DB
            try:
                if db_task_model:
                    db_task_model.status = "completed"
                    db_task_model.output = output
                    await db.commit()
            except Exception as e:
                logger.error(f"Orchestrator Error persisting task output: {str(e)}")

        # 5. Integrate & Verify
        logger.info(
            "Orchestrator: Integrating task outputs and initiating quality verification"
        )
        integrated_output = "\n\n".join(
            [f"--- {t['description']} ---\n{t['output']}" for t in task_outputs]
        )
        requirements = [f"Cumplir {task.description}" for task in plan.tasks]

        verification, ver_traces = await self.verifier.verify(
            integrated_output, requirements
        )
        telemetry_traces.extend(ver_traces)

        # Save final status to Project model
        try:
            final_status = (
                "completed" if verification.is_valid else "requires_correction"
            )
            db_project.status = final_status
            await db.commit()
        except Exception as e:
            logger.error(f"Orchestrator Error updating project final status: {str(e)}")

        total_latency = (time.time() - start_time) * 1000
        telemetry = ExecutionTelemetry(
            session_id=session_id,
            total_latency_ms=total_latency,
            total_cost_usd=sum(t.cost_usd or 0.0 for t in telemetry_traces),
            traces=telemetry_traces,
        )

        logger.info(
            f"Orchestrator: Finished pipeline processing for session {session_id} with status: {verification.is_valid}"
        )
        return UserResponse(
            session_id=session_id,
            status="completed" if verification.is_valid else "requires_correction",
            comprehension=comprehension,
            plan=plan,
            output=integrated_output,
            verification=verification,
            telemetry=telemetry,
        )
