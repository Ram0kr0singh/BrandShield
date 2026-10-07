from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.detection.engine import scan_all
from app.models import AppCandidate, Brand, Detection, MonitoringRun, MonitoringRunStatus, Severity, SocialCandidate
from app.schemas import MonitoringRunRead, MonitoringScanRequest

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


def _summary(run: MonitoringRun) -> MonitoringRunRead:
    return MonitoringRunRead.model_validate(run)


@router.post("/scan", response_model=MonitoringRunRead)
def scan(payload: MonitoringScanRequest, db: Session = Depends(get_db)) -> MonitoringRun:
    if db.get(Brand, payload.brand_id) is None:
        raise HTTPException(status_code=404, detail="Brand not found")
    social_count = len(list(db.scalars(select(SocialCandidate.id).where(SocialCandidate.brand_id == payload.brand_id))))
    app_count = len(list(db.scalars(select(AppCandidate.id).where(AppCandidate.brand_id == payload.brand_id))))
    run = MonitoringRun(brand_id=payload.brand_id, status=MonitoringRunStatus.RUNNING, candidate_count=social_count + app_count, social_candidate_count=social_count, app_candidate_count=app_count)
    db.add(run)
    db.commit()
    try:
        detections = scan_all(db, payload.brand_id)
        counts = {severity: 0 for severity in Severity}
        for detection in detections:
            counts[detection.severity] += 1
        run.status = MonitoringRunStatus.COMPLETED
        run.completed_at = datetime.now(timezone.utc)
        run.safe_count = counts[Severity.SAFE]
        run.low_count = counts[Severity.LOW]
        run.medium_count = counts[Severity.MEDIUM]
        run.high_count = counts[Severity.HIGH]
        run.critical_count = counts[Severity.CRITICAL]
        db.commit()
        db.refresh(run)
        return run
    except Exception:
        run.status = MonitoringRunStatus.FAILED
        run.completed_at = datetime.now(timezone.utc)
        db.commit()
        raise


@router.get("/runs", response_model=list[MonitoringRunRead])
def list_runs(brand_id: UUID | None = None, limit: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_db)) -> list[MonitoringRun]:
    statement = select(MonitoringRun).order_by(MonitoringRun.created_at.desc()).limit(limit)
    if brand_id is not None:
        statement = statement.where(MonitoringRun.brand_id == brand_id)
    return list(db.scalars(statement))


@router.get("/runs/{run_id}", response_model=MonitoringRunRead)
def get_run(run_id: UUID, db: Session = Depends(get_db)) -> MonitoringRun:
    run = db.get(MonitoringRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Monitoring run not found")
    return run
