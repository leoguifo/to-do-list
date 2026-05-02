from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreate, TaskOut, TaskStatus, TaskUpdate
from app.services.task_service import TaskNotFoundError, TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_task_service(db: Session = Depends(get_db)) -> TaskService:
    repository = TaskRepository(db)
    return TaskService(repository)


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    service: TaskService = Depends(get_task_service),
) -> TaskOut:
    return service.create_task(payload)


@router.get("", response_model=list[TaskOut], status_code=status.HTTP_200_OK)
def list_tasks(
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    service: TaskService = Depends(get_task_service),
) -> list[TaskOut]:
    return service.list_tasks(status=status_filter)


@router.get("/filter", response_model=list[TaskOut], status_code=status.HTTP_200_OK)
def filter_tasks(
    task_id: int | None = Query(default=None, alias="id", ge=1),
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    service: TaskService = Depends(get_task_service),
) -> list[TaskOut]:
    return service.filter_tasks(task_id=task_id, status=status_filter)


@router.get("/{task_id}", response_model=TaskOut, status_code=status.HTTP_200_OK)
def get_task_by_id(
    task_id: int,
    service: TaskService = Depends(get_task_service),
) -> TaskOut:
    try:
        return service.get_task_by_id(task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/{task_id}", response_model=TaskOut, status_code=status.HTTP_200_OK)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    service: TaskService = Depends(get_task_service),
) -> TaskOut:
    try:
        return service.update_task(task_id, payload)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    service: TaskService = Depends(get_task_service),
) -> Response:
    try:
        service.delete_task(task_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
