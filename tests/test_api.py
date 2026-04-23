"""
SkillBridge API Tests
=====================
Covers all 5 required test cases plus additional coverage.

Tests hitting a real (SQLite) database:
  - test_student_signup_and_login          (hits DB for signup + login)
  - test_trainer_creates_session           (hits DB for full create flow)
  - test_student_marks_attendance          (hits DB for full enrol + mark flow)

All others use TestClient with real DB via conftest fixtures.
"""

import pytest


# ─── Test 1: Student signup and login — asserts valid JWT returned ────────────

class TestAuthSignupLogin:
    """Test 1 (required): Successful student signup and login with JWT validation."""

    def test_student_signup_returns_jwt(self, client):
        """Signup must return a valid JWT with correct payload."""
        resp = client.post("/auth/signup", json={
            "name": "Aarav Test",
            "email": "aarav.test@example.com",
            "password": "secure123",
            "role": "student",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["role"] == "student"
        assert data["user"]["email"] == "aarav.test@example.com"

        # Decode and validate JWT payload
        from src.auth import decode_token
        payload = decode_token(data["access_token"])
        assert payload["role"] == "student"
        assert "user_id" in payload
        assert payload["token_type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_student_login_returns_jwt(self, client):
        """Login must return a valid JWT after successful credential check."""
        # Create the account first (hits real DB)
        client.post("/auth/signup", json={
            "name": "Login Test",
            "email": "login.test@example.com",
            "password": "loginpass",
            "role": "student",
        })

        resp = client.post("/auth/login", json={
            "email": "login.test@example.com",
            "password": "loginpass",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data

        from src.auth import decode_token
        payload = decode_token(data["access_token"])
        assert payload["role"] == "student"

    def test_login_wrong_password_returns_401(self, client):
        """Wrong password must return 401."""
        client.post("/auth/signup", json={
            "name": "Bad Pass Test",
            "email": "badpass@example.com",
            "password": "correct123",
            "role": "student",
        })
        resp = client.post("/auth/login", json={
            "email": "badpass@example.com",
            "password": "wrongpass",
        })
        assert resp.status_code == 401

    def test_duplicate_email_returns_422(self, client):
        """Duplicate email registration must return 422."""
        payload = {"name": "Dupe", "email": "dupe@x.com", "password": "abc123", "role": "student"}
        client.post("/auth/signup", json=payload)
        resp = client.post("/auth/signup", json=payload)
        assert resp.status_code == 422

    def test_signup_missing_fields_returns_422(self, client):
        """Missing required fields must return 422."""
        resp = client.post("/auth/signup", json={"name": "No Email"})
        assert resp.status_code == 422


# ─── Test 2: Trainer creates a session with all required fields ────────────────

class TestTrainerCreatesSession:
    """Test 2 (required): Trainer creates a session with all required fields."""

    def test_trainer_can_create_session(self, client, trainer_token, batch_id):
        """Trainer assigned to a batch can create a session. Hits real DB."""
        resp = client.post(
            "/sessions",
            json={
                "batch_id": batch_id,
                "title": "Introduction to Python",
                "date": "2025-03-10",
                "start_time": "09:00:00",
                "end_time": "11:00:00",
            },
            headers={"Authorization": f"Bearer {trainer_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Introduction to Python"
        assert data["batch_id"] == batch_id
        assert data["start_time"] == "09:00:00"
        assert data["end_time"] == "11:00:00"
        assert "id" in data

    def test_session_missing_title_returns_422(self, client, trainer_token, batch_id):
        """Missing title field must return 422."""
        resp = client.post(
            "/sessions",
            json={
                "batch_id": batch_id,
                "date": "2025-03-10",
                "start_time": "09:00:00",
                "end_time": "11:00:00",
            },
            headers={"Authorization": f"Bearer {trainer_token}"},
        )
        assert resp.status_code == 422

    def test_session_nonexistent_batch_returns_404(self, client, trainer_token):
        """Referencing a non-existent batch_id must return 404."""
        resp = client.post(
            "/sessions",
            json={
                "batch_id": 99999,
                "title": "Ghost Session",
                "date": "2025-03-10",
                "start_time": "09:00:00",
                "end_time": "11:00:00",
            },
            headers={"Authorization": f"Bearer {trainer_token}"},
        )
        assert resp.status_code == 404

    def test_student_cannot_create_session(self, client, student_token, batch_id):
        """A student attempting to create a session must get 403."""
        resp = client.post(
            "/sessions",
            json={
                "batch_id": batch_id,
                "title": "Illegal Session",
                "date": "2025-03-10",
                "start_time": "09:00:00",
                "end_time": "11:00:00",
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert resp.status_code == 403


# ─── Test 3: Student successfully marks their own attendance ──────────────────

class TestStudentMarksAttendance:
    """Test 3 (required): Student marks their own attendance. Hits real DB."""

    def test_enrolled_student_can_mark_attendance(self, client, enrolled_student, session_id):
        """Student enrolled in a batch can mark attendance for a session in that batch."""
        resp = client.post(
            "/attendance/mark",
            json={"session_id": session_id, "status": "present"},
            headers={"Authorization": f"Bearer {enrolled_student}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "present"
        assert data["session_id"] == session_id

    def test_unenrolled_student_gets_403(self, client, session_id):
        """A student NOT enrolled in the batch must receive 403."""
        # Create a second student who is NOT enrolled
        resp = client.post("/auth/signup", json={
            "name": "Outsider Student",
            "email": "outsider@test.com",
            "password": "out12345",
            "role": "student",
        })
        outsider_token = resp.json()["access_token"]

        mark_resp = client.post(
            "/attendance/mark",
            json={"session_id": session_id, "status": "present"},
            headers={"Authorization": f"Bearer {outsider_token}"},
        )
        assert mark_resp.status_code == 403

    def test_duplicate_attendance_returns_422(self, client, enrolled_student, session_id):
        """Marking attendance twice for the same session must return 422."""
        client.post(
            "/attendance/mark",
            json={"session_id": session_id, "status": "present"},
            headers={"Authorization": f"Bearer {enrolled_student}"},
        )
        resp2 = client.post(
            "/attendance/mark",
            json={"session_id": session_id, "status": "late"},
            headers={"Authorization": f"Bearer {enrolled_student}"},
        )
        assert resp2.status_code == 422

    def test_attendance_nonexistent_session_returns_404(self, client, enrolled_student):
        """Referencing a non-existent session_id must return 404."""
        resp = client.post(
            "/attendance/mark",
            json={"session_id": 99999, "status": "present"},
            headers={"Authorization": f"Bearer {enrolled_student}"},
        )
        assert resp.status_code == 404


# ─── Test 4: POST to /monitoring/attendance returns 405 ──────────────────────

class TestMonitoringMethodNotAllowed:
    """Test 4 (required): POST to /monitoring/attendance must return 405."""

    def test_post_monitoring_attendance_returns_405(self, client, monitoring_officer_token):
        """POST on read-only monitoring endpoint must return 405."""
        resp = client.post(
            "/monitoring/attendance",
            headers={"Authorization": f"Bearer {monitoring_officer_token}"},
        )
        assert resp.status_code == 405

    def test_delete_monitoring_attendance_returns_405(self, client, monitoring_officer_token):
        """DELETE on /monitoring/attendance must return 405."""
        resp = client.delete(
            "/monitoring/attendance",
            headers={"Authorization": f"Bearer {monitoring_officer_token}"},
        )
        assert resp.status_code == 405

    def test_put_monitoring_attendance_returns_405(self, client, monitoring_officer_token):
        """PUT on /monitoring/attendance must return 405."""
        resp = client.put(
            "/monitoring/attendance",
            headers={"Authorization": f"Bearer {monitoring_officer_token}"},
        )
        assert resp.status_code == 405


# ─── Test 5: Protected endpoint with no token returns 401 ────────────────────

class TestNoTokenReturns401:
    """Test 5 (required): Request to protected endpoint with no token must return 401."""

    def test_create_session_without_token_returns_401(self, client):
        """POST /sessions without Authorization header must return 401."""
        resp = client.post("/sessions", json={
            "batch_id": 1,
            "title": "No Auth",
            "date": "2025-01-15",
            "start_time": "09:00:00",
            "end_time": "11:00:00",
        })
        assert resp.status_code == 401

    def test_mark_attendance_without_token_returns_401(self, client):
        """POST /attendance/mark without token must return 401."""
        resp = client.post("/attendance/mark", json={"session_id": 1, "status": "present"})
        assert resp.status_code == 401

    def test_create_batch_without_token_returns_401(self, client):
        """POST /batches without token must return 401."""
        resp = client.post("/batches", json={"name": "X", "institution_id": 1})
        assert resp.status_code == 401

    def test_monitoring_attendance_without_token_returns_401(self, client):
        """GET /monitoring/attendance without token must return 401."""
        resp = client.get("/monitoring/attendance")
        assert resp.status_code == 401

    def test_expired_token_returns_401(self, client):
        """Expired JWT must return 401."""
        import jwt
        from datetime import datetime, timedelta, timezone

        expired_payload = {
            "user_id": 1,
            "role": "student",
            "token_type": "access",
            "iat": datetime.now(timezone.utc) - timedelta(hours=48),
            "exp": datetime.now(timezone.utc) - timedelta(hours=24),
        }
        expired_token = jwt.encode(expired_payload, "test-secret-key-skillbridge", algorithm="HS256")

        resp = client.post(
            "/sessions",
            json={"batch_id": 1, "title": "X", "date": "2025-01-01",
                  "start_time": "09:00:00", "end_time": "10:00:00"},
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert resp.status_code == 401


# ─── Bonus: Monitoring token flow ────────────────────────────────────────────

class TestMonitoringTokenFlow:
    """Bonus: Two-step monitoring token flow."""

    def test_monitoring_officer_gets_scoped_token(self, client, monitoring_officer_token):
        """Valid monitoring officer can exchange API key for scoped token."""
        resp = client.post(
            "/auth/monitoring-token",
            json={"key": "test-monitor-key-2025"},
            headers={"Authorization": f"Bearer {monitoring_officer_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["expires_in_seconds"] == 3600

        from src.auth import decode_token
        payload = decode_token(data["access_token"])
        assert payload["token_type"] == "monitoring"
        assert payload["scope"] == "read:monitoring"
        assert payload["role"] == "monitoring_officer"

    def test_wrong_api_key_returns_401(self, client, monitoring_officer_token):
        """Wrong API key must return 401."""
        resp = client.post(
            "/auth/monitoring-token",
            json={"key": "wrong-key"},
            headers={"Authorization": f"Bearer {monitoring_officer_token}"},
        )
        assert resp.status_code == 401

    def test_non_monitoring_role_cannot_get_monitoring_token(self, client, trainer_token):
        """A trainer cannot get a monitoring token."""
        resp = client.post(
            "/auth/monitoring-token",
            json={"key": "test-monitor-key-2025"},
            headers={"Authorization": f"Bearer {trainer_token}"},
        )
        assert resp.status_code == 403

    def test_standard_token_rejected_on_monitoring_endpoint(self, client, monitoring_officer_token):
        """Standard JWT (not monitoring-scoped) must be rejected at /monitoring/attendance."""
        resp = client.get(
            "/monitoring/attendance",
            headers={"Authorization": f"Bearer {monitoring_officer_token}"},
        )
        # Should be 401 because standard token is not a monitoring token
        assert resp.status_code == 401
