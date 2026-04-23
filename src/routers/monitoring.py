from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session as DBSession
from src.database import get_db
from src.models import User, Attendance, Session as SessionModel, Batch
from src.schemas import MonitoringAttendanceResponse, MonitoringAttendanceRecord
from src.dependencies import get_monitoring_user

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/attendance", response_model=MonitoringAttendanceResponse)
def get_monitoring_attendance(
    current_user: User = Depends(get_monitoring_user),
    db: DBSession = Depends(get_db),
):
    """
    Read-only attendance view across the full programme.
    Requires a monitoring-scoped token (obtained from POST /auth/monitoring-token).
    """
    records = db.query(Attendance).all()
    result = []

    for rec in records:
        session = rec.session
        batch = session.batch
        institution = batch.institution
        trainer = session.trainer

        result.append(MonitoringAttendanceRecord(
            attendance_id=rec.id,
            session_id=session.id,
            session_title=session.title,
            session_date=session.date,
            batch_id=batch.id,
            batch_name=batch.name,
            student_id=rec.student.id,
            student_name=rec.student.name,
            trainer_id=trainer.id,
            trainer_name=trainer.name,
            institution_id=institution.id,
            institution_name=institution.name,
            status=rec.status,
            marked_at=rec.marked_at,
        ))

    return MonitoringAttendanceResponse(total_records=len(result), records=result)


# ─── 405 for all non-GET methods on /monitoring/attendance ───────────────────

@router.post("/attendance", include_in_schema=False)
async def monitoring_post_not_allowed():
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="Method Not Allowed. Only GET is permitted on /monitoring/attendance.",
    )


@router.put("/attendance", include_in_schema=False)
async def monitoring_put_not_allowed():
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="Method Not Allowed. Only GET is permitted on /monitoring/attendance.",
    )


@router.delete("/attendance", include_in_schema=False)
async def monitoring_delete_not_allowed():
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="Method Not Allowed. Only GET is permitted on /monitoring/attendance.",
    )


@router.patch("/attendance", include_in_schema=False)
async def monitoring_patch_not_allowed():
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="Method Not Allowed. Only GET is permitted on /monitoring/attendance.",
    )
