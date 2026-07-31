# ADR-003: Capacidades Cognitivas, Persistencia Avanzada y Orquestación para la Fase 3 (TITÁN)

## Estado
Propuesto (Esperando Aprobación de Arquitectura por el Usuario/CTO)

## Contexto y Requisitos
Con la Fase 1 y Fase 2 concluidas, el **PROYECTO TITÁN** cuenta con una base de API asíncrona, trazabilidad mediante Correlation IDs, persistencia en Postgres y observabilidad integrada. En la **Fase 3**, procedemos a sustituir los componentes de simulación (mocks) por implementaciones funcionales reales e integrar servicios avanzados de persistencia y cognición de IA:

Los objetivos clave de la Fase 3 son:
1. **Desacoplar la Orquestación de la API:** Evitar que `main.py` acumule lógica de negocio extrayendo el flujo a un servicio especializado `PipelineOrchestrator`.
2. **Autenticación Segura:** Implementar flujos JWT (JSON Web Tokens) para dar soporte multiusuario.
3. **Proveedores de LLM Reales:** Conectar los clientes de OpenAI y Anthropic mediante sus SDKs oficiales de forma robusta con fallback.
4. **Caché y Mensajería Rápida con Redis:** Configurar soporte para colas en segundo plano, control de sesiones de baja latencia y caché de prompts redundantes.
5. **Capa GraphRAG Inicial:** Definir interfaces e integraciones con **Neo4j** (grafo de conocimiento de entidades) y **Qdrant** (búsquedas de embeddings vectoriales).
6. **Estrategia de Versionado de API:** Configurar de manera estricta prefijos de ruta (ej. `/api/v1/...`) para permitir actualizaciones futuras sin afectar a clientes antiguos.

---

## Decisiones de Arquitectura

### 1. Refactorización a `PipelineOrchestrator`
*   **Problema:** `main.py` concentraba la lógica secuencial de comprensión, planificación, recuperación, llamada a LLM, verificación y persistencia.
*   **Solución:** Extraer la orquestación del pipeline a `apps/backend/core/pipeline.py`. El archivo `main.py` solo actuará como ruteador HTTP delgado que delega al orquestador.

### 2. Autenticación y Autorización Basada en JWT
*   Implementaremos hashing seguro con `passlib` o `cryptography` y generación de tokens de acceso firmados con JWT (`PyJWT` o `jose`).
*   Los endpoints sensibles requerirán la inyección del token del portador (`Bearer Token`), aislando los recursos personales de cada usuario.

### 3. Clientes LLM Oficiales y Manejo de Errores
*   Integraremos los SDKs de `openai` y `anthropic`.
*   Añadiremos interceptores de reintentos y lógica de contingencia (failover): si el modelo preferido (ej. Claude) falla o excede el límite de cuotas, el orquestador puede degradarse con gracia a un modelo secundario (ej. GPT-4o) para no interrumpir el flujo.

### 4. Memoria Híbrida y Semántica (GraphRAG con Neo4j + Qdrant)
*   La lógica de recuperación selectiva de memoria combinará la búsqueda de similitud de vectores en Qdrant (para recuerdos contextuales de texto libre) con las relaciones estructuradas de Neo4j (para proyectos, preferencias explícitas e historial de decisiones), entregando un contexto óptimo al LLM.

### 5. Integración de Redis para Sesiones y Tareas en Segundo Plano
*   Utilizaremos Redis como almacén clave-valor para controlar estados de sesión activos y cachear prompts generados redundantes para reducir costos y latencias de tokens.
*   Soportará la integración futura con colas de tareas asíncronas para operaciones pesadas de agentes.

---

## Conclusión
Esta especificación de diseño para la Fase 3 eleva a TITÁN de un esqueleto local a un sistema de producción multiusuario totalmente conectado con servicios reales de IA y almacenamiento cognitivo.
