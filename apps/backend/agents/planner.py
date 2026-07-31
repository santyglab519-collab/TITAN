import time
import uuid
from typing import Tuple, List, Dict, Any
from apps.backend.core.interfaces import BasePlanner
from apps.backend.core.schemas import Plan, TaskNode, ComprehensionResult, TraceLog

class MockPlanner(BasePlanner):
    """
    Mock Planner Agent for Phase 1.
    """
    async def create_plan(self, comprehension: ComprehensionResult, context: Dict[str, Any]) -> Tuple[Plan, List[TraceLog]]:
        start_time = time.time()

        plan_id = str(uuid.uuid4())

        # Generate tasks based on domain
        tasks = []
        if comprehension.domain_classified == "videojuegos":
            tasks = [
                TaskNode(task_id="task_1", agent_role="Designer", description="Diseñar mecánicas y dinámicas del juego"),
                TaskNode(task_id="task_2", agent_role="Programmer", description="Escribir lógica y bucle principal de juego", dependencies=["task_1"]),
                TaskNode(task_id="task_3", agent_role="Verifier", description="Validar código y mecánicas", dependencies=["task_2"])
            ]
        elif comprehension.domain_classified == "desarrollo_software":
            tasks = [
                TaskNode(task_id="task_1", agent_role="Architect", description="Diseñar arquitectura de componentes y base de datos"),
                TaskNode(task_id="task_2", agent_role="Programmer", description="Implementar controladores y rutas API", dependencies=["task_1"]),
                TaskNode(task_id="task_3", agent_role="Verifier", description="Verificar cobertura de pruebas y calidad", dependencies=["task_2"])
            ]
        else:
            tasks = [
                TaskNode(task_id="task_1", agent_role="Investigator", description="Investigar y recopilar información clave"),
                TaskNode(task_id="task_2", agent_role="Writer", description="Redactar borrador del documento", dependencies=["task_1"]),
                TaskNode(task_id="task_3", agent_role="Verifier", description="Verificar precisión y coherencia", dependencies=["task_2"])
            ]

        result_plan = Plan(plan_id=plan_id, tasks=tasks)

        latency = (time.time() - start_time) * 1000
        trace = TraceLog(
            step_name="PlannerAgent",
            latency_ms=latency,
            token_count=180,
            cost_usd=0.00036,
            quality_score=0.92,
            metadata={"tasks_count": len(tasks)}
        )

        return result_plan, [trace]
