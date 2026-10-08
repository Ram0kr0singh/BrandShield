import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.database.base import Base
from app.database.session import get_db
from app.main import app
from app.models import Detection
from app.seed import seed_demo_data
from app.sources import NOT_CONFIGURED_MESSAGE, reset_source_status
from tests.test_detection import make_session


@pytest.fixture(autouse=True)
def reset_source_registry():
    reset_source_status()
    yield
    reset_source_status()


@pytest.fixture
def source_client():
    db = make_session()
    seed_demo_data(db)

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            yield client, db
    finally:
        app.dependency_overrides.clear()
        db.close()


def table_counts(db) -> dict[str, int]:
    return {
        table.name: db.scalar(select(func.count()).select_from(table)) or 0
        for table in Base.metadata.sorted_tables
    }


def test_source_status_has_expected_sources_and_shape(source_client) -> None:
    client, _ = source_client
    response = client.get("/api/sources/status")

    assert response.status_code == 200
    sources = response.json()
    assert [(source["id"], source["name"], source["kind"], source["status"]) for source in sources] == [
        ("demo_dataset", "Controlled demo dataset", "DEMO", "ONLINE"),
        ("instagram", "Instagram live monitor", "SOCIAL", "NOT_CONFIGURED"),
        ("google_play", "Google Play live monitor", "APP", "NOT_CONFIGURED"),
        ("app_store", "Apple App Store live monitor", "APP", "NOT_CONFIGURED"),
    ]
    assert all({
        "id", "name", "kind", "status", "message", "last_checked_at", "last_success_at",
    } <= set(source) for source in sources)
    assert all(source["message"] == NOT_CONFIGURED_MESSAGE for source in sources[1:])
    assert sources[0]["last_checked_at"] is not None
    assert sources[0]["last_success_at"] is not None
    assert all(source["last_success_at"] is None for source in sources[1:])


def test_simulated_outage_and_restore_round_trip(source_client) -> None:
    client, _ = source_client
    outage = client.post("/api/sources/instagram/simulate-outage")
    assert outage.status_code == 200
    assert outage.json()["status"] == "DEGRADED"
    assert outage.json()["message"] == "Source unreachable (simulated for demo). Showing last stored data."
    assert outage.json()["simulated"] is True
    assert client.get("/api/sources/status").json()[1]["simulated"] is True

    restored = client.post("/api/sources/instagram/restore")
    assert restored.status_code == 200
    assert restored.json()["status"] == "NOT_CONFIGURED"
    assert restored.json()["message"] == NOT_CONFIGURED_MESSAGE
    assert restored.json()["simulated"] is True
    assert client.get("/api/sources/status").json()[1]["simulated"] is False


def test_demo_dataset_cannot_be_broken_and_unknown_source_is_404(source_client) -> None:
    client, _ = source_client
    assert client.post("/api/sources/demo_dataset/simulate-outage").status_code == 409
    assert client.post("/api/sources/demo_dataset/restore").status_code == 409
    assert client.post("/api/sources/missing/simulate-outage").status_code == 404
    assert client.post("/api/sources/missing/restore").status_code == 404


def test_source_status_and_toggles_do_not_write_to_database(source_client) -> None:
    client, db = source_client
    before = table_counts(db)

    assert client.get("/api/sources/status").status_code == 200
    assert client.post("/api/sources/google_play/simulate-outage").status_code == 200
    assert client.post("/api/sources/google_play/restore").status_code == 200

    assert table_counts(db) == before


def test_scan_succeeds_during_simulated_outage_and_scores_remain_unchanged(source_client) -> None:
    client, db = source_client
    brands = client.get("/api/brands").json()
    nike = next(item for item in brands if item["slug"] == "nike")

    initial_scan = client.post("/api/detections/scan")
    assert initial_scan.status_code == 200
    assert initial_scan.json()["analyzed"] == 24
    before_scores = {
        detection.id: (detection.risk_score, detection.severity.value)
        for detection in db.scalars(select(Detection))
    }
    assert len(before_scores) == 24

    normal_scan = client.post("/api/monitoring/scan", json={"brand_id": nike["id"]})
    assert normal_scan.status_code == 200
    assert normal_scan.json()["source_warnings"] == []

    assert client.post("/api/sources/instagram/simulate-outage").status_code == 200
    scan = client.post("/api/monitoring/scan", json={"brand_id": nike["id"]})
    assert scan.status_code == 200
    response = scan.json()
    assert response["status"] == "COMPLETED"
    assert response["candidate_count"] == 7
    assert response["source_warnings"] == [
        {
            "id": "instagram",
            "name": "Instagram live monitor",
            "status": "DEGRADED",
            "message": "Source unreachable (simulated for demo). Showing last stored data.",
        },
    ]

    after_scores = {
        detection.id: (detection.risk_score, detection.severity.value)
        for detection in db.scalars(select(Detection))
    }
    assert after_scores == before_scores
    assert db.scalar(select(func.count()).select_from(Detection)) == 24
