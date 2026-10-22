"""Test fixtures.

The tests run against their own throwaway SQLite database, never the
Postgres the app uses in Compose or the cluster. TESTING=1 is set before any
app module is imported, so the lifespan hook skips create_all and the real
engine is never touched.
"""

import os

os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def client():
    # StaticPool keeps one connection alive for the whole test; without it
    # every session would get a fresh in-memory database and the tables
    # created below would vanish.
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # SQLite ignores ON DELETE CASCADE unless foreign keys are switched on
    # per connection, which would let the cascade-delete test pass for the
    # wrong reason.
    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_connection, _):
        cur = dbapi_connection.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    # Entering the context manager runs the lifespan hook, the same way
    # uvicorn would.
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def sample_issue(client):
    """One issue, already created, for tests that need something to act on."""
    response = client.post(
        "/api/issues",
        json={
            "title": "Projector not switching on",
            "description": "Lecture hall projector shows no power light.",
            "building": "Science Block",
            "room": "S-204",
            "category": "electrical",
            "priority": "high",
            "reported_by": "student",
        },
    )
    assert response.status_code == 201
    return response.json()
