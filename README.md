# SkillBridge Attendance API

Backend API for the SkillBridge attendance management system, designed for a state-level skilling programme.

## 🚀 Live API
- **Base URL**: [YOUR_DEPLOYED_URL_HERE] (e.g., `https://skillbridge-api.railway.app`)
- **Interactive Docs**: `/docs`

## 🛠️ Local Setup

### Prerequisites
- Python 3.10+
- pip

### Installation
1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Python_Assignment
   ```

2. **Set up virtual environment** (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```
   *Note: For local development, the default SQLite configuration works out of the box.*

5. **Seed the database**:
   ```bash
   python -m src.seed
   ```

6. **Run the server**:
   ```bash
   uvicorn src.main:app --reload
   ```

## 🧪 Testing
Run the test suite using pytest:
```bash
python -m pytest tests/
```
The suite includes 25 tests covering auth, role-based access control (RBAC), and core attendance flows.

## 👥 Test Accounts
The seed script creates the following accounts (password: `inst123` for institutions, `trainer123` for trainers, `student123` for students, etc.):

| Role | Email | Password |
|------|-------|----------|
| Institution | `admin@sunrise.edu` | `inst123` |
| Trainer | `ankit@sunrise.edu` | `trainer123` |
| Student | `aarav@student.sb` | `student123` |
| Programme Manager | `pm@skillbridge.gov` | `pm123456` |
| Monitoring Officer | `monitor@skillbridge.gov` | `mo123456` |

## 🔑 Authentication Flow

### Standard Login
1. `POST /auth/login` with credentials.
2. Receive a JWT `access_token`.
3. Include header: `Authorization: Bearer <token>` in subsequent requests.

### Monitoring Officer (Dual-Token)
The Monitoring Officer requires a second step to access strictly monitored data:
1. **Step 1**: Login via `/auth/login` to get a standard token.
2. **Step 2**: Exchange the standard token + API Key for a scoped token:
   ```bash
   curl -X POST /auth/monitoring-token \
     -H "Authorization: Bearer <standard_token>" \
     -H "Content-Type: application/json" \
     -d '{"key": "sb-monitor-key-2025-secure"}'
   ```
3. **Step 3**: Use the returned `access_token` (1-hour expiry) to call `GET /monitoring/attendance`.

## 🏗️ Architecture & Decisions

### Schema Choices
- **`batch_trainers`**: A many-to-many link table. This allows multiple trainers to be assigned to a single batch, supporting co-teaching and institutional oversight.
- **`batch_invites`**: Implements a token-based join system. Trainers generate secure tokens that students use to enroll, avoiding manual entry errors.
- **Dual-Token Auth**: We implemented an extra "exchange" step for the Monitoring Officer. This follows the principle of least privilege—the standard token cannot view sensitive logs until an API Key is provided, creating a scoped, short-lived session specifically for monitoring.

### JWT Structure
- **Standard**: `{"user_id": int, "role": str, "token_type": "access", "iat": timestamp, "exp": timestamp}`
- **Monitoring**: `{"user_id": int, "role": "monitoring_officer", "token_type": "monitoring", "scope": "read:monitoring", ...}`

### Security & Token Management
- **Rotation/Revocation**: In a production environment, we would implement a "Blacklist" using Redis to track revoked tokens before they expire.
- **Identified Issue**: The current implementation uses stateless JWTs without revocation. If a token is compromised, it remains valid until expiry (24h). 
- **Fix**: Implementation of Refresh Tokens and a revocation registry.

## 📁 Submission Structure
- `CONTACT.txt`: Contact information and challenge summary.
- `src/`: Core application logic (FastAPI routers, SQLAlchemy models, Pydantic schemas).
- `tests/`: Pytest suite using a dedicated test database.
- `requirements.txt`: Python dependencies.
- `Procfile`: Deployment configuration for Railway/Render.
- `.env.example`: Template for environment secrets.

## ✅ Implementation Status
- **Task 1 (Core API)**: 100% Completed. All models and endpoints implemented.
- **Task 2 (Auth & RBAC)**: 100% Completed. Role-based access enforced globally.
- **Task 3 (Validation & Tests)**: 100% Completed. 25 tests passing.
- **Task 4 (Deployment)**: Deployment ready via `Procfile`. (Live URL placeholder included).
- **Task 5 (README)**: Completed.
