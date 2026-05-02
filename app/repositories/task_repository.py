from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.task_model import Task
from app.schemas.task import TaskCreate, TaskOut, TaskStatus, TaskUpdate


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TaskRepository:
    """SQLite-backed task repository using SQLAlchemy ORM."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, payload: TaskCreate) -> TaskOut:
        """Persist a new task and return it."""
        entity = Task(
            title=payload.title,
            description=payload.description,
            status=payload.status.value,
            created_at=_utcnow(),
            updated_at=_utcnow(),
        )
        self._db.add(entity)
        self._db.commit()
        self._db.refresh(entity)
        return TaskOut.model_validate(entity)

    def list(self, status: TaskStatus | None = None) -> list[TaskOut]:
        """Return all tasks, optionally filtered by status."""
        query = self._db.query(Task)
        if status is not None:
            query = query.filter(Task.status == status.value)
        return [TaskOut.model_validate(e) for e in query.all()]

    def search(
        self,
        task_id: int | None = None,
        status: TaskStatus | None = None,
    ) -> list[TaskOut]:
        """Search tasks by optional ID and/or status."""
        query = self._db.query(Task)
        if task_id is not None:
            query = query.filter(Task.id == task_id)
        if status is not None:
            query = query.filter(Task.status == status.value)
        return [TaskOut.model_validate(e) for e in query.all()]

    def get_by_id(self, task_id: int) -> TaskOut | None:
        """Return a task by ID, or None if not found."""
        entity = self._db.get(Task, task_id)
        return TaskOut.model_validate(entity) if entity else None

    def update(self, task_id: int, payload: TaskUpdate) -> TaskOut | None:
        """Apply partial update to a task. Returns updated task or None if not found."""
        entity = self._db.get(Task, task_id)
        if entity is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(entity, field, value.value if hasattr(value, "value") else value)
        entity.updated_at = _utcnow()
        self._db.commit()
        self._db.refresh(entity)
        return TaskOut.model_validate(entity)

    def delete(self, task_id: int) -> bool:
        """Remove a task by ID. Returns True if deleted, False if not found."""
        entity = self._db.get(Task, task_id)
        if entity is None:
            return False
        self._db.delete(entity)
        self._db.commit()
        return True
