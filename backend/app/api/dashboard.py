from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database.session import get_db
from app.models import AppCandidate, Brand, Detection, DetectionCandidateType, MonitoringRun, Severity, SocialCandidate
from app.schemas import DashboardOverview

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _candidate(detection: Detection, db: Session) -> dict:
    if detection.candidate_type == DetectionCandidateType.SOCIAL:
        item = db.get(SocialCandidate, detection.candidate_id)
        return {"name": item.display_name or item.handle if item else "Unknown candidate", "source": "Social Media", "publisher": None}
    item = db.get(AppCandidate, detection.candidate_id)
    return {"name": item.app_name if item else "Unknown candidate", "source": "App Store", "publisher": item.developer_name if item else None}


@router.get("/overview", response_model=DashboardOverview)
def overview(brand_id: UUID | None = None, db: Session = Depends(get_db)) -> dict:
    brand = db.get(Brand, brand_id) if brand_id else db.scalar(select(Brand).order_by(Brand.name))
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")
    detections = list(db.scalars(select(Detection).options(selectinload(Detection.evidence)).where(Detection.brand_id == brand.id).order_by(Detection.detected_at.desc())))
    social_count = len(list(db.scalars(select(SocialCandidate.id).where(SocialCandidate.brand_id == brand.id))))
    app_count = len(list(db.scalars(select(AppCandidate.id).where(AppCandidate.brand_id == brand.id))))
    counts = {severity.value: sum(item.severity == severity for item in detections) for severity in Severity}
    threats = [item for item in detections if item.severity != Severity.SAFE]
    types: dict[str, int] = {}
    for item in threats:
        if item.threat_type:
            types[item.threat_type.value] = types.get(item.threat_type.value, 0) + 1
    recent = []
    for item in threats[:8]:
        recent.append({"id": str(item.id), **_candidate(item, db), "threat_type": item.threat_type.value if item.threat_type else None, "risk_score": item.risk_score, "severity": item.severity.value, "status": item.status.value, "detected_at": item.detected_at.isoformat()})
    last = db.scalar(select(MonitoringRun).where(MonitoringRun.brand_id == brand.id).order_by(MonitoringRun.created_at.desc()))
    return {"brand": {"id": str(brand.id), "name": brand.name}, "summary": {"protected_brands": 1, "total_candidates": social_count + app_count, "total_detections": len(detections), "detected_threats": len(threats), "high_risk": counts["HIGH"] + counts["CRITICAL"], "lookalikes": sum(item.lookalike_detected for item in detections), "safe": counts["SAFE"], "low_risk": counts["LOW"], "medium_risk": counts["MEDIUM"]}, "risk_distribution": [{"severity": severity.value, "count": counts[severity.value]} for severity in Severity], "source_distribution": [{"source": "Social Media", "count": social_count}, {"source": "App Stores", "count": app_count}], "threat_type_distribution": [{"threat_type": name, "count": count} for name, count in types.items()], "recent_threats": recent, "last_scan": {"id": str(last.id), "status": last.status.value, "completed_at": last.completed_at.isoformat() if last.completed_at else None, "candidate_count": last.candidate_count} if last else None}
