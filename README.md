# SkillBridge Attendance API

SkillBridge+ is a professional-grade, state-level skilling programme attendance management system. It provides a secure REST API for managing institutions, trainers, students, batches, and live attendance logs.

## 🚀 Live API & Deployment
- **Base URL**: `https://education-system-7vme.onrender.com` (Example Render URL)
- **Interactive API Documentation**: `/docs` (Swagger UI)
- **Deployment Platform**: Render.com (Web Service)
- **Database**: Neon PostgreSQL (Cloud Hosted)

---

## 🛠️ Local Setup Instructions
Follow these steps to run the project from scratch on your machine:

### 1. Prerequisites
- Python 3.10 or higher
- pip (Python package manager)

### 2. Environment Configuration
1. **Clone the repository** and navigate to the directory:
   ```bash
   git clone <repository-url>
   cd Python_Assignment
   ```
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment Variables**:
   Create a `.env` file in the root:
   ```ini
   DATABASE_URL=postgresql://neondb_owner:... (your Neon URL)
   JWT_SECRET_KEY=yoursecretkey
   MONITORING_API_KEY=SB-ADMIN-99-TEST-KEY
   APP_ENV=development
   ```

### 3. Initialize & Run
1. **Seed the database** (Creates tables and initial test accounts):
   ```bash
   python -m src.seed
   ```
2. **Start the server**:
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
   ```

---

## 👥 Test Accounts (Post-Seed)
All roles are pre-seeded with the following credentials:

| Role | Email | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Student** | `aarav@student.sb` | `student123` | Mark own attendance, Join batches. |
| **Trainer** | `ankit@sunrise.edu` | `trainer123` | Create sessions, Manage batches, View stats. |
| **Institution** | `admin@sunrise.edu` | `inst123` | View institution-wide summaries. |
| **Programme Manager** | `pm@skillbridge.gov` | `pm123456` | Global oversight, Performance index access. |
| **Monitoring Officer** | `monitor@skillbridge.gov` | `mo123456` | Access to dual-token secured live logs. |

---

## 🔌 Sample API Usage (cURL)

### 1. Authentication (Login)
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "ankit@sunrise.edu", "password": "trainer123"}'
```
*Action: Copy the `access_token` from the response.*

### 2. Standard Request (e.g., Student Marking Attendance)
```bash
curl -X POST http://localhost:8000/attendance/mark \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"session_id": 1, "status": "present"}'
```

### 3. Monitoring Officer Flow (Dual-Token Step)
Monitoring Officers must exchange their daily token + Security Key for a short-lived (1hr) scoped monitoring token.
```bash
# Step 1: Exchange for Monitoring Scope
curl -X POST http://localhost:8000/auth/monitoring-token \
  -H "Authorization: Bearer <STANDARD_JWT>" \
  -H "Content-Type: application/json" \
  -d '{"key": "SB-ADMIN-99-TEST-KEY"}'

# Step 2: Use the Monitoring Scoped Token
curl -X GET http://localhost:8000/monitoring/attendance \
  -H "Authorization: Bearer <MONITORING_TOKEN>"
```

---

## 🏗️ System Design & Schema Decisions

### 1. Relational Integrity (PostgreSQL)
We moved from SQLite to **Neon PostgreSQL** to support concurrent connections and ACID compliance across multiple institutions.

### 2. Key Modelling Choices
- **`batch_trainers`**: Implemented as a many-to-many junction table. This reflects real-world scenarios where multiple trainers (Lead + Co-trainer) collaborate on a single batch.
- **`batch_invites`**: Uses cryptographic token generation (`secrets.token_urlsafe`). This allows for secure, invite-only enrollment without requiring complex invite-link infrastructure.
- **Dual-Token Monitoring Architecture**: To prevent "Token Theft" of sensitive programme logs, the Monitoring Officer cannot view logs with a standard login token. They must provide a second-factor Security Key (`MONITORING_API_KEY`) to generate a scoped token with a narrow `read:monitoring` permission.

### 3. Security Flow (JWT & Bcrypt)
- **Hashing**: All passwords are salted and hashed using `bcrypt`.
- **RBAC**: Implemented a **Dynamic Permission Checker** in `dependencies.py` that maps Roles to granular permissions (e.g., `mark_attendance`), allowing for easy updates to the security policy without changing code in every route.

### 4. OTP-Ready Architecture (Future Roadmap)
While the current version uses standard credentials for the rapid prototype, the architecture includes an inactivated `request_otp` pipeline. The database is already designed to support short-lived codes and expiration logic for a passwordless "magic code" flow in the future.

---

## ✅ Project Status & Deliverables

| Feature | Status | Note |
| :--- | :--- | :--- |
| **FastAPI Backend** | 🟢 Ready | Fully dynamic, follows REST best practices. |
| **Neon Postgres DB** | 🟢 Ready | Cloud hosted and optimized. |
| **Standard Auth** | 🟢 Ready | Secure email/password login. |
| **Monitoring Auth** | 🟢 Ready | High-security dual-token exchange. |
| **RBAC** | 🟢 Ready | Centralized permission enforcement. |
| **OTP Auth** | 🟡 Skipped | Temporarily removed for simpler deployment as per request. |
| **Front-end UI** | 🟢 Ready | A stunning Vite + Vanilla JS interface. |

### 🛠️ One Thing I’d Do Differently (With more time)
I would implement **Real-time WebSockets** for the Monitoring Officer dashboard. Currently, the officer has to refresh or poll the API to see new attendance logs. Integrating WebSockets (using FastAPI's built-in support) would allow live, scrolling logs to appear in real-time as students across the state mark themselves present.
