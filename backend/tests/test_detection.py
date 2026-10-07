from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database.base import Base
from app.database.session import get_db
from app.detection.engine import analyze_app_candidate, analyze_social_candidate, scan_all
from app.detection.normalization import analyze_name, normalize_text
from app.main import app
from app.models import AppCandidate, Detection, Severity, SocialCandidate
from app.seed import seed_demo_data


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record):  # type: ignore[no-untyped-def]
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_normalization_and_lookalike_transformations() -> None:
    assert normalize_text("  NÍKE--Store! ") == "níke store"
    substitution = analyze_name("Nike", "N1ke")
    assert substitution.similarity == 100
    assert substitution.detected and substitution.transformations[0]["type"] == "CHARACTER_SUBSTITUTION"
    assert any(item["type"] == "CHARACTER_SUBSTITUTION" for item in analyze_name("Spotify", "Spot1fy").transformations)
    assert any(item["type"] == "ADDED_WORDS" for item in analyze_name("Nike", "Nike Support").transformations)
    assert any(item["type"] == "SPACING_VARIATION" for item in analyze_name("Nike Store", "NikeStore").transformations)
    assert analyze_name("Nike", "Completely Different").similarity < 30


def test_seeded_official_assets_are_safe_and_app_mismatch_is_explainable() -> None:
    db = make_session()
    seed_demo_data(db)
    official_social = db.scalar(select(SocialCandidate).where(SocialCandidate.handle == "nike"))
    official_adidas = db.scalar(select(SocialCandidate).where(SocialCandidate.handle == "adidas"))
    official_app = db.scalar(select(AppCandidate).where(AppCandidate.package_identifier == "example.demo.spotify.official"))
    suspicious_app = db.scalar(select(AppCandidate).where(AppCandidate.package_identifier == "example.demo.n1ke.shopping"))
    legitimate_similar = db.scalar(select(SocialCandidate).where(SocialCandidate.handle == "nike_running_club_local"))
    assert official_social and official_adidas and official_app and suspicious_app and legitimate_similar
    assert analyze_social_candidate(db, official_social.id).severity == Severity.SAFE
    assert analyze_social_candidate(db, official_adidas.id).severity == Severity.SAFE
    assert analyze_app_candidate(db, official_app.id).severity == Severity.SAFE
    assert analyze_social_candidate(db, legitimate_similar.id).severity in {Severity.SAFE, Severity.LOW}
    result = analyze_app_candidate(db, suspicious_app.id)
    evidence = {item.signal_type: item for item in result.evidence}
    assert evidence["PUBLISHER_MISMATCH"].details["result"] == "MISMATCH"
    assert evidence["LOGO_SIMILARITY"].available is True
    assert evidence["LOGO_SIMILARITY"].score is not None and evidence["LOGO_SIMILARITY"].score >= 90


def test_scan_persists_without_duplicates_and_api_returns_evidence() -> None:
    db = make_session()
    seed_demo_data(db)
    first = scan_all(db)
    second = scan_all(db)
    assert len(first) == len(second) == 24
    assert db.scalar(select(func.count()).select_from(Detection)) == 24

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    try:
        client = TestClient(app)
        name = client.post("/api/analyze/name", json={"official_name": "Nike", "candidate_name": "N1ke"})
        assert name.status_code == 200 and name.json()["detected"] is True
        listed = client.get("/api/detections")
        assert listed.status_code == 200 and len(listed.json()) == 24
        assert listed.json()[0]["evidence"]
        assert client.post("/api/detections/scan").json()["analyzed"] == 24
    finally:
        app.dependency_overrides.clear()
        db.close()
