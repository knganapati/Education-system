import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Date, Time,
    ForeignKey, Enum as SQLEnum, func
)
from sqlalchemy.orm import relationship
from src.database import Base


class UserRole(str, enum.Enum):
    """Enumeration of all user roles in the SkillBridge system."""
    student = "student"
    trainer = "trainer"
    institution = "institution"
    programme_manager = "programme_manager"
    monitoring_officer = "monitoring_officer"


class AttendanceStatus(str, enum.Enum):
    """Enumeration of attendance statuses."""
    present = "present"
    absent = "absent"
    late = "late"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    institution_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    institution = relationship("User", remote_side=[id], backref="members")
    trained_batches = relationship("BatchTrainer", back_populates="trainer")
    enrolled_batches = relationship("BatchStudent", back_populates="student")
    created_sessions = relationship("Session", back_populates="trainer")
    attendance_records = relationship("Attendance", back_populates="student")


class Batch(Base):
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    institution_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    institution = relationship("User", foreign_keys=[institution_id])
    trainers = relationship("BatchTrainer", back_populates="batch", cascade="all, delete-orphan")
    students = relationship("BatchStudent", back_populates="batch", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="batch", cascade="all, delete-orphan")
    invites = relationship("BatchInvite", back_populates="batch", cascade="all, delete-orphan")


class BatchTrainer(Base):
    __tablename__ = "batch_trainers"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("batches.id", ondelete="CASCADE"), nullable=False)
    trainer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    batch = relationship("Batch", back_populates="trainers")
    trainer = relationship("User", back_populates="trained_batches")


class BatchStudent(Base):
    __tablename__ = "batch_students"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("batches.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    batch = relationship("Batch", back_populates="students")
    student = relationship("User", back_populates="enrolled_batches")


class BatchInvite(Base):
    __tablename__ = "batch_invites"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("batches.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False, nullable=False)

    # Relationships
    batch = relationship("Batch", back_populates="invites")
    creator = relationship("User", foreign_keys=[created_by])


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("batches.id", ondelete="CASCADE"), nullable=False)
    trainer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    batch = relationship("Batch", back_populates="sessions")
    trainer = relationship("User", back_populates="created_sessions")
    attendance = relationship("Attendance", back_populates="session", cascade="all, delete-orphan")


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(SQLEnum(AttendanceStatus), nullable=False)
    marked_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    session = relationship("Session", back_populates="attendance")
    student = relationship("User", back_populates="attendance_records")





