from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseGraphStore(ABC):
    """
    Abstract interface for Knowledge Graph Store (e.g. Neo4j).
    Responsible for managing conceptual nodes, entity relations, weights, and decisions.
    """
    @abstractmethod
    async def get_neighbors(self, node_id: str, depth: int = 1) -> List[Dict[str, Any]]:
        """
        Retrieves neighbouring nodes up to N steps deep.
        """
        pass

    @abstractmethod
    async def add_relation(self, source_id: str, relation: str, target_id: str, weight: float = 1.0) -> None:
        """
        Registers a new semantic edge with weights between entities.
        """
        pass


class BaseVectorStore(ABC):
    """
    Abstract interface for Semantic Vector Store (e.g. Qdrant).
    Responsible for fast indexing, search of prompt memory embeds, and context generation.
    """
    @abstractmethod
    async def search_similarity(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Executes dense vector similarity matching on registered memories.
        """
        pass

    @abstractmethod
    async def upsert_vector(self, document_id: str, text: str, vector: List[float], metadata: Dict[str, Any]) -> None:
        """
        Registers/updates raw text embeddings within Qdrant.
        """
        pass


class GraphRAGOrchestrator:
    """
    Combines Vector semantic search and Knowledge Graph relation traversals
    to reconstruct context-aware subgraphs for multi-agent execution.
    """
    def __init__(self, graph_store: BaseGraphStore, vector_store: BaseVectorStore):
        self.graph = graph_store
        self.vector = vector_store

    async def build_optimal_context(self, prompt: str, limit: int = 5) -> Dict[str, Any]:
        """
        First matches semantic concepts via similarity search (Vector),
        then traverses local graph neighbors (Graph) to fetch entity weights and preferences.
        """
        # Simulated dense GraphRAG flow
        similar_docs = await self.vector.search_similarity(prompt, limit=limit)

        graph_contexts = []
        for doc in similar_docs:
            neighbors = await self.graph.get_neighbors(doc.get("id", ""), depth=1)
            graph_contexts.append({
                "concept": doc.get("text", ""),
                "relations": neighbors
            })

        return {
            "retrieved_memories": similar_docs,
            "subgraph_contexts": graph_contexts
        }
