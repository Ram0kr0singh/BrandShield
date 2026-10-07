from uuid import uuid4
import json
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from app.analyst import GroqAnalystProvider, generate_analysis
from app.core.config import Settings
from app.database.session import get_db
from app.main import app
from app.seed import seed_demo_data
from tests.test_detection import make_session


def test_settings_load_repository_env_independently_of_working_directory() -> None:
    env_file = Settings.model_config["env_file"]
    assert Path(env_file) == Path(__file__).resolve().parents[2] / ".env"


def test_deterministic_analyst_is_evidence_grounded_and_preserves_detection(monkeypatch) -> None:
    from app.api import detections as detections_api

    monkeypatch.setattr(detections_api, "get_settings", lambda: Settings(database_url="postgresql+psycopg://localhost/test", llm_api_key=None))
    db = make_session()
    seed_demo_data(db)
    def override_db():
        yield db
    app.dependency_overrides[get_db] = override_db
    try:
        client = TestClient(app)
        client.post("/api/detections/scan")
        detections = client.get("/api/detections").json()
        high = next(item for item in detections if item["candidate"]["name"] == "N1ke Shopping")
        before = client.get(f"/api/detections/{high['id']}").json()
        response = client.post(f"/api/detections/{high['id']}/analyze")
        assert response.status_code == 200
        analysis = response.json()
        assert analysis["provider"] == "deterministic_fallback"
        assert analysis["source_facts"]["candidate_name"] == "N1ke Shopping"
        assert analysis["source_facts"]["risk_score"] == before["risk_score"]
        assert analysis["source_facts"]["severity"] == before["severity"]
        assert any(item["signal_type"] == "PUBLISHER_MISMATCH" for item in analysis["key_evidence"])
        after = client.get(f"/api/detections/{high['id']}").json()
        assert {key: after[key] for key in ("risk_score", "severity", "threat_type", "status", "evidence")} == {key: before[key] for key in ("risk_score", "severity", "threat_type", "status", "evidence")}
        lower = next(item for item in detections if item["severity"] == "LOW" and any(e["signal_type"] == "LOOKALIKE_NAME" and e["score"] == 100 for e in item["evidence"]))
        lower_analysis = client.post(f"/api/detections/{lower['id']}/analyze").json()
        assert "does not by itself establish malicious intent" in lower_analysis["risk_rationale"]
        assert client.post(f"/api/detections/{uuid4()}/analyze").status_code == 404
    finally:
        app.dependency_overrides.clear()
        db.close()


def test_groq_provider_validates_grounded_output_and_falls_back_on_failure(monkeypatch) -> None:
    context = {"candidate_name": "N1ke Shopping", "risk_score": 80.63, "severity": "HIGH", "official_match": False, "investigation_status": "NEW", "source": "App Store", "candidate_url": "https://example.test/app", "publisher_or_developer": "Demo Publisher", "evidence": [{"signal_type": "NAME_SIMILARITY", "available": True, "score": 100.0, "details": {}}, {"signal_type": "PUBLISHER_MISMATCH", "available": True, "score": 100.0, "details": {}}, {"signal_type": "LOGO_SIMILARITY", "available": False, "score": None, "details": {}}]}
    settings = Settings(database_url="postgresql+psycopg://test:test@localhost/test", llm_api_key="test-key", llm_base_url="https://provider.test/v1")
    payload = {"summary": "Persisted signals warrant review.", "risk_rationale": "Publisher mismatch is present.", "key_evidence": ["NAME_SIMILARITY", "PUBLISHER_MISMATCH"], "uncertainties": ["Logo evidence is unavailable."], "recommended_actions": ["Verify publisher identity."], "confidence": "Grounded in supplied evidence."}
    captured = {}

    def fake_post(url, **kwargs):
        assert url == "https://provider.test/v1/chat/completions"
        captured["url"] = url
        captured.update(kwargs)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": json.dumps(payload)}}]},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr("app.analyst.httpx.post", fake_post)
    result = GroqAnalystProvider(settings).generate(context)
    assert result["provider"] == "groq"
    assert [item["signal_type"] for item in result["key_evidence"]] == payload["key_evidence"]
    assert captured["url"] == "https://provider.test/v1/chat/completions"
    assert captured["headers"] == {"Authorization": "Bearer test-key"}
    request_body = captured["json"]
    assert request_body["model"] == "openai/gpt-oss-120b"
    assert request_body["response_format"]["type"] == "json_schema"
    assert request_body["response_format"]["json_schema"]["strict"] is True
    request_schema = request_body["response_format"]["json_schema"]["schema"]
    assert request_schema["additionalProperties"] is False
    assert request_schema["properties"]["key_evidence"]["items"]["enum"] == [
        "NAME_SIMILARITY",
        "PUBLISHER_MISMATCH",
    ]
    assert captured["timeout"] == settings.llm_timeout_seconds

    def timeout_post(url, **kwargs):
        assert url.endswith("/chat/completions")
        assert kwargs["timeout"] == settings.llm_timeout_seconds
        raise httpx.TimeoutException("timed out")

    monkeypatch.setattr("app.analyst.httpx.post", timeout_post)
    fallback = generate_analysis(context, settings)
    assert fallback["provider"] == "deterministic_fallback"


def test_groq_http_denial_is_logged_safely_and_falls_back(monkeypatch, caplog) -> None:
    context = {
        "candidate_name": "Synthetic check",
        "risk_score": 80.63,
        "severity": "HIGH",
        "official_match": False,
        "investigation_status": "NEW",
        "source": "App Store",
        "candidate_url": "https://example.test/app",
        "publisher_or_developer": "Synthetic Publisher",
        "evidence": [{"signal_type": "PUBLISHER_MISMATCH", "available": True, "score": 100.0, "details": {}}],
    }
    secret = "test-key-that-must-not-be-logged"
    settings = Settings(
        database_url="postgresql+psycopg://localhost/test",
        llm_api_key=secret,
        llm_base_url="https://provider.test/v1",
    )

    def forbidden_post(url, **kwargs):
        assert url == "https://provider.test/v1/chat/completions"
        assert kwargs["timeout"] == settings.llm_timeout_seconds
        return httpx.Response(
            403,
            text="<html>error code: 1010</html>",
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr("app.analyst.httpx.post", forbidden_post)
    result = generate_analysis(context, settings)

    assert result["provider"] == "deterministic_fallback"
    assert "category=upstream_access_denied" in caplog.text
    assert "http_status=403" in caplog.text
    assert "Cloudflare error 1010" in caplog.text
    assert secret not in caplog.text


def test_groq_malformed_response_falls_back(monkeypatch) -> None:
    context = {
        "candidate_name": "Synthetic check",
        "risk_score": 80.63,
        "severity": "HIGH",
        "official_match": False,
        "investigation_status": "NEW",
        "source": "App Store",
        "candidate_url": "https://example.test/app",
        "publisher_or_developer": "Synthetic Publisher",
        "evidence": [{"signal_type": "PUBLISHER_MISMATCH", "available": True, "score": 100.0, "details": {}}],
    }

    settings = Settings(
        database_url="postgresql+psycopg://localhost/test",
        llm_api_key="test-key",
        llm_base_url="https://provider.test/v1",
    )
    def malformed_post(url, **kwargs):
        assert url == "https://provider.test/v1/chat/completions"
        assert kwargs["timeout"] == settings.llm_timeout_seconds
        return httpx.Response(
            200,
            text=json.dumps({"choices": [{"message": {"content": "not JSON"}}]}),
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr("app.analyst.httpx.post", malformed_post)

    result = generate_analysis(context, settings)

    assert result["provider"] == "deterministic_fallback"
