from fastapi.testclient import TestClient

from app.database.session import get_db
from app.main import app
from app.seed import seed_demo_data
from tests.test_detection import make_session


def test_investigation_status_notes_audit_and_drafts() -> None:
    db = make_session()
    seed_demo_data(db)
    def override_db():
        yield db
    app.dependency_overrides[get_db] = override_db
    try:
        client = TestClient(app)
        client.post("/api/detections/scan")
        detection = next(item for item in client.get("/api/detections").json() if item["candidate"]["source"] == "App Store" and item["severity"] in {"HIGH", "CRITICAL"})
        endpoint = f"/api/detections/{detection['id']}"
        state = client.get(endpoint + "/investigation")
        assert state.status_code == 200 and state.json()["status"] == "NEW"
        changed = client.post(endpoint + "/status", json={"status": "INVESTIGATING"})
        assert changed.status_code == 200 and changed.json()["status"] == "INVESTIGATING"
        assert [x["event_type"] for x in changed.json()["activity"]] == ["INVESTIGATION_CREATED", "STATUS_CHANGED"]
        repeated = client.post(endpoint + "/status", json={"status": "INVESTIGATING"})
        assert repeated.status_code == 200 and len(repeated.json()["activity"]) == 2
        assert client.post(endpoint + "/status", json={"status": "FALSE_POSITIVE"}).status_code == 200
        assert client.post(endpoint + "/status", json={"status": "CONFIRMED_THREAT"}).status_code == 422
        note = client.post(endpoint + "/notes", json={"content": "Reviewed publisher mismatch."})
        assert note.status_code == 200 and note.json()["notes"][0]["content"] == "Reviewed publisher mismatch."
        assert client.post(endpoint + "/notes", json={"content": "   "}).status_code == 422
        draft = client.post(endpoint + "/remediation-drafts", json={"draft_type": "APP_STORE"})
        assert draft.status_code == 200
        assert "DRAFT ONLY" in draft.json()["content"] and detection["candidate"]["name"] in draft.json()["content"]
        state = client.get(endpoint + "/investigation").json()
        assert [x["created_at"] for x in state["activity"]] == sorted(x["created_at"] for x in state["activity"])
    finally:
        app.dependency_overrides.clear()
        db.close()
