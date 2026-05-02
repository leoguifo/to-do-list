from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health_routes import router as health_router
from app.api.task_routes import router as task_router
from app.db.database import create_tables


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    create_tables()
    yield


app = FastAPI(title="To-Do List API", lifespan=lifespan)

app.include_router(health_router)
app.include_router(task_router)
