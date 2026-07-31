import pytest
from fastapi.testclient import TestClient
import sys
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.future import select

sys.path.append(".")
from apps.backend.main import app
from apps.backend.brain.database import get_db, Base, ProjectModel, TaskModel

# Set up in-memory SQLite for testing database operations
test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

# Override the live DB dependency with the in-memory SQLite DB
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
async def setup_test_db():
    # Create tables before each test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Drop tables after each test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "TITÁN Core"

def test_process_request_clarification_needed():
    payload = {
        "user_id": "test_user_1",
        "session_id": "session_123",
        "text_prompt": "crear"
    }
    response = client.post("/api/v1/process", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "clarification_needed"
    assert data["comprehension"]["clarification"]["needed"] is True

@pytest.mark.anyio
async def test_process_request_videojuegos_and_database_persistence():
    payload = {
        "user_id": "test_user_db_1",
        "session_id": "session_db_123",
        "text_prompt": "Quiero construir un videojuego de rol en 2D"
    }
    response = client.post("/api/v1/process", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed" or data["status"] == "requires_correction"
    assert data["comprehension"]["domain_classified"] == "videojuegos"

    # Assert database persistence
    async with TestingSessionLocal() as session:
        # Check Project was saved
        proj_query = await session.execute(select(ProjectModel).filter_by(session_id="session_db_123"))
        proj = proj_query.scalars().first()
        assert proj is not None
        assert proj.user_id == "test_user_db_1"
        assert proj.domain_classified == "videojuegos"

        # Check Tasks were saved
        tasks_query = await session.execute(select(TaskModel).filter_by(project_id=proj.id))
        tasks = tasks_query.scalars().all()
        assert len(tasks) == 3
        assert tasks[0].agent_role == "Designer"
        assert tasks[0].status == "completed"
        assert tasks[0].output is not None

def test_process_request_software():
    payload = {
        "user_id": "test_user_2",
        "session_id": "session_456",
        "text_prompt": "Necesito desarrollar una aplicación web moderna"
    }
    response = client.post("/api/v1/process", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["comprehension"]["domain_classified"] == "desarrollo_software"
    assert len(data["plan"]["tasks"]) == 3
    assert data["plan"]["tasks"][0]["agent_role"] == "Architect"
