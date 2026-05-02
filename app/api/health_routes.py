from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    timestamp: str


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    current_timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return HealthResponse(status="ok", timestamp=current_timestamp)
