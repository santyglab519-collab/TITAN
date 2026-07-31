# ADR-004: Implementación de Capacidades Cognitivas Reales y GraphRAG de Producción para la Fase 4 (TITÁN)

## Estado
Propuesto (Esperando Aprobación de Arquitectura por el Usuario/CTO)

## Contexto y Requisitos
Con la Fase 3 completada, el **PROYECTO TITÁN** ha madurado su capa de API HTTP, desacoplado su PipelineOrchestrator de la capa web, e implementado de forma segura la autenticación por JSON Web Tokens (JWT). En la **Fase 4**, nos enfocamos en habilitar el primer ciclo operativo con inteligencia artificial real y persistencia semántica híbrida (GraphRAG):

Los objetivos clave de la Fase 4 son:
1. **Sustituir Mocks por Clientes Reales:** Conectar clientes reales de OpenAI y Anthropic mediante sus SDKs oficiales.
2. **Integrar Bases de Datos Cognitivas Reales:** Reemplazar las abstracciones simuladas de GraphRAG por clientes de producción con **Neo4j** (asíncrono) y **Qdrant** (búsquedas vectoriales densas).
3. **Establecer Políticas de Memoria (Corto y Largo Plazo):** Implementar estrategias para consolidar recuerdos de proyectos y expirar memorias temporales redundantes.
4. **Construir el Ciclo Cognitivo Real:** Ejecutar el primer ciclo completo de planificación, ejecución, verificación y persistencia utilizando llamadas reales a LLMs.
5. **Observabilidad Distribuida (OpenTelemetry):** Diseñar la estructura de telemetría distribuida para trazar latencia y coste entre microservicios de agentes.

---

## Decisiones de Arquitectura

### 1. Integración de Motores de Persistencia Cognitiva Real
*   **Neo4j (`apps/backend/brain/neo4j_store.py`):** Utilizaremos el driver oficial `neo4j` para establecer conexiones asíncronas con instancias en producción, indexando entidades mediante consultas Cypher parametrizadas.
*   **Qdrant (`apps/backend/brain/qdrant_store.py`):** Usaremos el cliente oficial `qdrant-client` para gestionar colecciones de vectores, persistiendo embeddings generados semánticamente.

### 2. Memoria de Corto y Largo Plazo
*   **Memoria de Corto Plazo:** Almacenada en Redis con políticas de expiración (TTL) estrictas de sesión para retener el contexto inmediato de la conversación actual.
*   **Memoria de Largo Plazo (Consolidación):** Al expirar una sesión, un agente de consolidación extraerá las decisiones clave del proyecto, las convertirá en embeddings y nodos de grafos, y las persistirá permanentemente en Neo4j y Qdrant.

### 3. OpenTelemetry para Observabilidad Distribuida
*   Integraremos instrumentación de OpenTelemetry en `apps/backend/core/telemetry.py` para generar trazas (`traces`) unificadas por cada agente en ejecución, permitiendo que Grafana Tempo visualice de manera transparente los cuellos de botella y costos por cada paso.

### 4. Evaluación Continua de Calidad (Verifier de Producción)
*   El Verifier ejecutará prompts de evaluación cuantitativa usando un LLM especializado (ej. Claude) para puntuar objetivamente tres dimensiones de calidad: Compleción (0.0-1.0), Consistencia (0.0-1.0) y Riesgo de Alucinación (0.0-1.0), calculando un puntaje de confianza consolidado antes de autorizar la entrega al usuario.

---

## Conclusión
Este diseño de arquitectura para la Fase 4 dota a TITÁN de capacidades de inteligencia reales e infraestructura híbrida de GraphRAG que garantizan un sistema operativo cognitivo potente y resiliente.
