from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator


def setup_metrics(app: FastAPI) -> None:
    """
    Configures and hooks the Prometheus Instrumentator middleware into the FastAPI instance.
    Exposes /metrics endpoint for scraping.
    """
    # Create the instrumentator instance
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        env_var_name="ENABLE_METRICS",
        excluded_handlers=["/metrics", "/docs", "/openapi.json"],
    )

    # Initialize instrumentator
    instrumentator.instrument(app)

    # Expose the metric endpoint
    instrumentator.expose(app, endpoint="/metrics")
