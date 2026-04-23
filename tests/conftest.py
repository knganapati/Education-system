"""
pytest fixtures for SkillBridge tests.

Uses a real SQLite test database (not mocked) so that at least two tests
hit actual DB operations, as required by the assignment spec.
"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# Point at a separate test database BEFORE importing app
TEST_DB_URL = "sqlite:///./test_skillbridge.db"
os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ["JWT_SECRET_KEY"] = "test-secret-key-skillbridge"
os.environ["MONITORING_API_KEY"] = "test-monitor-key-2025"

from src.main import app
from src.database import Base, get_db

# ── Test engine & session ──────────────────────────────────────────────────────

test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
)


@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create fresh tables once for the test session, drop after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
    # Clean up the SQLite file
    import time
    time.sleep(0.1)
    if os.path.exists("./test_skillbridge.db"):
        try:
            os.remove("./test_skillbridge.db")
        except PermissionError:
            pass


@pytest.fixture(scope="function", autouse=True)
def clean_tables():
    """Wipe all rows before each test so tests are independent."""
    from src.models import Attendance, Session, BatchInvite, BatchStudent, BatchTrainer, Batch, User
    db = TestingSessionLocal()
    try:
        for model in [Attendance, Session, BatchInvite, BatchStudent, BatchTrainer, Batch, User]:
            db.query(model).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture(scope="function")
def client():
    """TestClient with the DB dependency overridden to use the test DB."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ─── Helper fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def institution_token(client):
    """Register an institution and return its JWT."""
    resp = client.post("/auth/signup", json={
        "name": "Test Institution",
        "email": "inst@test.com",
        "password": "inst1234",
        "role": "institution",
    })
    assert resp.status_code == 201
    return resp.json()["access_token"]


@pytest.fixture
def institution_id(client, institution_token):
    """Return the institution user id."""
    from src.auth import decode_token
    payload = decode_token(institution_token)
    return payload["user_id"]


@pytest.fixture
def trainer_token(client, institution_id):
    """Register a trainer under the test institution and return its JWT."""
    resp = client.post("/auth/signup", json={
        "name": "Test Trainer",
        "email": "trainer@test.com",
        "password": "train1234",
        "role": "trainer",
        "institution_id": institution_id,
    })
    assert resp.status_code == 201
    return resp.json()["access_token"]


@pytest.fixture
def trainer_id(client, trainer_token):
    from src.auth import decode_token
    return decode_token(trainer_token)["user_id"]


@pytest.fixture
def student_token(client):
    """Register a student and return its JWT."""
    resp = client.post("/auth/signup", json={
        "name": "Test Student",
        "email": "student@test.com",
        "password": "stud1234",
        "role": "student",
    })
    assert resp.status_code == 201
    return resp.json()["access_token"]


@pytest.fixture
def student_id(client, student_token):
    from src.auth import decode_token
    return decode_token(student_token)["user_id"]


@pytest.fixture
def monitoring_officer_token(client):
    """Register a monitoring officer and return its standard JWT."""
    resp = client.post("/auth/signup", json={
        "name": "Test Monitor",
        "email": "monitor@test.com",
        "password": "mon12345",
        "role": "monitoring_officer",
    })
    assert resp.status_code == 201
    return resp.json()["access_token"]


@pytest.fixture
def batch_id(client, institution_id, trainer_token, trainer_id):
    """Create a batch and return its id."""
    resp = client.post(
        "/batches",
        json={"name": "Test Batch", "institution_id": institution_id},
        headers={"Authorization": f"Bearer {trainer_token}"},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.fixture
def session_id(client, trainer_token, batch_id):
    """Create a session and return its id."""
    resp = client.post(
        "/sessions",
        json={
            "batch_id": batch_id,
            "title": "Test Session",
            "date": "2025-01-15",
            "start_time": "09:00:00",
            "end_time": "11:00:00",
        },
        headers={"Authorization": f"Bearer {trainer_token}"},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.fixture
def enrolled_student(client, student_token, trainer_token, batch_id):
    """Enrol the test student in the test batch via invite token. Returns student token."""
    # Create invite
    inv_resp = client.post(
        f"/batches/{batch_id}/invite",
        headers={"Authorization": f"Bearer {trainer_token}"},
    )
    assert inv_resp.status_code == 201
    token = inv_resp.json()["token"]

    # Student joins
    join_resp = client.post(
        "/batches/join",
        json={"token": token},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert join_resp.status_code == 200
    return student_token
