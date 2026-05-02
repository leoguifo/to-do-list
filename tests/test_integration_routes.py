from __future__ import annotations

from pathlib import Path
import sqlite3
import sys

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app
import app.db.database as database


def test_lifespan_creates_db_and_tasks_table(tmp_path, monkeypatch) -> None:
    """Application startup should create SQLite file and tasks table."""
    db_file = tmp_path / "todo.db"

    # Reconfigure DB module for this test to ensure isolation in a temp file.
    test_engine = create_engine(
        f"sqlite:///{db_file.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    monkeypatch.setattr(database, "engine", test_engine)
    monkeypatch.setattr(
        database,
        "SessionLocal",
        sessionmaker(bind=test_engine, autocommit=False, autoflush=False),
    )

    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200

    assert db_file.exists()

    with sqlite3.connect(db_file) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }

    assert "tasks" in tables
