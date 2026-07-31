import json
import logging
import uuid
import contextvars
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timezone

# Context variable to store correlation_id per request/task
correlation_id_var = contextvars.ContextVar("correlation_id", default="system")

class StructuredJSONFormatter(logging.Formatter):
    """
    Custom logger formatter that outputs structured JSON logs including the correlation ID.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "correlation_id": correlation_id_var.get(),
            "message": record.getMessage(),
            "logger": record.name,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Merge extra fields if provided
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields) # type: ignore

        return json.dumps(log_data)

def setup_logger(log_level: str = "INFO") -> logging.Logger:
    """
    Configures and returns the root application logger.
    """
    logger = logging.getLogger("titan")
    logger.setLevel(log_level.upper())

    # Remove existing handlers to avoid duplication
    if logger.hasHandlers():
        logger.handlers.clear()

    handler = logging.StreamHandler()
    handler.setFormatter(StructuredJSONFormatter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger

# Initialize application-wide logger
logger = setup_logger()

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    FastAPI Middleware to propagate and inject a Correlation ID for tracing across request lifecycles.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        # Get from headers if exists, else generate fresh UUID4
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())

        # Set context-local correlation ID
        token = correlation_id_var.set(correlation_id)

        logger.info(f"Incoming request: {request.method} {request.url.path}")
        try:
            response: Response = await call_next(request)
        except Exception as e:
            logger.error(f"Uncaught exception processing request: {str(e)}", exc_info=True)
            raise e
        finally:
            # Clean up context variable
            correlation_id_var.reset(token)

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        return response
