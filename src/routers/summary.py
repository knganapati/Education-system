from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func
from src.database import get_db
from src.models import User, UserRole, Batch, BatchStudent, BatchTrainer, Session as SessionModel, Attendance
from src.schemas import (
    BatchSummaryResponse, InstitutionSummaryResponse, ProgrammeSummaryResponse,
    StudentStatsResponse, TrainerStatsResponse, BatchResponse
)
from src.dependencies import RoleChecker

router = APIRouter(tags=["Summaries"])


def _compute_batch_summary(batch: Batch, db: DBSession) -> BatchSummaryResponse:
    """Compute attendance summary for a single batch."""
    total_students = db.query(BatchStudent).filter(BatchStudent.batch_id == batch.id).count()
    total_sessions = len(batch.sessions)

    total_possible = 0
    total_present = 0
    sessions_data = []

    for session in batch.sessions:
        session_student_count = total_students
        session_present = db.query(Attendance).filter(
            Attendance.session_id == session.id,
            Attendance.status.in_(["present", "late"]),
        ).count()
        total_possible += session_student_count
        total_present += session_present

        sessions_data.append({
            "session_id": session.id,
            "title": session.title,
            "date": str(session.date),
            "present_count": session_present,
            "total_students": session_student_count,
        })

    rate = (total_present / total_possible * 100) if total_possible > 0 else 0.0

    return BatchSummaryResponse(
        batch_id=batch.id,
        batch_name=batch.name,
        total_students=total_students,
        total_sessions=total_sessions,
        attendance_rate=round(rate, 2),
        sessions=sessions_data,
    )


@router.get("/batches/{batch_id}/summary", response_model=BatchSummaryResponse)
def get_batch_summary(
    batch_id: int,
    current_user: User = Depends(RoleChecker([UserRole.institution, UserRole.programme_manager])),
    db: DBSession = Depends(get_db),
):
    """Attendance summary for a batch. Institution and Programme Manager only."""
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Batch {batch_id} not found.")

    # Institution can only see their own batches
    if current_user.role == UserRole.institution and batch.institution_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only view summaries for your own batches.")

    return _compute_batch_summary(batch, db)


@router.get("/institutions/{institution_id}/summary", response_model=InstitutionSummaryResponse)
def get_institution_summary(
    institution_id: int,
    current_user: User = Depends(RoleChecker([UserRole.programme_manager])),
    db: DBSession = Depends(get_db),
):
    """Summary across all batches in an institution. Programme Manager only."""
    institution = db.query(User).filter(
        User.id == institution_id,
        User.role == UserRole.institution,
    ).first()
    if not institution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Institution {institution_id} not found.")

    batches = db.query(Batch).filter(Batch.institution_id == institution_id).all()
    batch_summaries = [_compute_batch_summary(b, db) for b in batches]

    total_students = sum(s.total_students for s in batch_summaries)
    total_sessions = sum(s.total_sessions for s in batch_summaries)

    # Weighted average attendance rate
    if batch_summaries:
        weighted_rates = [s.attendance_rate * s.total_sessions for s in batch_summaries]
        overall_rate = sum(weighted_rates) / total_sessions if total_sessions > 0 else 0.0
    else:
        overall_rate = 0.0

    return InstitutionSummaryResponse(
        institution_id=institution.id,
        institution_name=institution.name,
        total_batches=len(batches),
        total_students=total_students,
        total_sessions=total_sessions,
        overall_attendance_rate=round(overall_rate, 2),
        batches=batch_summaries,
    )


@router.get("/programme/summary", response_model=ProgrammeSummaryResponse)
def get_programme_summary(
    current_user: User = Depends(RoleChecker([UserRole.programme_manager])),
    db: DBSession = Depends(get_db),
):
    """Programme-wide summary across all institutions. Programme Manager only."""
    institutions = db.query(User).filter(User.role == UserRole.institution).all()
    institution_summaries = []

    for inst in institutions:
        batches = db.query(Batch).filter(Batch.institution_id == inst.id).all()
        batch_summaries = [_compute_batch_summary(b, db) for b in batches]

        inst_total_students = sum(s.total_students for s in batch_summaries)
        inst_total_sessions = sum(s.total_sessions for s in batch_summaries)
        weighted = [s.attendance_rate * s.total_sessions for s in batch_summaries]
        inst_rate = sum(weighted) / inst_total_sessions if inst_total_sessions > 0 else 0.0

        institution_summaries.append(InstitutionSummaryResponse(
            institution_id=inst.id,
            institution_name=inst.name,
            total_batches=len(batches),
            total_students=inst_total_students,
            total_sessions=inst_total_sessions,
            overall_attendance_rate=round(inst_rate, 2),
            batches=batch_summaries,
        ))

    total_batches = db.query(Batch).count()
    total_students = db.query(BatchStudent.student_id).distinct().count()
    total_sessions = db.query(SessionModel).count()

    all_sessions = sum(s.total_sessions for s in institution_summaries)
    weighted_overall = [
        s.overall_attendance_rate * s.total_sessions for s in institution_summaries
    ]
    overall_rate = sum(weighted_overall) / all_sessions if all_sessions > 0 else 0.0

    return ProgrammeSummaryResponse(
        total_institutions=len(institutions),
        total_batches=total_batches,
        total_students=total_students,
        total_sessions=total_sessions,
        overall_attendance_rate=round(overall_rate, 2),
        institutions=institution_summaries,
    )


@router.get("/students/me/stats", response_model=StudentStatsResponse)
def get_student_stats(
    current_user: User = Depends(RoleChecker([UserRole.student])),
    db: DBSession = Depends(get_db),
):
    """Fetch real-time stats for the logged-in student."""
    enrolled = db.query(BatchStudent).filter(BatchStudent.student_id == current_user.id).all()
    batch_ids = [e.batch_id for e in enrolled]
    
    batches = db.query(Batch).filter(Batch.id.in_(batch_ids)).all() if batch_ids else []
    
    # Calculate attendance rate
    total_sessions = db.query(SessionModel).filter(SessionModel.batch_id.in_(batch_ids)).count() if batch_ids else 0
    attendance_count = db.query(Attendance).filter(
        Attendance.student_id == current_user.id,
        Attendance.status.in_(["present", "late"])
    ).count()
    
    rate = (attendance_count / total_sessions * 100) if total_sessions > 0 else 0.0
    
    return StudentStatsResponse(
        total_batches=len(batches),
        total_sessions=total_sessions,
        attendance_rate=round(rate, 2),
        enrolled_batches=[BatchResponse.model_validate(b) for b in batches]
    )


@router.get("/trainers/me/stats", response_model=TrainerStatsResponse)
def get_trainer_stats(
    current_user: User = Depends(RoleChecker([UserRole.trainer])),
    db: DBSession = Depends(get_db),
):
    """Fetch real-time stats for the logged-in trainer."""
    assignments = db.query(BatchTrainer).filter(BatchTrainer.trainer_id == current_user.id).all()
    batch_ids = [a.batch_id for a in assignments]
    
    batches = db.query(Batch).filter(Batch.id.in_(batch_ids)).all() if batch_ids else []
    
    # Total students across their batches
    total_students = db.query(BatchStudent).filter(BatchStudent.batch_id.in_(batch_ids)).count() if batch_ids else 0
    total_sessions = db.query(SessionModel).filter(SessionModel.trainer_id == current_user.id).count()

    return TrainerStatsResponse(
        total_batches=len(batches),
        total_students=total_students,
        total_sessions_conducted=total_sessions,
        assigned_batches=[BatchResponse.model_validate(b) for b in batches]
    )

