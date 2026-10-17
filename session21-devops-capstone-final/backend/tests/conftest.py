import os

# Point the app at a throwaway SQLite file before app.db builds its engine.
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import pytest
from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app


@pytest.fixture()
def client():
    # Entering the context manager runs the lifespan hook, which creates the tables.
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)
