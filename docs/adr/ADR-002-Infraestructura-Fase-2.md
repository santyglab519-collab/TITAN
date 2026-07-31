# ADR-002: Infraestructura y Configuración de Soporte para la Fase 2 (TITÁN)

## Estado
Propuesto (Esperando Aprobación de Arquitectura por el Usuario/CTO)

## Contexto y Requisitos
Como parte de la evolución controlada del **PROYECTO TITÁN**, tras culminar exitosamente la Phase 1 (Base y Esqueleto de la API), iniciamos la **Fase 2** enfocada en asentar bases sólidas de infraestructura antes de expandir el cerebro cognitivo y los agentes con IA avanzada.

Los objetivos clave de infraestructura de la Fase 2 son:
1. **Configuración Centralizada:** Validar variables de entorno de manera robusta y segura.
2. **Registro Estructurado y Trazabilidad:** Implementar un sistema de logging JSON que propague identificadores de correlación por solicitud.
3. **Persistencia Relacional:** Conectar e integrar una base de datos PostgreSQL real con soporte de migraciones automáticas.
4. **Métricas y Monitoreo:** Instrumentar endpoints con Prometheus para recolectar métricas clave de latencia y uso de recursos.
5. **Abstracción de Proveedores de LLM:** Diseñar interfaces desacopladas para cambiar dinámicamente entre OpenAI, Anthropic u otros modelos.
6. **Contenerización:** Permitir levantar todo el ecosistema de desarrollo de manera ágil con un solo comando.
7. **Integración Continua (CI):** Automatizar pruebas, formateo, estilo y verificación de tipos estáticos.

---

## Decisiones de Arquitectura

### 1. Configuración Centralizada con `pydantic-settings`
Utilizaremos `pydantic-settings` para cargar, tipar y validar variables de entorno con facilidad desde archivos `.env`. Esto previene el inicio de la aplicación si faltan credenciales o variables críticas.

### 2. Logging Estructurado con Correlation IDs (UUID)
Para garantizar trazabilidad extrema en un flujo asíncrono y multiagente:
* Se implementará un middleware en FastAPI que genere un `correlation_id` (UUID4) por cada petición si no viene en los headers.
* El logger formateará los mensajes en JSON con campos fijos: `timestamp`, `level`, `correlation_id`, `message`, y metadatos extras.

### 3. Persistencia Relacional con `SQLAlchemy` y `Alembic`
* **SQLAlchemy (Async / Sync):** Utilizaremos el ORM estándar en modo asíncrono para bases de datos relacionales robustas como PostgreSQL, asegurando alta concurrencia.
* **Alembic:** Motor de migraciones ligero y flexible de SQLAlchemy para versionar y evolucionar el esquema de la base de datos sin pérdida de información.

### 4. Monitoreo con `Prometheus`
* Integraremos `prometheus-fastapi-instrumentator` para exponer de forma inmediata la ruta `/metrics`, proveyendo trazas de tasa de peticiones, duración promedio (latencia) de HTTP, y conteo de errores listos para paneles de Grafana.

### 5. Interfaces Desacopladas de LLM Providers
Para evitar el acoplamiento a un proveedor particular (vendor lock-in), definiremos la interfaz abstracta `BaseLLMProvider`. Los proveedores concretos (`OpenAIProvider`, `AnthropicProvider`, `LocalLLMProvider`) implementarán esta interfaz, aislando la lógica del dominio del formato propietario de las llamadas API.

### 6. Contenerización Completa (Docker & Docker-Compose)
* **Dockerfile Multi-Stage:** Minimiza el tamaño de la imagen final del backend copiando solo dependencias de ejecución.
* **Docker-Compose:** Levanta de forma automática:
  * El backend de FastAPI en el puerto `8000`.
  * Una base de datos PostgreSQL en el puerto `5432`.
  * Un Prometheus en el puerto `9090` para recolección de métricas.

### 7. Pipelines de CI (Ruff, Black, Mypy, Pytest)
Configuraremos un flujo automático de GitHub Actions que valide la calidad del código antes de aceptar cualquier pull request:
* **Ruff:** El linter más rápido de la comunidad de Python que reemplaza a Flake8/isort.
* **Black:** El formateador de código estándar determinista.
* **Mypy:** Verificación de tipos estáticos rigurosa.
* **Pytest:** Ejecución automatizada de pruebas unitarias y de integración.

---

## Conclusión
Estas elecciones garantizan que TITÁN esté preparado para despliegues de producción desde el inicio, con máxima observabilidad, mantenimiento escalable y entornos de desarrollo unificados.
