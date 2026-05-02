from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.task_model import Task
from app.schemas.task import TaskCreate, TaskOut, TaskStatus, TaskUpdate


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TaskRepository:
    """SQLite-backed task repository using SQLAlchemy ORM."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def _to_out(self, entity: Task) -> TaskOut:
        return TaskOut.model_validate(entity)

    def _build_query(
        self,
        task_id: int | None = None,
        status: TaskStatus | None = None,
    ):
        query = self._db.query(Task)
        if task_id is not None:
            query = query.filter(Task.id == task_id)
        if status is not None:
            query = query.filter(Task.status == status.value)
        return query

    def _commit_and_refresh(self, entity: Task) -> None:
        self._db.commit()
        self._db.refresh(entity)

    def _normalize_update_value(self, value: Any) -> Any:
        if isinstance(value, TaskStatus):
            return value.value
        return value

    def create(self, payload: TaskCreate) -> TaskOut:
        """Persist a new task and return it."""
        now = _utcnow()
        entity = Task(
            title=payload.title,
            description=payload.description,
            status=payload.status.value,
            created_at=now,
            updated_at=now,
        )
        self._db.add(entity)
        self._commit_and_refresh(entity)
        return self._to_out(entity)

    def list(self, status: TaskStatus | None = None) -> list[TaskOut]:
        """Return all tasks, optionally filtered by status."""
        query = self._build_query(status=status)
        return [self._to_out(entity) for entity in query.all()]

    def search(
        self,
        task_id: int | None = None,
        status: TaskStatus | None = None,
    ) -> list[TaskOut]:
        """Search tasks by optional ID and/or status."""
        query = self._build_query(task_id=task_id, status=status)
        return [self._to_out(entity) for entity in query.all()]

    def get_by_id(self, task_id: int) -> TaskOut | None:
        """Return a task by ID, or None if not found."""
        entity = self._db.get(Task, task_id)
        return self._to_out(entity) if entity else None

    def update(self, task_id: int, payload: TaskUpdate) -> TaskOut | None:
        """Apply partial update to a task. Returns updated task or None if not found."""
        entity = self._db.get(Task, task_id)
        if entity is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(entity, field, self._normalize_update_value(value))
        entity.updated_at = _utcnow()
        self._commit_and_refresh(entity)
        return self._to_out(entity)

    def delete(self, task_id: int) -> bool:
        """Remove a task by ID. Returns True if deleted, False if not found."""
        entity = self._db.get(Task, task_id)
        if entity is None:
            return False
        self._db.delete(entity)
        self._db.commit()
        return True
