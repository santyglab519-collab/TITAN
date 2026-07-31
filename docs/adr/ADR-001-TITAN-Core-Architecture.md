# ADR-001: Diseño de la Arquitectura de Referencia del Sistema Operativo Personal de Inteligencia Artificial (TITÁN)

## Estado
Aprobado con condiciones (Ajustes de simplificación de inicio, agentes incrementales, métricas del Verificador y Observabilidad desde el diseño inicial).

## Contexto y Objetivos de Negocio/Usuario
El usuario requiere la construcción de **TITÁN**, un sistema operativo personal de inteligencia artificial. No se trata de un chatbot tradicional, sino de una plataforma que piense, planifique, recuerde, aprenda, decida qué herramientas utilizar y coordine múltiples modelos de IA para resolver cualquier tipo de proyecto de forma autónoma.

### Principios Fundamentales (Actualizados según Feedback de CTO)
1. **Transparencia en el Modelo:** El usuario nunca debe preocuparse por qué IA utilizar. El sistema decidirá automáticamente de manera invisible para el usuario final (ChatGPT, Claude, etc.).
2. **El Cerebro Cognitivo (Grafo de Conocimiento):** Un sistema de memoria multinivel (permanente, por proyectos, temporal, preferencias de usuario, historial de decisiones, relaciones entre conceptos, sistema de pesos y aprendizaje continuo) que recupera únicamente subgrafos/nodos relevantes para minimizar el consumo de tokens.
3. **Motor Cognitivo Previo:** Antes de consultar cualquier LLM, el sistema debe comprender el input, detectar objetivos implícitos y datos faltantes, formular todas las preguntas de aclaración en un único paso, clasificar el proyecto, recuperar memoria relevante y definir el flujo de trabajo óptimo.
4. **Orquestador de IA & Prompt Engineer Automático:** Selección del modelo óptimo de forma dinámica. El input del usuario nunca se envía directamente; se traduce mediante un motor que genera prompts optimizados según las fortalezas específicas del modelo.
5. **Red de Agentes Especialistas Modulares (Introducción Incremental):**
   - **Fase Inicial:** `Planner` (Planificación de tareas) -> `Executor` (Ejecución de código/tareas) -> `Verifier` (Validación con métricas complejas) -> `Memory` (Persistencia selectiva).
   - **Fases Siguientes:** Expansión del catálogo de agentes especialistas (Arquitecto, Programador, Investigador, etc.).
6. **Pipeline Secuencial y Bucle de Verificación de Calidad:** Flujo estricto de Comprensión -> Preguntas -> Planificación -> Recorrido del Grafo -> Selección de IA -> Generación de Prompts -> Ejecución -> Integración -> Verificación -> Corrección automática -> Entrega.
7. **Extensibilidad de Dominios:** Capacidad para soportar múltiples dominios (desarrollo, videojuegos, ciencia de datos, matemáticas, etc.) sin modificar el núcleo de la aplicación.
8. **Experiencia de Usuario (UX) Simple:** Interfaz unificada donde el usuario solo describe su objetivo final y el sistema se encarga de todo el ciclo de vida de manera automatizada.

---

## Decisiones de Arquitectura

### 1. Estructura de Módulos (Backend y Frontend) - Enfoque Monorepo Simplificado
Para no sobrearquitecturar desde el primer día, consolidamos el monorepo inicial en menos paquetes, concentrando la lógica del motor cognitivo, los agentes iniciales y el orquestador en un único backend extensible:

*   `apps/frontend`: Aplicación web moderna construida con **Next.js** y **TypeScript**.
*   `apps/backend`: Servidor unificado en **FastAPI (Python)** que contiene:
    *   `core`: Router, Pipeline cognitivo y lógica de Observabilidad.
    *   `agents`: Catálogo inicial incremental (`Planner`, `Executor`, `Verifier`, `Memory`).
    *   `brain`: Módulos de memoria y abstracciones de grafos de conocimiento.
    *   `orchestrator`: Ruteo de LLM y Prompt Engineering.

---

### 2. Pila Tecnológica Seleccionada y Justificación

| Componente | Tecnología | Justificación |
| :--- | :--- | :--- |
| **Backend Core** | `Python (FastAPI)` | Ecosistema líder indiscutible en IA y manipulación de datos. FastAPI ofrece un rendimiento asíncrono superior (ASGI), tipado fuerte con Pydantic para validar entradas/salidas de agentes, y documentación automática e interactiva (OpenAPI). |
| **Frontend** | `Next.js 14 (React) + TypeScript + Tailwind CSS` | Next.js proporciona Server-Side Rendering (SSR) y Static Site Generation (SSG), excelente para cargas rápidas de UI. TypeScript garantiza la robustez del código frontend. Tailwind CSS permite diseñar interfaces de usuario modernas, adaptables y minimalistas con alta velocidad de desarrollo. Además, es altamente compatible con futuros empaquetados para escritorio (vía Tauri o Electron) y móvil. |
| **Grafo de Conocimiento (El Cerebro)** | `Neo4j` (o base de datos basada en grafos con soporte local/nube) | Permite almacenar entidades, proyectos y decisiones como nodos interconectados. El lenguaje de consulta Cypher facilita la recuperación selectiva de subgrafos locales (por ejemplo, vecinos de rango N) para evitar el desbordamiento de contexto de tokens. |
| **Memoria Semántica y Vectorial** | `Qdrant` | Base de datos vectorial optimizada para búsquedas semánticas rápidas. Se integrará en conjunto con el Grafo de Conocimiento en un patrón **GraphRAG** para resolver de manera óptima las memorias temporales y permanentes. |
| **Base de Datos Relacional** | `PostgreSQL` | Estándar de la industria para almacenar metadatos de usuario, estados persistentes de tareas de larga duración (pipelines) y logs de auditoría estructurados. |
| **Caché y Cola de Tareas** | `Redis` | Almacenamiento clave-valor en memoria de baja latencia para el estado actual de la sesión, caché de peticiones idénticas de agentes y colas de mensajes de procesamiento en tiempo real. |
| **Orquestación de Agentes** | `LangGraph` | Extensión de LangChain diseñada específicamente para construir arquitecturas multiagente cíclicas y de grano fino. Permite modelar el pipeline de TITÁN como un grafo de control donde las transiciones entre agentes, las verificaciones de calidad y los bucles de autocorrección son deterministas y fáciles de auditar. |
| **Observabilidad** | `OpenTelemetry` + `Langfuse` o logs estructurados | Incorporación desde el inicio de telemetría de trazas de LLMs, latencia, número de tokens/costes y calidad de las respuestas para monitorear el rendimiento en tiempo real de cada paso del pipeline. |

