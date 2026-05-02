from __future__ import annotations

from pathlib import Path
import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.database import Base
from app.models.task_model import Task  # noqa: F401
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreate, TaskStatus, TaskUpdate
from app.services.task_service import TaskNotFoundError, TaskService


@pytest.fixture
def db_session() -> Session:
    """Create an isolated in-memory SQLite session for each test."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def task_service(db_session: Session) -> TaskService:
    """Build TaskService with a real repository over in-memory DB."""
    repository = TaskRepository(db_session)
    return TaskService(repository)


def test_create_task_persists_data(task_service: TaskService) -> None:
    """Should create a task with generated ID and default pending status."""
    created = task_service.create_task(
        TaskCreate(title="Comprar leite", description="2 litros integral")
    )

    assert created.id == 1
    assert created.title == "Comprar leite"
    assert created.description == "2 litros integral"
    assert created.status == TaskStatus.PENDING


def test_list_tasks_returns_all_created_items(task_service: TaskService) -> None:
    """Should list all tasks stored in the service."""
    task_service.create_task(TaskCreate(title="Tarefa 1"))
    task_service.create_task(TaskCreate(title="Tarefa 2"))

    tasks = task_service.list_tasks()

    assert len(tasks) == 2
    assert [task.title for task in tasks] == ["Tarefa 1", "Tarefa 2"]


def test_update_task_changes_fields(task_service: TaskService) -> None:
    """Should update task fields and keep the same ID."""
    created = task_service.create_task(TaskCreate(title="Original", description="Texto"))

    updated = task_service.update_task(
        created.id,
        TaskUpdate(title="Atualizada", status=TaskStatus.COMPLETED),
    )

    assert updated.id == created.id
    assert updated.title == "Atualizada"
    assert updated.status == TaskStatus.COMPLETED


def test_delete_task_removes_item(task_service: TaskService) -> None:
    """Should delete an existing task and make it unavailable by ID."""
    created = task_service.create_task(TaskCreate(title="Excluir"))

    task_service.delete_task(created.id)

    with pytest.raises(TaskNotFoundError):
        task_service.get_task_by_id(created.id)


def test_nonexistent_task_raises_not_found_error(task_service: TaskService) -> None:
    """Should raise TaskNotFoundError for operations with missing IDs."""
    with pytest.raises(TaskNotFoundError):
        task_service.get_task_by_id(999)

    with pytest.raises(TaskNotFoundError):
        task_service.update_task(999, TaskUpdate(title="Nao existe"))

    with pytest.raises(TaskNotFoundError):
        task_service.delete_task(999)


def test_filter_tasks_by_status_returns_matching_items(task_service: TaskService) -> None:
    """Should filter tasks by status and return only matching tasks."""
    task_service.create_task(TaskCreate(title="Pendente", status=TaskStatus.PENDING))
    task_service.create_task(TaskCreate(title="Concluida", status=TaskStatus.COMPLETED))

    completed_tasks = task_service.filter_tasks(status=TaskStatus.COMPLETED)

    assert len(completed_tasks) == 1
    assert completed_tasks[0].title == "Concluida"
    assert completed_tasks[0].status == TaskStatus.COMPLETED


def test_filter_tasks_by_id_and_status(task_service: TaskService) -> None:
    """Should support combined filtering by task ID and status."""
    pending = task_service.create_task(TaskCreate(title="Item 1", status=TaskStatus.PENDING))
    task_service.create_task(TaskCreate(title="Item 2", status=TaskStatus.COMPLETED))

    match = task_service.filter_tasks(task_id=pending.id, status=TaskStatus.PENDING)
    no_match = task_service.filter_tasks(task_id=pending.id, status=TaskStatus.COMPLETED)

    assert len(match) == 1
    assert match[0].id == pending.id
    assert no_match == []
