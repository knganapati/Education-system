from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession
from src.database import get_db
from src.models import User, UserRole, Batch, BatchTrainer, BatchStudent, Session as SessionModel
from src.schemas import SessionCreateRequest, SessionResponse, AttendanceListItem
from src.dependencies import get_current_user, PermissionChecker

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: SessionCreateRequest,
    current_user: User = Depends(PermissionChecker("create_session")),
    db: DBSession = Depends(get_db),
):
    """Create a training session. Trainer only."""
    # Validate batch exists
    batch = db.query(Batch).filter(Batch.id == payload.batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch with id {payload.batch_id} not found.",
        )

    # Verify trainer belongs to this batch
    assignment = db.query(BatchTrainer).filter(
        BatchTrainer.batch_id == payload.batch_id,
        BatchTrainer.trainer_id == current_user.id,
    ).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned as a trainer for this batch.",
        )

    # Validate time ordering
    if payload.end_time <= payload.start_time:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_time must be after start_time.",
        )

    session = SessionModel(
        batch_id=payload.batch_id,
        trainer_id=current_user.id,
        title=payload.title,
        date=payload.date,
        start_time=payload.start_time,
        end_time=payload.end_time,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/{session_id}/attendance", response_model=list[AttendanceListItem])
def get_session_attendance(
    session_id: int,
    current_user: User = Depends(PermissionChecker("manage_batch")),
    db: DBSession = Depends(get_db),
):
    """Get full attendance list for a session. Trainer only."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with id {session_id} not found.",
        )

    # Verify trainer owns this session or is assigned to the batch
    assignment = db.query(BatchTrainer).filter(
        BatchTrainer.batch_id == session.batch_id,
        BatchTrainer.trainer_id == current_user.id,
    ).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned as a trainer for this batch.",
        )

    result = []
    for record in session.attendance:
        result.append(AttendanceListItem(
            student_id=record.student.id,
            student_name=record.student.name,
            student_email=record.student.email,
            status=record.status,
            marked_at=record.marked_at,
        ))

    return result
