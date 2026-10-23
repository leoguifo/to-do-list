"""Integration tests for the To-Do List API full CRUD cycle (CT-01..CT-26).

All internal layers (Routes -> Service -> Repository -> SQLAlchemy ORM) run for
real. The only test isolation is the database: an in-memory SQLite instance per
test. Persistence is verified both via independent HTTP reads and by querying
the live SQLAlchemy session / ``tasks`` table directly.
"""

from __future__ import annotations

from pathlib import Path
import sys
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.api.task_routes import get_task_service
from app.db.database import Base
from app.main import app
from app.models.task_model import Task
from app.repositories.task_repository import TaskRepository
from app.services.task_service import TaskService


@pytest.fixture
def session() -> Iterator[Session]:
    """Provide a fresh in-memory SQLite session with the real schema."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    db: Session = session_local()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(session: Session) -> Iterator[TestClient]:
    """TestClient wired to the real service stack over the test session."""

    def _override_task_service() -> TaskService:
        return TaskService(TaskRepository(session))

    app.dependency_overrides[get_task_service] = _override_task_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _row(session: Session, task_id: int) -> Task | None:
    """Read a task row straight from the DB, bypassing the HTTP/service path."""
    session.expire_all()
    return session.get(Task, task_id)


# --------------------------------------------------------------------------- #
# Grupo 1 - Ciclo completo
# --------------------------------------------------------------------------- #
def test_ct01_full_create_read_update_delete_cycle(
    client: TestClient, session: Session
) -> None:
    """CT-01: full lifecycle across all layers with persistence checks."""
    created = client.post(
        "/tasks",
        json={"title": "Estudar QA", "description": "Integração", "status": "pending"},
    )
    assert created.status_code == 201
    body = created.json()
    task_id = body["id"]
    assert isinstance(task_id, int)
    assert body["title"] == "Estudar QA"
    assert body["status"] == "pending"
    assert body["created_at"] == body["updated_at"]

    read = client.get(f"/tasks/{task_id}")
    assert read.status_code == 200
    assert read.json() == body

    updated = client.put(f"/tasks/{task_id}", json={"status": "completed"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "completed"
    assert updated.json()["updated_at"] >= body["updated_at"]

    row = _row(session, task_id)
    assert row is not None
    assert row.status == "completed"

    deleted = client.delete(f"/tasks/{task_id}")
    assert deleted.status_code == 204
    assert deleted.content == b""

    missing = client.get(f"/tasks/{task_id}")
    assert missing.status_code == 404
    assert missing.json()["detail"] == f"Task with id={task_id} not found"
    assert _row(session, task_id) is None


# --------------------------------------------------------------------------- #
# Grupo 2 - Create
# --------------------------------------------------------------------------- #
def test_ct02_create_with_full_payload(client: TestClient) -> None:
    """CT-02: create with all fields and confirm persistence via fresh GET."""
    created = client.post(
        "/tasks",
        json={"title": "Tarefa", "description": "Detalhe", "status": "completed"},
    ).json()

    read = client.get(f"/tasks/{created['id']}")
    assert read.status_code == 200
    body = read.json()
    assert body["title"] == "Tarefa"
    assert body["description"] == "Detalhe"
    assert body["status"] == "completed"


def test_ct03_create_with_title_only_uses_defaults(client: TestClient) -> None:
    """CT-03: defaults -> description None, status pending."""
    response = client.post("/tasks", json={"title": "Somente titulo"})

    assert response.status_code == 201
    body = response.json()
    assert body["description"] is None
    assert body["status"] == "pending"


def test_ct04_create_strips_title_whitespace(
    client: TestClient, session: Session
) -> None:
    """CT-04: title is stripped before persistence."""
    created = client.post("/tasks", json={"title": "  Tarefa  "}).json()

    assert created["title"] == "Tarefa"
    row = _row(session, created["id"])
    assert row is not None
    assert row.title == "Tarefa"


def test_ct05_create_with_max_length_title(client: TestClient) -> None:
    """CT-05: title of exactly 120 chars is accepted."""
    title = "a" * 120
    response = client.post("/tasks", json={"title": title})

    assert response.status_code == 201
    assert response.json()["title"] == title


def test_ct06_create_title_over_limit_returns_422(
    client: TestClient, session: Session
) -> None:
    """CT-06: title of 121 chars is rejected and nothing persists."""
    response = client.post("/tasks", json={"title": "a" * 121})

    assert response.status_code == 422
    assert session.query(Task).count() == 0


def test_ct07_create_blank_title_returns_422(
    client: TestClient, session: Session
) -> None:
    """CT-07: whitespace-only title fails min_length after strip."""
    response = client.post("/tasks", json={"title": "   "})

    assert response.status_code == 422
    assert session.query(Task).count() == 0


def test_ct08_create_missing_title_returns_422(client: TestClient) -> None:
    """CT-08: title is required."""
    response = client.post("/tasks", json={"description": "sem titulo"})

    assert response.status_code == 422


def test_ct09_create_invalid_status_returns_422(
    client: TestClient, session: Session
) -> None:
    """CT-09: status must be a valid TaskStatus enum value."""
    response = client.post("/tasks", json={"title": "X", "status": "in-progress"})

    assert response.status_code == 422
    assert session.query(Task).count() == 0


# --------------------------------------------------------------------------- #
# Grupo 3 - Read
# --------------------------------------------------------------------------- #
def test_ct10_list_all_tasks(client: TestClient) -> None:
    """CT-10: GET /tasks returns every persisted task."""
    client.post("/tasks", json={"title": "Tarefa A"})
    client.post("/tasks", json={"title": "Tarefa B"})

    response = client.get("/tasks")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert {item["title"] for item in body} == {"Tarefa A", "Tarefa B"}


def test_ct11_list_empty_returns_empty_array(client: TestClient) -> None:
    """CT-11: listing with empty DB returns []."""
    response = client.get("/tasks")

    assert response.status_code == 200
    assert response.json() == []


def test_ct12_list_filtered_by_status(client: TestClient) -> None:
    """CT-12: GET /tasks?status= filters the collection."""
    client.post("/tasks", json={"title": "Pendente", "status": "pending"})
    client.post("/tasks", json={"title": "Concluida", "status": "completed"})

    response = client.get("/tasks?status=completed")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Concluida"


def test_ct13_get_existing_by_id(client: TestClient) -> None:
    """CT-13: single task read by id."""
    created = client.post("/tasks", json={"title": "Alvo"}).json()

    response = client.get(f"/tasks/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_ct14_get_missing_id_returns_404(client: TestClient) -> None:
    """CT-14: reading an unknown id returns 404."""
    response = client.get("/tasks/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task with id=999 not found"


def test_ct15_filter_by_id_and_status_match(client: TestClient) -> None:
    """CT-15: /tasks/filter with id + status returns the matching task."""
    pending = client.post("/tasks", json={"title": "Pendente", "status": "pending"}).json()
    client.post("/tasks", json={"title": "Concluida", "status": "completed"})

    response = client.get(f"/tasks/filter?id={pending['id']}&status=pending")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == pending["id"]


def test_ct16_filter_without_match_returns_empty(client: TestClient) -> None:
    """CT-16: filter with no match returns []."""
    pending = client.post("/tasks", json={"title": "A", "status": "pending"}).json()

    response = client.get(f"/tasks/filter?id={pending['id']}&status=completed")

    assert response.status_code == 200
    assert response.json() == []


def test_ct17_filter_invalid_id_returns_422(client: TestClient) -> None:
    """CT-17: filter id must be >= 1."""
    response = client.get("/tasks/filter?id=0")

    assert response.status_code == 422


# --------------------------------------------------------------------------- #
# Grupo 4 - Update
# --------------------------------------------------------------------------- #
def test_ct18_partial_update_preserves_other_fields(
    client: TestClient, session: Session
) -> None:
    """CT-18: updating only status keeps title; change persists."""
    created = client.post("/tasks", json={"title": "Original", "status": "pending"}).json()

    response = client.put(f"/tasks/{created['id']}", json={"status": "completed"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["title"] == "Original"

    read = client.get(f"/tasks/{created['id']}").json()
    assert read["status"] == "completed"
    row = _row(session, created["id"])
    assert row is not None
    assert row.status == "completed"
    assert row.title == "Original"


def test_ct19_update_multiple_fields(client: TestClient) -> None:
    """CT-19: updating title and status together."""
    created = client.post("/tasks", json={"title": "Original"}).json()

    response = client.put(
        f"/tasks/{created['id']}",
        json={"title": "Novo", "status": "completed"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Novo"
    assert body["status"] == "completed"
    assert body["updated_at"] >= created["updated_at"]


def test_ct20_update_with_empty_body_keeps_business_fields(client: TestClient) -> None:
    """CT-20: PUT {} leaves business fields unchanged (current behavior)."""
    created = client.post(
        "/tasks", json={"title": "Imutavel", "description": "d", "status": "pending"}
    ).json()

    response = client.put(f"/tasks/{created['id']}", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Imutavel"
    assert body["description"] == "d"
    assert body["status"] == "pending"


def test_ct21_update_missing_id_returns_404(client: TestClient) -> None:
    """CT-21: updating an unknown id returns 404."""
    response = client.put("/tasks/999", json={"title": "X"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Task with id=999 not found"


def test_ct22_update_invalid_status_returns_422(
    client: TestClient, session: Session
) -> None:
    """CT-22: invalid status enum is rejected and the row is unchanged."""
    created = client.post("/tasks", json={"title": "Original", "status": "pending"}).json()

    response = client.put(f"/tasks/{created['id']}", json={"status": "doing"})

    assert response.status_code == 422
    row = _row(session, created["id"])
    assert row is not None
    assert row.status == "pending"


def test_ct23_update_title_over_limit_returns_422(client: TestClient) -> None:
    """CT-23: title length limit also applies on update."""
    created = client.post("/tasks", json={"title": "Original"}).json()

    response = client.put(f"/tasks/{created['id']}", json={"title": "a" * 121})

    assert response.status_code == 422


# --------------------------------------------------------------------------- #
# Grupo 5 - Delete
# --------------------------------------------------------------------------- #
def test_ct24_delete_existing_task(client: TestClient, session: Session) -> None:
    """CT-24: delete removes the row and later reads 404."""
    created = client.post("/tasks", json={"title": "Remover"}).json()

    response = client.delete(f"/tasks/{created['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert _row(session, created["id"]) is None
    assert client.get(f"/tasks/{created['id']}").status_code == 404


def test_ct25_delete_missing_id_returns_404(client: TestClient) -> None:
    """CT-25: deleting an unknown id returns 404."""
    response = client.delete("/tasks/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task with id=999 not found"


def test_ct26_delete_is_not_idempotent_on_second_call(client: TestClient) -> None:
    """CT-26: first delete 204, second delete 404."""
    created = client.post("/tasks", json={"title": "Remover"}).json()

    first = client.delete(f"/tasks/{created['id']}")
    second = client.delete(f"/tasks/{created['id']}")

    assert first.status_code == 204
    assert second.status_code == 404
