from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

from apps.backend.core.schemas import UserRequest, UserResponse
from apps.backend.core.config import settings
from apps.backend.core.logger import CorrelationIdMiddleware, logger
from apps.backend.core.metrics import setup_metrics
from apps.backend.brain.database import get_db, Base, engine
from apps.backend.core.pipeline import PipelineOrchestrator

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager. Ensures database schemas are created automatically on startup.
    """
    logger.info("Initializing database schemas...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schemas initialized successfully!")
    except Exception as e:
        logger.error(f"Failed to automatically initialize database schemas: {str(e)}")
    yield

app = FastAPI(
    title=settings.app_name,
    description="The modular, scalable central API for the TITÁN Personal AI Operating System.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enable Correlation ID Middleware for request tracing
app.add_middleware(CorrelationIdMiddleware)

# Initialize Prometheus instrumentation and /metrics route
setup_metrics(app)

# Instantiate the decoupled core pipeline orchestrator
orchestrator = PipelineOrchestrator()

@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": "1.0.0",
        "message": "Welcome to your Personal AI Operating System Cerebro."
    }

@app.post("/api/v1/process", response_model=UserResponse)
async def process_request(request: UserRequest, db: AsyncSession = Depends(get_db)):
    """
    Main entry point for TITÁN Pipeline. Delegates completely to the PipelineOrchestrator service.
    """
    return await orchestrator.process(request, db)
