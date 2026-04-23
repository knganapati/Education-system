import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession
from src.database import get_db
from src.models import User, UserRole, Batch, BatchTrainer, BatchStudent, BatchInvite
from src.schemas import (
    BatchCreateRequest, BatchResponse, BatchInviteResponse, BatchJoinRequest
)
from src.dependencies import get_current_user, PermissionChecker

router = APIRouter(prefix="/batches", tags=["Batches"])


@router.post("", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
def create_batch(
    payload: BatchCreateRequest,
    current_user: User = Depends(PermissionChecker("manage_batch")),
    db: DBSession = Depends(get_db),
):
    """Create a new batch. Trainers and institution admins can create batches."""
    # Validate institution exists
    institution = db.query(User).filter(
        User.id == payload.institution_id,
        User.role == UserRole.institution,
    ).first()
    if not institution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Institution with id {payload.institution_id} not found.",
        )

    batch = Batch(name=payload.name, institution_id=payload.institution_id)
    db.add(batch)
    db.flush()  # Get batch.id before commit

    # Auto-assign trainer if current user is a trainer
    if current_user.role == UserRole.trainer:
        db.add(BatchTrainer(batch_id=batch.id, trainer_id=current_user.id))

    # Assign additional trainers if specified
    if payload.trainer_ids:
        for tid in payload.trainer_ids:
            trainer = db.query(User).filter(User.id == tid, User.role == UserRole.trainer).first()
            if not trainer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Trainer with id {tid} not found.",
                )
            # Avoid duplicate for the current user
            if tid != current_user.id:
                db.add(BatchTrainer(batch_id=batch.id, trainer_id=tid))

    db.commit()
    db.refresh(batch)
    return batch


@router.post("/{batch_id}/invite", response_model=BatchInviteResponse, status_code=status.HTTP_201_CREATED)
def create_invite(
    batch_id: int,
    current_user: User = Depends(PermissionChecker("manage_batch")),
    db: DBSession = Depends(get_db),
):
    """Generate an invite token for a batch. Trainer only."""
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Batch {batch_id} not found.")

    # Verify trainer is assigned to this batch
    assignment = db.query(BatchTrainer).filter(
        BatchTrainer.batch_id == batch_id,
        BatchTrainer.trainer_id == current_user.id,
    ).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned as a trainer for this batch.",
        )

    invite = BatchInvite(
        batch_id=batch_id,
        token=secrets.token_urlsafe(32),
        created_by=current_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        used=False,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


@router.post("/join", status_code=status.HTTP_200_OK)
def join_batch(
    payload: BatchJoinRequest,
    current_user: User = Depends(PermissionChecker("join_batch")),
    db: DBSession = Depends(get_db),
):
    """Join a batch using an invite token. Student only."""
    invite = db.query(BatchInvite).filter(BatchInvite.token == payload.token).first()
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite token not found.")

    if invite.used:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="This invite token has already been used.")

    if invite.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invite token has expired.")

    # Check if student is already enrolled
    existing = db.query(BatchStudent).filter(
        BatchStudent.batch_id == invite.batch_id,
        BatchStudent.student_id == current_user.id,
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="You are already enrolled in this batch.")

    db.add(BatchStudent(batch_id=invite.batch_id, student_id=current_user.id))

    # Mark invite as used (single-use tokens for security)
    invite.used = True
    db.commit()

    return {"message": f"Successfully joined batch {invite.batch_id}.", "batch_id": invite.batch_id}
