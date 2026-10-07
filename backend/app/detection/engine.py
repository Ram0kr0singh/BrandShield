from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.detection.signals import Signal, app_official_signal, description_signal, logo_signal, lookalike_signal, name_signal, publisher_signal, social_official_signal
from app.models import AppCandidate, Brand, Detection, DetectionCandidateType, DetectionEvidence, DetectionStatus, OfficialApp, OfficialSocialAccount, Severity, SocialCandidate, ThreatType

WEIGHTS = {"NAME_SIMILARITY": 25, "LOOKALIKE_NAME": 15, "DESCRIPTION_SIMILARITY": 20, "PUBLISHER_MISMATCH": 15}


def _severity(score: float) -> Severity:
    if score >= 90:
        return Severity.CRITICAL
    if score >= 75:
        return Severity.HIGH
    if score >= 50:
        return Severity.MEDIUM
    if score >= 25:
        return Severity.LOW
    return Severity.SAFE


def _score(signals: Iterable[Signal], official_match: bool) -> tuple[float, float]:
    signal_list = list(signals)
    if official_match:
        return 0.0, 100.0
    scored = [item for item in signal_list if item.available and item.score is not None and item.signal_type in WEIGHTS]
    total_weight = sum(WEIGHTS[item.signal_type] for item in scored)
    raw = sum(WEIGHTS[item.signal_type] * item.score for item in scored) / total_weight if total_weight else 0.0
    # Similarity alone is explanatory, but cannot independently become a severe verdict.
    corroborated = any(item.signal_type == "PUBLISHER_MISMATCH" and item.score == 100 for item in scored) or any(item.signal_type == "DESCRIPTION_SIMILARITY" and item.score >= 70 for item in scored)
    if not corroborated:
        raw = min(raw, 49.0)
    confidence = round(100 * sum(item.available for item in signal_list) / len(signal_list), 2) if signal_list else 0.0
    return round(raw, 2), confidence


def _threat_type(candidate_type: DetectionCandidateType, score: float, signals: list[Signal]) -> ThreatType | None:
    if score < 25:
        return None
    publisher = next((item for item in signals if item.signal_type == "PUBLISHER_MISMATCH"), None)
    lookalike = next((item for item in signals if item.signal_type == "LOOKALIKE_NAME"), None)
    if candidate_type == DetectionCandidateType.APP and publisher and publisher.score == 100:
        return ThreatType.SUSPICIOUS_PUBLISHER
    if lookalike and lookalike.score == 100:
        return ThreatType.LOOKALIKE_IDENTITY
    return ThreatType.FAKE_APP if candidate_type == DetectionCandidateType.APP else ThreatType.BRAND_IMPERSONATION


def _persist(db: Session, brand: Brand, candidate_type: DetectionCandidateType, candidate_id: UUID, signals: list[Signal]) -> Detection:
    official = next(item for item in signals if item.signal_type == "OFFICIAL_ASSET_MATCH")
    official_match = bool(official.details["matched"])
    score, confidence = _score(signals, official_match)
    detection = db.scalar(select(Detection).where(Detection.candidate_type == candidate_type, Detection.candidate_id == candidate_id))
    if detection is None:
        detection = Detection(brand_id=brand.id, candidate_type=candidate_type, candidate_id=candidate_id, severity=_severity(score), risk_score=score, confidence=confidence, official_match=official_match, lookalike_detected=False)
        db.add(detection)
        db.flush()
    else:
        detection.brand_id = brand.id
        detection.evidence.clear()
    detection.risk_score = score
    detection.confidence = confidence
    detection.official_match = official_match
    detection.lookalike_detected = bool(next(item for item in signals if item.signal_type == "LOOKALIKE_NAME").details["detected"])
    detection.severity = _severity(score)
    detection.threat_type = _threat_type(candidate_type, score, signals)
    detection.status = DetectionStatus.FALSE_POSITIVE if official_match else DetectionStatus.NEW
    detection.detected_at = datetime.now(timezone.utc)
    detection.evidence.extend(DetectionEvidence(signal_type=item.signal_type, available=item.available, score=item.score, priority=item.priority, details=item.details) for item in sorted(signals, key=lambda value: value.priority))
    db.commit()
    db.refresh(detection)
    return detection


def analyze_social_candidate(db: Session, candidate_id: UUID) -> Detection:
    candidate = db.get(SocialCandidate, candidate_id)
    if candidate is None:
        raise LookupError("Social candidate not found")
    brand = db.get(Brand, candidate.brand_id)
    assert brand is not None
    accounts = list(db.scalars(select(OfficialSocialAccount).where(OfficialSocialAccount.brand_id == brand.id)))
    name, name_result = name_signal(brand, candidate.display_name or candidate.handle)
    signals = [social_official_signal(candidate, accounts), name, lookalike_signal(name_result), description_signal(candidate.description, [brand.description or ""] + [item.description or "" for item in accounts]), logo_signal()]
    return _persist(db, brand, DetectionCandidateType.SOCIAL, candidate.id, signals)


def analyze_app_candidate(db: Session, candidate_id: UUID) -> Detection:
    candidate = db.get(AppCandidate, candidate_id)
    if candidate is None:
        raise LookupError("App candidate not found")
    brand = db.get(Brand, candidate.brand_id)
    assert brand is not None
    apps = list(db.scalars(select(OfficialApp).where(OfficialApp.brand_id == brand.id)))
    name, name_result = name_signal(brand, candidate.app_name)
    signals = [app_official_signal(candidate, apps), name, lookalike_signal(name_result), publisher_signal(candidate, apps), description_signal(candidate.description, [brand.description or ""] + [item.description or "" for item in apps]), logo_signal()]
    return _persist(db, brand, DetectionCandidateType.APP, candidate.id, signals)


def scan_all(db: Session) -> list[Detection]:
    detections = [analyze_social_candidate(db, item.id) for item in db.scalars(select(SocialCandidate))]
    detections.extend(analyze_app_candidate(db, item.id) for item in db.scalars(select(AppCandidate)))
    return detections
