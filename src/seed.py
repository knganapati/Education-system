"""
Seed script for SkillBridge API.

Creates:
  - 2 institutions
  - 1 programme manager
  - 1 monitoring officer
  - 4 trainers
  - 15 students
  - 3 batches (with trainer assignments)
  - 8 sessions (spread across batches)
  - Attendance records for all sessions

Usage:
    python -m src.seed
"""

import sys
import os
from datetime import datetime, date, time, timedelta, timezone

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import SessionLocal, init_db
from src.models import (
    User, UserRole, Batch, BatchTrainer, BatchStudent,
    BatchInvite, Session as SessionModel, Attendance, AttendanceStatus
)
from src.auth import hash_password
import secrets


def seed():
    init_db()
    db = SessionLocal()

    try:
        # ── Wipe existing data ──────────────────────────────────────────────
        print("Clearing existing data...")
        for model in [Attendance, SessionModel, BatchInvite, BatchStudent, BatchTrainer, Batch, User]:
            db.query(model).delete()
        db.commit()

        # ── Institutions ───────────────────────────────────────────────────
        print("Creating institutions...")
        inst1 = User(name="Sunrise Polytechnic", email="admin@sunrise.edu",
                     hashed_password=hash_password("inst123"), role=UserRole.institution)
        inst2 = User(name="Greenfield Skills Centre", email="admin@greenfield.edu",
                     hashed_password=hash_password("inst123"), role=UserRole.institution)
        db.add_all([inst1, inst2])
        db.flush()

        # ── Programme Manager & Monitoring Officer ─────────────────────────
        print("Creating programme manager and monitoring officer...")
        pm = User(name="Priya Mehta", email="pm@skillbridge.gov",
                  hashed_password=hash_password("pm123456"), role=UserRole.programme_manager)
        mo = User(name="Ravi Nair", email="monitor@skillbridge.gov",
                  hashed_password=hash_password("mo123456"), role=UserRole.monitoring_officer)
        db.add_all([pm, mo])
        db.flush()

        # ── Trainers ───────────────────────────────────────────────────────
        print("Creating trainers...")
        trainers = [
            User(name="Ankit Sharma", email="ankit@sunrise.edu",
                 hashed_password=hash_password("trainer123"), role=UserRole.trainer,
                 institution_id=inst1.id),
            User(name="Deepa Verma", email="deepa@sunrise.edu",
                 hashed_password=hash_password("trainer123"), role=UserRole.trainer,
                 institution_id=inst1.id),
            User(name="Kiran Rao", email="kiran@greenfield.edu",
                 hashed_password=hash_password("trainer123"), role=UserRole.trainer,
                 institution_id=inst2.id),
            User(name="Meena Pillai", email="meena@greenfield.edu",
                 hashed_password=hash_password("trainer123"), role=UserRole.trainer,
                 institution_id=inst2.id),
        ]
        db.add_all(trainers)
        db.flush()

        # ── Students ───────────────────────────────────────────────────────
        print("Creating 15 students...")
        student_data = [
            ("Aarav Patel", "aarav@student.sb"),
            ("Bhavna Singh", "bhavna@student.sb"),
            ("Chetan Kumar", "chetan@student.sb"),
            ("Divya Nair", "divya@student.sb"),
            ("Eshan Joshi", "eshan@student.sb"),
            ("Fatima Khan", "fatima@student.sb"),
            ("Ganesh Yadav", "ganesh@student.sb"),
            ("Harini Menon", "harini@student.sb"),
            ("Ishaan Gupta", "ishaan@student.sb"),
            ("Jaya Bose", "jaya@student.sb"),
            ("Karthik Reddy", "karthik@student.sb"),
            ("Lavanya Iyer", "lavanya@student.sb"),
            ("Manish Tiwari", "manish@student.sb"),
            ("Neha Chauhan", "neha@student.sb"),
            ("Omkar Desai", "omkar@student.sb"),
        ]
        students = [
            User(name=name, email=email,
                 hashed_password=hash_password("student123"), role=UserRole.student)
            for name, email in student_data
        ]
        db.add_all(students)
        db.flush()

        # ── Batches ────────────────────────────────────────────────────────
        print("Creating batches...")
        batch1 = Batch(name="Web Dev Batch A", institution_id=inst1.id)
        batch2 = Batch(name="Data Analytics Batch B", institution_id=inst1.id)
        batch3 = Batch(name="IoT Fundamentals Batch C", institution_id=inst2.id)
        db.add_all([batch1, batch2, batch3])
        db.flush()

        # ── Batch-Trainer Assignments ──────────────────────────────────────
        print("Assigning trainers to batches...")
        bt_assignments = [
            BatchTrainer(batch_id=batch1.id, trainer_id=trainers[0].id),  # Ankit -> Batch A
            BatchTrainer(batch_id=batch1.id, trainer_id=trainers[1].id),  # Deepa -> Batch A (co-trainer)
            BatchTrainer(batch_id=batch2.id, trainer_id=trainers[1].id),  # Deepa -> Batch B
            BatchTrainer(batch_id=batch3.id, trainer_id=trainers[2].id),  # Kiran -> Batch C
            BatchTrainer(batch_id=batch3.id, trainer_id=trainers[3].id),  # Meena -> Batch C (co-trainer)
        ]
        db.add_all(bt_assignments)
        db.flush()

        # ── Batch-Student Enrollments ──────────────────────────────────────
        print("Enrolling students...")
        # Batch A: students 0-5 (6 students)
        for s in students[0:6]:
            db.add(BatchStudent(batch_id=batch1.id, student_id=s.id))
        # Batch B: students 4-9 (6 students, overlap intentional)
        for s in students[4:10]:
            db.add(BatchStudent(batch_id=batch2.id, student_id=s.id))
        # Batch C: students 9-14 (6 students)
        for s in students[9:15]:
            db.add(BatchStudent(batch_id=batch3.id, student_id=s.id))
        db.flush()

        # ── Sessions ───────────────────────────────────────────────────────
        print("Creating 8 sessions...")
        today = date.today()
        sessions_data = [
            # Batch A - 3 sessions
            SessionModel(batch_id=batch1.id, trainer_id=trainers[0].id,
                         title="HTML & CSS Basics", date=today - timedelta(days=14),
                         start_time=time(9, 0), end_time=time(11, 0)),
            SessionModel(batch_id=batch1.id, trainer_id=trainers[0].id,
                         title="JavaScript Fundamentals", date=today - timedelta(days=7),
                         start_time=time(9, 0), end_time=time(11, 0)),
            SessionModel(batch_id=batch1.id, trainer_id=trainers[1].id,
                         title="React Introduction", date=today - timedelta(days=2),
                         start_time=time(14, 0), end_time=time(16, 0)),
            # Batch B - 3 sessions
            SessionModel(batch_id=batch2.id, trainer_id=trainers[1].id,
                         title="Python for Data Science", date=today - timedelta(days=12),
                         start_time=time(10, 0), end_time=time(12, 0)),
            SessionModel(batch_id=batch2.id, trainer_id=trainers[1].id,
                         title="Pandas & NumPy", date=today - timedelta(days=5),
                         start_time=time(10, 0), end_time=time(12, 0)),
            SessionModel(batch_id=batch2.id, trainer_id=trainers[1].id,
                         title="Data Visualisation", date=today - timedelta(days=1),
                         start_time=time(14, 0), end_time=time(16, 0)),
            # Batch C - 2 sessions
            SessionModel(batch_id=batch3.id, trainer_id=trainers[2].id,
                         title="IoT Sensors Overview", date=today - timedelta(days=10),
                         start_time=time(9, 0), end_time=time(11, 0)),
            SessionModel(batch_id=batch3.id, trainer_id=trainers[3].id,
                         title="MQTT Protocol", date=today - timedelta(days=3),
                         start_time=time(13, 0), end_time=time(15, 0)),
        ]
        db.add_all(sessions_data)
        db.flush()

        # ── Attendance Records ─────────────────────────────────────────────
        print("Marking attendance for all sessions...")

        def mark(session, student, status_val):
            db.add(Attendance(
                session_id=session.id,
                student_id=student.id,
                status=status_val,
                marked_at=datetime.combine(session.date, session.end_time, tzinfo=timezone.utc),
            ))

        # Batch A sessions (students 0-5)
        attendance_matrix_a = [
            # [present, present, present, late, present, absent]
            [AttendanceStatus.present, AttendanceStatus.present, AttendanceStatus.present,
             AttendanceStatus.late, AttendanceStatus.present, AttendanceStatus.absent],
            [AttendanceStatus.present, AttendanceStatus.late, AttendanceStatus.present,
             AttendanceStatus.present, AttendanceStatus.absent, AttendanceStatus.present],
            [AttendanceStatus.present, AttendanceStatus.present, AttendanceStatus.late,
             AttendanceStatus.present, AttendanceStatus.present, AttendanceStatus.present],
        ]
        for i, session in enumerate(sessions_data[0:3]):
            for j, student in enumerate(students[0:6]):
                mark(session, student, attendance_matrix_a[i][j])

        # Batch B sessions (students 4-9)
        for i, session in enumerate(sessions_data[3:6]):
            for j, student in enumerate(students[4:10]):
                status_val = AttendanceStatus.present if (i + j) % 4 != 0 else AttendanceStatus.absent
                mark(session, student, status_val)

        # Batch C sessions (students 9-14)
        for i, session in enumerate(sessions_data[6:8]):
            for j, student in enumerate(students[9:15]):
                if j == 0 and i == 0:
                    status_val = AttendanceStatus.late
                elif (i + j) % 5 == 0:
                    status_val = AttendanceStatus.absent
                else:
                    status_val = AttendanceStatus.present
                mark(session, student, status_val)

        db.commit()

        print("\n[OK] Seed complete!")
        # print("\n--- Test Accounts -------------------------------------------")
        # print(f"  Institution 1 : admin@sunrise.edu         / inst123")
        # print(f"  Institution 2 : admin@greenfield.edu      / inst123")
        # print(f"  Trainer 1     : ankit@sunrise.edu         / trainer123")
        # print(f"  Trainer 2     : deepa@sunrise.edu         / trainer123")
        # print(f"  Trainer 3     : kiran@greenfield.edu      / trainer123")
        # print(f"  Trainer 4     : meena@greenfield.edu      / trainer123")
        # print(f"  Student 1     : aarav@student.sb          / student123")
        # print(f"  Student 2     : bhavna@student.sb         / student123")
        # print(f"  Programme Mgr : pm@skillbridge.gov        / pm123456")
        # print(f"  Monitoring    : monitor@skillbridge.gov   / mo123456")
        # print(f"-------------------------------------------------------------")
        # print(f"\n  Batches: {batch1.id} (Web Dev A), {batch2.id} (Data Analytics B), {batch3.id} (IoT C)")
        # print(f"  Sessions: {[s.id for s in sessions_data]}")

    except Exception as e:
        db.rollback()
        print(f"[FAIL] Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
