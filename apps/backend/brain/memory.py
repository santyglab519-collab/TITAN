import time
from typing import Any, List, Tuple

from apps.backend.core.interfaces import BaseMemorySystem
from apps.backend.core.schemas import MemoryNode, TraceLog


class MockMemorySystem(BaseMemorySystem):
    """
    Mock Memory System for Phase 1.
    """

    def __init__(self):
        self._store = {}

    async def query_relevant_nodes(
        self, query: str, limit: int = 5
    ) -> Tuple[List[MemoryNode], List[TraceLog]]:
        start_time = time.time()

        # Simulate returning relevant subgraphs based on search terms
        nodes = []
        lowered = query.lower()

        if "videojuego" in lowered or "game" in lowered:
            nodes = [
                MemoryNode(
                    node_id="mem_1",
                    concept="Preferencia de Motor de Videojuegos",
                    weight=0.9,
                    relations=[{"relation": "PREFERS", "target": "Godot/Unity"}],
                ),
                MemoryNode(
                    node_id="mem_2",
                    concept="Historial de Decisiones",
                    weight=0.8,
                    relations=[
                        {
                            "relation": "DECIDED",
                            "target": "Usar Python para prototipado rápido",
                        }
                    ],
                ),
            ]
        elif "app" in lowered or "web" in lowered:
            nodes = [
                MemoryNode(
                    node_id="mem_3",
                    concept="Arquitectura Web Favorita",
                    weight=0.95,
                    relations=[
                        {"relation": "PREFERS", "target": "Next.js con FastAPI"}
                    ],
                ),
                MemoryNode(
                    node_id="mem_4",
                    concept="Estilo UI",
                    weight=0.85,
                    relations=[
                        {
                            "relation": "PREFERS",
                            "target": "Tailwind Minimalista y Moderno",
                        }
                    ],
                ),
            ]
        else:
            nodes = [
                MemoryNode(
                    node_id="mem_5",
                    concept="Preferencia General",
                    weight=0.7,
                    relations=[
                        {
                            "relation": "PREFERS",
                            "target": "Explicaciones claras y directas",
                        }
                    ],
                )
            ]

        latency = (time.time() - start_time) * 1000
        trace = TraceLog(
            step_name="MemorySystemQuery",
            latency_ms=latency,
            token_count=80,
            cost_usd=0.00016,
            quality_score=0.99,
            metadata={"nodes_returned": len(nodes)},
        )

        return nodes[:limit], [trace]

    async def save_interaction(self, key: str, value: Any) -> None:
        self._store[key] = value
