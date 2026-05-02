from __future__ import annotations

from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreate, TaskOut, TaskStatus, TaskUpdate


class TaskNotFoundError(Exception):
    """Raised when the requested task does not exist."""


class TaskService:
    """Business layer for task operations."""

    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    def create_task(self, payload: TaskCreate) -> TaskOut:
        """Create and return a new task."""
        return self._repository.create(payload)

    def list_tasks(self, status: TaskStatus | None = None) -> list[TaskOut]:
        """List tasks, optionally filtered by status."""
        return self._repository.list(status=status)

    def filter_tasks(
        self,
        task_id: int | None = None,
        status: TaskStatus | None = None,
    ) -> list[TaskOut]:
        """Filter tasks by optional ID and/or status."""
        return self._repository.search(task_id=task_id, status=status)

    def get_task_by_id(self, task_id: int) -> TaskOut:
        """Return one task by ID or raise TaskNotFoundError."""
        task = self._repository.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(f"Task with id={task_id} not found")
        return task

    def update_task(self, task_id: int, payload: TaskUpdate) -> TaskOut:
        """Update one task by ID or raise TaskNotFoundError."""
        task = self._repository.update(task_id, payload)
        if task is None:
            raise TaskNotFoundError(f"Task with id={task_id} not found")
        return task

    def delete_task(self, task_id: int) -> None:
        """Delete one task by ID or raise TaskNotFoundError."""
        deleted = self._repository.delete(task_id)
        if not deleted:
            raise TaskNotFoundError(f"Task with id={task_id} not found")
