from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database.session import get_db
from app.models import (AppCandidate, Brand, Detection, DetectionCandidateType, DetectionStatus,
                        InvestigationActivity, InvestigationEventType, InvestigationNote,
                        RemediationDraft, RemediationDraftType, SocialCandidate)
from app.schemas import (InvestigationRead, NoteCreate, RemediationDraftCreate,
                         RemediationDraftRead, StatusUpdate)

router = APIRouter(prefix="/detections", tags=["investigations"])
ACTOR = "local-demo-analyst"
TRANSITIONS = {
    DetectionStatus.NEW: {DetectionStatus.INVESTIGATING, DetectionStatus.CONFIRMED_THREAT, DetectionStatus.FALSE_POSITIVE, DetectionStatus.DISMISSED},
    DetectionStatus.INVESTIGATING: {DetectionStatus.NEW, DetectionStatus.CONFIRMED_THREAT, DetectionStatus.FALSE_POSITIVE, DetectionStatus.DISMISSED},
    DetectionStatus.CONFIRMED_THREAT: {DetectionStatus.INVESTIGATING, DetectionStatus.DISMISSED},
    DetectionStatus.FALSE_POSITIVE: {DetectionStatus.INVESTIGATING},
    DetectionStatus.DISMISSED: {DetectionStatus.INVESTIGATING},
}

def _detection(detection_id: UUID, db: Session) -> Detection:
    item = db.scalar(select(Detection).options(selectinload(Detection.evidence), selectinload(Detection.notes), selectinload(Detection.activity), selectinload(Detection.remediation_drafts)).where(Detection.id == detection_id))
    if item is None:
        raise HTTPException(status_code=404, detail="Detection not found")
    return item

def _activity(detection_id: UUID, event_type: InvestigationEventType, **values: object) -> InvestigationActivity:
    return InvestigationActivity(detection_id=detection_id, event_type=event_type, actor=ACTOR, previous_value=values.get("previous_value"), new_value=values.get("new_value"), details=values.get("details", {}))

def _read(item: Detection) -> dict:
    return {"detection_id": item.id, "status": item.status, "notes": item.notes, "activity": item.activity, "drafts": item.remediation_drafts}

def _ensure_created(item: Detection, db: Session) -> None:
    exists = db.scalar(select(InvestigationActivity.id).where(InvestigationActivity.detection_id == item.id, InvestigationActivity.event_type == InvestigationEventType.INVESTIGATION_CREATED))
    if exists is None:
        db.add(_activity(item.id, InvestigationEventType.INVESTIGATION_CREATED, new_value=item.status.value, details={"source": "persisted detection"}))

@router.get("/{detection_id}/investigation", response_model=InvestigationRead)
def get_investigation(detection_id: UUID, db: Session = Depends(get_db)) -> dict:
    return _read(_detection(detection_id, db))

@router.post("/{detection_id}/status", response_model=InvestigationRead)
def update_status(detection_id: UUID, payload: StatusUpdate, db: Session = Depends(get_db)) -> dict:
    item = _detection(detection_id, db)
    _ensure_created(item, db)
    if payload.status == item.status:
        return _read(item)
    if payload.status not in TRANSITIONS[item.status]:
        raise HTTPException(status_code=422, detail=f"Invalid status transition: {item.status.value} to {payload.status.value}")
    previous = item.status
    item.status = payload.status
    db.add(_activity(item.id, InvestigationEventType.STATUS_CHANGED, previous_value=previous.value, new_value=payload.status.value))
    db.commit()
    return _read(_detection(detection_id, db))

@router.post("/{detection_id}/notes", response_model=InvestigationRead)
def add_note(detection_id: UUID, payload: NoteCreate, db: Session = Depends(get_db)) -> dict:
    item = _detection(detection_id, db)
    _ensure_created(item, db)
    note = InvestigationNote(detection_id=item.id, content=payload.content, actor=ACTOR)
    db.add(note)
    # Allocate the UUID before recording it in the audit event.  Without this
    # flush, the activity log can incorrectly persist the literal "None".
    db.flush()
    db.add(_activity(item.id, InvestigationEventType.NOTE_ADDED, details={"note_id": str(note.id)}))
    db.commit()
    return _read(_detection(detection_id, db))

def _candidate(item: Detection, db: Session) -> tuple[object | None, str]:
    if item.candidate_type == DetectionCandidateType.SOCIAL:
        return db.get(SocialCandidate, item.candidate_id), "social"
    return db.get(AppCandidate, item.candidate_id), "app"

def _draft_content(item: Detection, kind: RemediationDraftType, db: Session) -> tuple[str, list[str]]:
    candidate, source = _candidate(item, db)
    brand = db.get(Brand, item.brand_id)
    if candidate is None or brand is None:
        raise HTTPException(status_code=422, detail="Persisted candidate or brand data is unavailable")
    if kind == RemediationDraftType.APP_STORE and source != "app":
        raise HTTPException(status_code=422, detail="APP_STORE drafts require an app detection")
    if kind == RemediationDraftType.SOCIAL_PLATFORM and source != "social":
        raise HTTPException(status_code=422, detail="SOCIAL_PLATFORM drafts require a social detection")
    name = candidate.app_name if source == "app" else (candidate.display_name or candidate.handle)
    url = candidate.store_url if source == "app" else candidate.profile_url
    publisher = candidate.developer_name if source == "app" else None
    evidence = [e.signal_type.replace("_", " ") for e in item.evidence if e.available]
    facts = [f"Protected brand: {brand.name}", f"Candidate: {name}", f"Source URL: {url}", f"Risk score: {item.risk_score:.2f}", f"Severity: {item.severity.value}"]
    if publisher:
        facts.append(f"Publisher/developer: {publisher}")
    if item.threat_type:
        facts.append(f"Detection classification: {item.threat_type.value.replace('_', ' ')}")
    facts.append("Evidence signals: " + (", ".join(evidence) if evidence else "Unavailable"))
    conclusion = "Please review this report and take appropriate action under your applicable impersonation or trademark policy."
    content = "DRAFT ONLY — NOT SENT\n\nRemediation notice template\n\n" + "\n".join(facts) + "\n\n" + conclusion + " This is an analyst draft based on persisted deterministic evidence; it does not assert confirmed malicious activity unless separately investigated."
    return content, evidence

@router.post("/{detection_id}/remediation-drafts", response_model=RemediationDraftRead)
def generate_draft(detection_id: UUID, payload: RemediationDraftCreate, db: Session = Depends(get_db)) -> RemediationDraft:
    item = _detection(detection_id, db)
    _ensure_created(item, db)
    content, evidence = _draft_content(item, payload.draft_type, db)
    draft = RemediationDraft(detection_id=item.id, draft_type=payload.draft_type, content=content, evidence_summary=evidence, actor=ACTOR)
    db.add(draft)
    db.flush()
    db.add(_activity(item.id, InvestigationEventType.REMEDIATION_DRAFT_GENERATED, details={"draft_id": str(draft.id), "draft_type": payload.draft_type.value}))
    db.commit()
    db.refresh(draft)
    return draft
