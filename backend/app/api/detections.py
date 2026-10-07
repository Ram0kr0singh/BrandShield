from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database.session import get_db
from app.detection.engine import analyze_app_candidate, analyze_social_candidate, scan_all
from app.detection.normalization import analyze_name
from app.models import Detection
from app.schemas import DetectionRead, NameAnalysisRead, NameAnalysisRequest, ScanRead

router = APIRouter(tags=["detections"])


def _not_found(error: LookupError) -> HTTPException:
    return HTTPException(status_code=404, detail=str(error))


@router.post("/analyze/name", response_model=NameAnalysisRead)
def analyze_name_endpoint(payload: NameAnalysisRequest) -> dict:
    return analyze_name(payload.official_name, payload.candidate_name).as_dict()


@router.post("/analyze/social/{candidate_id}", response_model=DetectionRead)
def analyze_social(candidate_id: UUID, db: Session = Depends(get_db)) -> Detection:
    try:
        return analyze_social_candidate(db, candidate_id)
    except LookupError as error:
        raise _not_found(error) from error


@router.post("/analyze/app/{candidate_id}", response_model=DetectionRead)
def analyze_app(candidate_id: UUID, db: Session = Depends(get_db)) -> Detection:
    try:
        return analyze_app_candidate(db, candidate_id)
    except LookupError as error:
        raise _not_found(error) from error


@router.post("/detections/scan", response_model=ScanRead)
def scan(db: Session = Depends(get_db)) -> ScanRead:
    detections = scan_all(db)
    by_severity: dict[str, int] = {}
    for detection in detections:
        by_severity[detection.severity.value] = by_severity.get(detection.severity.value, 0) + 1
    return ScanRead(analyzed=len(detections), created_or_updated=len(detections), by_severity=by_severity)


@router.get("/detections", response_model=list[DetectionRead])
def list_detections(db: Session = Depends(get_db)) -> list[Detection]:
    return list(db.scalars(select(Detection).options(selectinload(Detection.evidence)).order_by(Detection.detected_at.desc())))


@router.get("/detections/{detection_id}", response_model=DetectionRead)
def get_detection(detection_id: UUID, db: Session = Depends(get_db)) -> Detection:
    detection = db.scalar(select(Detection).options(selectinload(Detection.evidence)).where(Detection.id == detection_id))
    if detection is None:
        raise HTTPException(status_code=404, detail="Detection not found")
    return detection
