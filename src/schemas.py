from datetime import datetime, date as date_type, time as time_type
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from src.models import UserRole, AttendanceStatus


# ─── Auth Schemas ─────────────────────────────────────────────

class SignupRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Full name")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=6, max_length=128, description="Password (min 6 chars)")
    role: UserRole = Field(..., description="User role")
    institution_id: Optional[int] = Field(None, description="Institution ID (for trainers/students)")


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=1, description="Password")


class MonitoringTokenRequest(BaseModel):
    key: str = Field(..., description="Monitoring API key")


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int


class OTPRequest(BaseModel):
    email: EmailStr = Field(..., description="Email to send OTP to")


class OTPVerifyRequest(BaseModel):
    email: EmailStr = Field(..., description="Email for verification")
    otp_code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")



# ─── User Schemas ─────────────────────────────────────────────

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    institution_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Batch Schemas ────────────────────────────────────────────

class BatchCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Batch name")
    institution_id: int = Field(..., description="Institution ID this batch belongs to")
    trainer_ids: Optional[List[int]] = Field(None, description="Optional list of trainer IDs to assign")


class BatchResponse(BaseModel):
    id: int
    name: str
    institution_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class BatchInviteResponse(BaseModel):
    id: int
    batch_id: int
    token: str
    expires_at: datetime
    used: bool

    class Config:
        from_attributes = True


class BatchJoinRequest(BaseModel):
    token: str = Field(..., description="Invite token to join a batch")


# ─── Session Schemas ──────────────────────────────────────────

class SessionCreateRequest(BaseModel):
    batch_id: int = Field(..., description="Batch ID for this session")
    title: str = Field(..., min_length=1, max_length=255, description="Session title")
    date: date_type = Field(..., description="Session date (YYYY-MM-DD)")
    start_time: time_type = Field(..., description="Start time (HH:MM)")
    end_time: time_type = Field(..., description="End time (HH:MM)")


class SessionResponse(BaseModel):
    id: int
    batch_id: int
    trainer_id: int
    title: str
    date: date_type
    start_time: time_type
    end_time: time_type
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Attendance Schemas ───────────────────────────────────────

class AttendanceMarkRequest(BaseModel):
    session_id: int = Field(..., description="Session ID to mark attendance for")
    status: AttendanceStatus = Field(..., description="Attendance status: present, absent, or late")


class AttendanceResponse(BaseModel):
    id: int
    session_id: int
    student_id: int
    status: AttendanceStatus
    marked_at: datetime
    student_name: Optional[str] = None

    class Config:
        from_attributes = True


class AttendanceListItem(BaseModel):
    student_id: int
    student_name: str
    student_email: str
    status: AttendanceStatus
    marked_at: datetime


# ─── Summary Schemas ──────────────────────────────────────────

class BatchSummaryResponse(BaseModel):
    batch_id: int
    batch_name: str
    total_students: int
    total_sessions: int
    attendance_rate: float
    sessions: List[dict] = []


class InstitutionSummaryResponse(BaseModel):
    institution_id: int
    institution_name: str
    total_batches: int
    total_students: int
    total_sessions: int
    overall_attendance_rate: float
    batches: List[BatchSummaryResponse] = []


class ProgrammeSummaryResponse(BaseModel):
    total_institutions: int
    total_batches: int
    total_students: int
    total_sessions: int
    overall_attendance_rate: float
    institutions: List[InstitutionSummaryResponse] = []


# ─── Monitoring Schemas ───────────────────────────────────────

class MonitoringAttendanceRecord(BaseModel):
    attendance_id: int
    session_id: int
    session_title: str
    session_date: date_type
    batch_id: int
    batch_name: str
    student_id: int
    student_name: str
    trainer_id: int
    trainer_name: str
    institution_id: int
    institution_name: str
    status: AttendanceStatus
    marked_at: datetime


class MonitoringAttendanceResponse(BaseModel):
    total_records: int
    records: List[MonitoringAttendanceRecord]


# ─── Error Schemas ────────────────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str


# ─── Personalized Dashboards ──────────────────────────────────

class StudentStatsResponse(BaseModel):
    total_batches: int
    total_sessions: int
    attendance_rate: float
    enrolled_batches: List[BatchResponse]


class TrainerStatsResponse(BaseModel):
    total_batches: int
    total_students: int
    total_sessions_conducted: int
    assigned_batches: List[BatchResponse]

