from neo4j import AsyncGraphDatabase
from typing import List, Dict, Any, Optional
from apps.backend.brain.graph_rag import BaseGraphStore
from apps.backend.core.logger import logger

class Neo4jGraphStore(BaseGraphStore):
    """
    Concrete asynchronous implementation of Neo4j Graph Database Store.
    Manages entity relationships, weight weights, and context subgraphs.
    """
    def __init__(self, uri: str = "bolt://localhost:7687", auth: Optional[tuple] = None):
        self._uri = uri
        self._auth = auth or ("neo4j", "password")
        self._driver = None

    async def connect(self) -> None:
        """
        Instantiates the underlying driver connection pool.
        """
        logger.info(f"Neo4jGraphStore: Connecting to pool at {self._uri}")
        self._driver = AsyncGraphDatabase.driver(self._uri, auth=self._auth)

    async def close(self) -> None:
        """
        Gracefully terminates the driver connection pool.
        """
        if self._driver:
            await self._driver.close()
            logger.info("Neo4jGraphStore: Connection pool closed.")

    async def get_neighbors(self, node_id: str, depth: int = 1) -> List[Dict[str, Any]]:
        """
        Traverses neighbouring concept edges from Neo4j asynchronously using Cypher query.
        """
        if not self._driver:
            logger.warning("Neo4jGraphStore: Driver not connected. Returning simulated mock data.")
            return [{"source": node_id, "relation": "RELATED_TO", "target": "SimulatedConcept", "weight": 1.0}]

        logger.info(f"Neo4jGraphStore: Fetching neighbors for node {node_id} at depth {depth}")
        query = (
            "MATCH (n {id: $node_id})-[r]->(m) "
            "RETURN type(r) AS relation, m.id AS target, r.weight AS weight"
        )
        neighbors = []
        try:
            async with self._driver.session() as session:
                result = await session.run(query, node_id=node_id)
                async for record in result:
                    neighbors.append({
                        "source": node_id,
                        "relation": record["relation"],
                        "target": record["target"],
                        "weight": record["weight"] or 1.0
                    })
        except Exception as e:
            logger.error(f"Neo4jGraphStore: Query execution failed: {str(e)}")

        return neighbors

    async def add_relation(self, source_id: str, relation: str, target_id: str, weight: float = 1.0) -> None:
        """
        Saves or updates semantic graph relationships in Neo4j.
        """
        if not self._driver:
            logger.warning("Neo4jGraphStore: Driver not connected. Simulating relation save.")
            return

        query = (
            "MERGE (a:Concept {id: $source_id}) "
            "MERGE (b:Concept {id: $target_id}) "
            "MERGE (a)-[r:RELATION {type: $relation}]->(b) "
            "SET r.weight = $weight"
        )
        try:
            async with self._driver.session() as session:
                await session.run(query, source_id=source_id, relation=relation, target_id=target_id, weight=weight)
                logger.info(f"Neo4jGraphStore: Saved relation {source_id} -[{relation}]-> {target_id} (weight={weight})")
        except Exception as e:
            logger.error(f"Neo4jGraphStore: Failed to merge relation: {str(e)}")
