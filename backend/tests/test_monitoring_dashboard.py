from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database.session import get_db
from app.main import app
from app.models import Brand
from app.seed import seed_demo_data
from tests.test_detection import make_session


def test_monitoring_scan_persists_run_and_dashboard_is_brand_scoped() -> None:
    db = make_session()
    seed_demo_data(db)

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    try:
        client = TestClient(app)
        brands = client.get("/api/brands").json()
        nike = next(item for item in brands if item["slug"] == "nike")
        spotify = next(item for item in brands if item["slug"] == "spotify")
        scan = client.post("/api/monitoring/scan", json={"brand_id": nike["id"]})
        assert scan.status_code == 200
        run = scan.json()
        assert run["status"] == "COMPLETED"
        assert run["candidate_count"] == run["social_candidate_count"] + run["app_candidate_count"]
        assert client.get(f"/api/monitoring/runs/{run['id']}").status_code == 200
        overview = client.get("/api/dashboard/overview", params={"brand_id": nike["id"]})
        assert overview.status_code == 200
        body = overview.json()
        assert body["brand"]["name"] == "Nike"
        assert body["summary"]["total_candidates"] == run["candidate_count"]
        assert body["summary"]["total_detections"] == run["candidate_count"]
        other = client.get("/api/dashboard/overview", params={"brand_id": spotify["id"]}).json()
        assert other["brand"]["id"] != body["brand"]["id"]
    finally:
        app.dependency_overrides.clear()
        db.close()
