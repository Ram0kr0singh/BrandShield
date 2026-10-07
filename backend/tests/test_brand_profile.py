from io import BytesIO

from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database.base import Base
from app.database.session import get_db
from app.main import app
from app.seed import seed_demo_data


def _png_upload() -> BytesIO:
    content = BytesIO()
    Image.new("RGB", (16, 16), "#2f6fed").save(content, format="PNG")
    content.seek(0)
    return content


def test_brand_logo_upload_is_validated_and_served_locally() -> None:
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db: Session = sessionmaker(bind=engine)()
    seed_demo_data(db)

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    try:
        client = TestClient(app)
        brand_id = client.get("/api/brands").json()[0]["id"]
        uploaded = client.post(
            f"/api/brands/{brand_id}/logo",
            files={"file": ("logo.png", _png_upload(), "image/png")},
        )
        assert uploaded.status_code == 200
        reference = uploaded.json()["logo_url"]
        assert reference.startswith("/static/logos/uploads/brand-")
        assert client.get(reference).status_code == 200
        invalid = client.post(
            f"/api/brands/{brand_id}/logo",
            files={"file": ("logo.txt", b"not an image", "text/plain")},
        )
        assert invalid.status_code == 415
    finally:
        app.dependency_overrides.clear()
        db.close()
        engine.dispose()


def test_brand_profile_crud_and_server_validation() -> None:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    db: Session = sessionmaker(bind=engine)()
    seed_demo_data(db)

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    try:
        client = TestClient(app)
        created = client.post("/api/brands", json={
            "name": "Acme Labs",
            "slug": "acme-labs",
            "official_domain": "WWW.Acme.Example",
            "logo_url": "https://cdn.acme.example/logo.png",
        })
        assert created.status_code == 201
        brand_id = created.json()["id"]
        assert created.json()["official_domain"] == "www.acme.example"
        assert client.post("/api/brands", json={
            "name": "Duplicate Domain",
            "slug": "duplicate-domain",
            "official_domain": "WWW.ACME.EXAMPLE",
        }).status_code == 409

        updated = client.patch(f"/api/brands/{brand_id}", json={
            "name": "Acme Group",
            "description": "Official public profiles",
        })
        assert updated.status_code == 200
        assert updated.json()["name"] == "Acme Group"
        assert updated.json()["description"] == "Official public profiles"

        social = client.post(f"/api/brands/{brand_id}/social-accounts", json={
            "platform": "X",
            "handle": "@Acme_Official",
            "profile_url": "https://x.example/Acme_Official",
        })
        assert social.status_code == 201
        social_id = social.json()["id"]
        assert social.json()["handle"] == "Acme_Official"
        assert client.post(f"/api/brands/{brand_id}/social-accounts", json={
            "platform": "X",
            "handle": "acme_official",
            "profile_url": "https://x.example/acme_official",
        }).status_code == 409
        assert client.delete(f"/api/brands/{brand_id}/social-accounts/{social_id}").status_code == 204
        assert client.delete(f"/api/brands/{brand_id}/social-accounts/{social_id}").status_code == 404

        official_app = client.post(f"/api/brands/{brand_id}/apps", json={
            "platform": "GOOGLE_PLAY",
            "app_name": "Acme Portal",
            "package_identifier": "com.acme.portal",
            "store_url": "https://play.example/apps/acme",
            "developer_name": "Acme Labs",
        })
        assert official_app.status_code == 201
        app_id = official_app.json()["id"]
        assert client.post(f"/api/brands/{brand_id}/apps", json={
            "platform": "GOOGLE_PLAY",
            "app_name": "Duplicate",
            "package_identifier": "EXAMPLE.DEMO.NIKE.OFFICIAL",
            "store_url": "https://play.example/duplicate",
            "developer_name": "Acme Labs",
        }).status_code == 409
        assert client.delete(f"/api/brands/{brand_id}/apps/{app_id}").status_code == 204

        asset = client.post(f"/api/brands/{brand_id}/assets", json={
            "asset_type": "OTHER",
            "value": "ACME wordmark",
            "label": "Registered wordmark",
        })
        assert asset.status_code == 201
        asset_id = asset.json()["id"]
        assert client.post(f"/api/brands/{brand_id}/assets", json={
            "asset_type": "OTHER",
            "value": "acme wordmark",
        }).status_code == 409
        assert client.delete(f"/api/brands/{brand_id}/assets/{asset_id}").status_code == 204
        assert client.post(f"/api/brands/{brand_id}/assets", json={
            "asset_type": "DOMAIN",
            "value": "https://bad.example/path",
        }).status_code == 422
        assert client.post(f"/api/brands/{brand_id}/assets", json={
            "asset_type": "LOGO",
            "value": "not-a-url",
        }).status_code == 422

        assert client.patch(f"/api/brands/{brand_id}", json={
            "official_domain": "https://not-a-host.example/path",
        }).status_code == 422
        assert client.patch(f"/api/brands/{brand_id}", json={
            "name": "   ",
        }).status_code == 422
        assert client.patch(f"/api/brands/{brand_id}", json={
            "official_domain": "nike.demo.example",
        }).status_code == 409
        assert client.post(f"/api/brands/{brand_id}/social-accounts", json={
            "platform": "X",
            "handle": "not a handle",
            "profile_url": "https://x.example/invalid",
        }).status_code == 422
        assert client.post(f"/api/brands/{brand_id}/social-accounts", json={
            "platform": "X",
            "handle": "valid",
            "profile_url": "javascript:alert(1)",
        }).status_code == 422
        assert client.post(f"/api/brands/{brand_id}/apps", json={
            "platform": "GOOGLE_PLAY",
            "app_name": "Bad Package",
            "package_identifier": "not a package",
            "store_url": "https://play.example/bad",
            "developer_name": "Acme Labs",
        }).status_code == 422
    finally:
        app.dependency_overrides.clear()
        db.close()
        engine.dispose()
