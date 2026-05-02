from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel

from app.db.database import create_tables


class HealthResponse(BaseModel):
    status: str
    timestamp: str


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    create_tables()
    yield


app = FastAPI(title="To-Do List API", lifespan=lifespan)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    current_timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return HealthResponse(status="ok", timestamp=current_timestamp)
