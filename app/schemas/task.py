from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


class TaskStatus(StrEnum):
    """Supported task states."""

    PENDING = "pending"
    COMPLETED = "completed"


Title = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=120),
]

Description = Annotated[
    str | None,
    StringConstraints(strip_whitespace=True, max_length=500),
]


class TaskCreate(BaseModel):
    """Payload for creating a task."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: Title = Field(description="Task title.")
    description: Description = Field(default=None, description="Optional task details.")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Initial task status.")


class TaskUpdate(BaseModel):
    """Payload for updating a task. All fields are optional."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: Title | None = Field(default=None, description="New task title.")
    description: Description = Field(default=None, description="New task details.")
    status: TaskStatus | None = Field(default=None, description="New task status.")


class TaskOut(BaseModel):
    """Task representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Unique task identifier.")
    title: str = Field(description="Task title.")
    description: str | None = Field(description="Task details.")
    status: TaskStatus = Field(description="Current task status.")
    created_at: datetime = Field(description="Creation timestamp (UTC).")
    updated_at: datetime = Field(description="Last update timestamp (UTC).")
