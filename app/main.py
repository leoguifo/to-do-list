from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    timestamp: str


app = FastAPI(title="To-Do List API")


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    current_timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return HealthResponse(status="ok", timestamp=current_timestamp)
