from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session as DBSession
from src.database import get_db
from src.models import User, UserRole, BatchStudent, Session as SessionModel, Attendance
from src.schemas import AttendanceMarkRequest, AttendanceResponse
from src.dependencies import PermissionChecker

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.post("/mark", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
def mark_attendance(
    payload: AttendanceMarkRequest,
    current_user: User = Depends(PermissionChecker("mark_attendance")),

    db: DBSession = Depends(get_db),
):
    """Mark attendance for a session. Student only — marks their own attendance."""
    # Validate session exists
    session = db.query(SessionModel).filter(SessionModel.id == payload.session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with id {payload.session_id} not found.",
        )

    # Validate student is enrolled in the batch for this session
    enrolled = db.query(BatchStudent).filter(
        BatchStudent.batch_id == session.batch_id,
        BatchStudent.student_id == current_user.id,
    ).first()
    if not enrolled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in the batch for this session.",
        )

    # Check if attendance already marked
    existing = db.query(Attendance).filter(
        Attendance.session_id == payload.session_id,
        Attendance.student_id == current_user.id,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Attendance has already been marked for this session.",
        )

    record = Attendance(
        session_id=payload.session_id,
        student_id=current_user.id,
        status=payload.status,
        marked_at=datetime.now(timezone.utc),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# Block all non-GET methods on /monitoring/attendance
# (Handled in monitoring router but also enforced here as a precaution)
@router.post("/monitoring", include_in_schema=False)
@router.put("/monitoring", include_in_schema=False)
@router.delete("/monitoring", include_in_schema=False)
@router.patch("/monitoring", include_in_schema=False)
def monitoring_not_allowed():
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="Method Not Allowed. Only GET is permitted on this endpoint.",
    )
