import pytest
from fastapi.testclient import TestClient
import sys

sys.path.append(".")
from apps.backend.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "TITÁN Core"

def test_process_request_clarification_needed():
    # Very short input should trigger clarification questions
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
    assert len(data["comprehension"]["clarification"]["questions"]) > 0
    assert data["telemetry"]["total_latency_ms"] >= 0

def test_process_request_videojuegos():
    payload = {
        "user_id": "test_user_1",
        "session_id": "session_123",
        "text_prompt": "Quiero construir un videojuego de rol en 2D"
    }
    response = client.post("/api/v1/process", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed" or data["status"] == "requires_correction"
    assert data["comprehension"]["domain_classified"] == "videojuegos"
    assert len(data["plan"]["tasks"]) == 3
    assert data["plan"]["tasks"][0]["agent_role"] == "Designer"
    assert "designer" in data["output"].lower() or "bucle" in data["output"].lower()

    # Check verifier metrics presence
    assert "completeness_score" in data["verification"]
    assert "consistency_score" in data["verification"]
    assert "accuracy_score" in data["verification"]
    assert "confidence_score" in data["verification"]
    assert data["verification"]["confidence_score"] >= 0.0

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