---

### 3. Detalle del Pipeline Cognitivo y Flujo de Ejecución Incremental

El procesamiento de una petición del usuario sigue el flujo secuencial y controlado representado a continuación, implementado de forma incremental:

```
[Usuario]
   │
   ▼
[Comprensión y Análisis] ──► Detecta intenciones, objetivos ocultos e información faltante.
   │
   ├─► ¿Falta info crítica? ──► [Formulación de Preguntas en un solo Paso] ──► [Respuesta Usuario]
   │
   ▼
[Planner Agent] ──► Clasifica el dominio del proyecto y genera un Grafo de Tareas ordenado de forma secuencial/paralela.
   │
   ▼
[Memory (Neo4j/Qdrant)] ──► Recupera subgrafos contextuales o recuerdos relevantes del proyecto/usuario.
   │
   ▼
[Orquestador de IA (Ruteador + Prompter)] ──► Generación de prompts optimizados y selección automática del LLM idóneo.
   │
   ▼
[Executor Agent] ──► Ejecución técnica de las tareas individuales del plan.
   │
   ▼
[Bucle de Verificación de Calidad] ◄────┐ (Rechazo si Confianza < Umbral)
   │                                     │
   ├──► [Verifier Agent] ────────────────┘
   │      ├─ Evalúa Compleción del Requisito (0.0 - 1.0)
   │      ├─ Evalúa Consistencia / Coherencia (0.0 - 1.0)
   │      ├─ Evalúa Precisión / Ausencia de Alucinación (0.0 - 1.0)
   │      └─ Puntaje de Confianza Consolidado (Confianza >= 0.85 para Entrega)
   │
   ▼ (Aprobación)
[Entrega al Usuario]
```

---

### 4. Estrategia de Extensibilidad de Dominios
Para permitir que TITÁN se expanda a prácticamente cualquier área (videojuegos, matemáticas, medicina, etc.) sin alterar el motor principal de orquestación, se adopta un **Patrón de Plugins de Dominio**:
* Cada dominio se registra como una clase que implementa la interfaz `BaseDomainPlugin`.
* Expone un esquema de tareas típicas, prompts especializados para ese dominio y herramientas externas asociadas.
* El Motor Cognitivo detecta el dominio, carga dinámicamente las extensiones requeridas y las inyecta en el orquestador de agentes.

---

### 5. Plan de Implementación de Fases (Actualizado)

Para garantizar un desarrollo seguro, estructurado y sin errores, dividiremos el proyecto en las siguientes fases ejecutables:

1.  **Fase 1: Base Arquitectónica y Esqueleto (Actual):**
    *   Definición y aprobación de este ADR (Completado).
    *   Creación de la estructura del backend base (FastAPI) y frontend (Next.js) simplificado en el monorepo.
    *   Interfaces iniciales de los agentes incrementales (`Planner`, `Executor`, `Verifier`, `Memory`).
    *   Definición del objeto `VerificationResult` con métricas cuantitativas (compleción, consistencia, precisión) y puntaje de confianza.
    *   Esqueleto del sistema de Observabilidad (mecanismo base de trazas de latencia, coste/tokens y calidad).
2.  **Fase 2: Motor Cognitivo y Orquestación:**
    *   Implementación de la lógica de comprensión, detección de vacíos de información y formulación de preguntas.
    *   Construcción del ruteador de LLM dinámico y el Generador Automático de Prompts.
3.  **Fase 3: Cerebro Cognitivo y Almacenamiento (GraphRAG):**
    *   Integración de bases de datos Neo4j y Qdrant.
    *   Lógica de indexación semántica dinámica de relaciones y actualización de pesos por aprendizaje continuo.
4.  **Fase 4: Red de Agentes Especialistas Completa:**
    *   Desarrollo detallado de cada agente (Programador, Diseñador, Investigador, Matemático, Verificador con bucle de corrección automática).
5.  **Fase 5: Extensibilidad, UI Completa y Despliegue:**
    *   Implementación de la interfaz de usuario interactiva y fluida.
    *   Soporte de plugins de dominio extensibles.
    *   Pruebas finales de extremo a extremo (E2E).

---

## Conclusión y Próximos Pasos
Este documento establece los cimientos de **PROYECTO TITÁN** como un sistema robusto, con separación limpia de responsabilidades y modularidad que garantiza su evolución a largo plazo.

Quedamos a la espera de sus comentarios, preguntas y/o aprobación formal de esta arquitectura para iniciar la implementación de la **Fase 1**.
