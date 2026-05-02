from __future__ import annotations

from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.api.task_routes import get_task_service
from app.db.database import Base
from app.main import app
from app.models.task_model import Task  # noqa: F401
from app.repositories.task_repository import TaskRepository
from app.services.task_service import TaskService


@pytest.fixture
def task_service() -> TaskService:
    """Build a fresh TaskService backed by in-memory SQLite for each test."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    session: Session = session_local()
    repository = TaskRepository(session)
    service = TaskService(repository)

    try:
        yield service
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(task_service: TaskService) -> TestClient:
    """Create a TestClient overriding TaskService dependency for isolation."""

    def _override_task_service() -> TaskService:
        return task_service

    app.dependency_overrides[get_task_service] = _override_task_service

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_post_tasks_returns_201(client: TestClient) -> None:
    """POST /tasks should create a task and return 201."""
    response = client.post(
        "/tasks",
        json={"title": "Criar endpoint", "description": "Implementar rota"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["title"] == "Criar endpoint"
    assert body["status"] == "pending"


def test_get_tasks_returns_200(client: TestClient) -> None:
    """GET /tasks should list tasks and return 200."""
    client.post("/tasks", json={"title": "Tarefa A"})
    client.post("/tasks", json={"title": "Tarefa B"})

    response = client.get("/tasks")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert {item["title"] for item in body} == {"Tarefa A", "Tarefa B"}


def test_put_tasks_by_id_returns_200(client: TestClient) -> None:
    """PUT /tasks/{id} should update task and return 200."""
    created = client.post("/tasks", json={"title": "Original"}).json()

    response = client.put(
        f"/tasks/{created['id']}",
        json={"title": "Atualizada", "status": "completed"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["title"] == "Atualizada"
    assert body["status"] == "completed"


def test_delete_tasks_by_id_returns_204(client: TestClient) -> None:
    """DELETE /tasks/{id} should remove task and return 204."""
    created = client.post("/tasks", json={"title": "Remover"}).json()

    response = client.delete(f"/tasks/{created['id']}")

    assert response.status_code == 204
    assert response.content == b""


def test_get_tasks_by_invalid_id_returns_404(client: TestClient) -> None:
    """GET /tasks/{id} should return 404 when task does not exist."""
    response = client.get("/tasks/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task with id=999 not found"


def test_put_tasks_by_invalid_id_returns_404(client: TestClient) -> None:
    """PUT /tasks/{id} should return 404 when task does not exist."""
    response = client.put("/tasks/999", json={"title": "Nao existe"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Task with id=999 not found"


def test_delete_tasks_by_invalid_id_returns_404(client: TestClient) -> None:
    """DELETE /tasks/{id} should return 404 when task does not exist."""
    response = client.delete("/tasks/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task with id=999 not found"


def test_post_tasks_with_missing_title_returns_422(client: TestClient) -> None:
    """POST /tasks should return 422 when required fields are missing."""
    response = client.post("/tasks", json={"description": "Sem titulo"})

    assert response.status_code == 422


def test_post_tasks_with_invalid_type_returns_422(client: TestClient) -> None:
    """POST /tasks should return 422 when payload has invalid field types."""
    response = client.post("/tasks", json={"title": 123})

    assert response.status_code == 422


def test_put_tasks_with_invalid_status_returns_422(client: TestClient) -> None:
    """PUT /tasks/{id} should return 422 for invalid status enum value."""
    created = client.post("/tasks", json={"title": "Original"}).json()

    response = client.put(
        f"/tasks/{created['id']}",
        json={"status": "in-progress"},
    )

    assert response.status_code == 422


def test_filter_tasks_returns_200_with_query_params(client: TestClient) -> None:
    """GET /tasks/filter should filter by id and status and return 200."""
    pending = client.post("/tasks", json={"title": "Pendente", "status": "pending"}).json()
    client.post("/tasks", json={"title": "Concluida", "status": "completed"})

    response = client.get(f"/tasks/filter?id={pending['id']}&status=pending")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == pending["id"]


def test_filter_tasks_without_params_returns_all(client: TestClient) -> None:
    """GET /tasks/filter without params should return all tasks."""
    client.post("/tasks", json={"title": "A"})
    client.post("/tasks", json={"title": "B"})

    response = client.get("/tasks/filter")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_filter_tasks_with_no_match_returns_empty_list(client: TestClient) -> None:
    """GET /tasks/filter should return empty list when filters do not match."""
    pending = client.post("/tasks", json={"title": "A", "status": "pending"}).json()

    response = client.get(f"/tasks/filter?id={pending['id']}&status=completed")

    assert response.status_code == 200
    assert response.json() == []


def test_filter_tasks_with_invalid_id_returns_422(client: TestClient) -> None:
    """GET /tasks/filter should return 422 for invalid query id."""
    response = client.get("/tasks/filter?id=0")

    assert response.status_code == 422
