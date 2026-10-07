from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database.base import Base
from app.database.session import get_db
from app.main import app
from app.models import Brand, OfficialBrandAsset, AssetType
from app.seed import seed_demo_data


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record):  # type: ignore[no-untyped-def]
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_brand_relationships_and_unique_asset() -> None:
    db = make_session()
    brand = Brand(name="Test Brand", slug="test-brand")
    brand.assets.append(OfficialBrandAsset(asset_type=AssetType.DOMAIN, value="test.demo.example"))
    db.add(brand)
    db.commit()
    assert brand.assets[0].brand_id == brand.id

    db.add(OfficialBrandAsset(brand_id=brand.id, asset_type=AssetType.DOMAIN, value="test.demo.example"))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
    else:
        raise AssertionError("duplicate official asset was accepted")


def test_seed_is_repeatable_and_covers_candidate_categories() -> None:
    db = make_session()
    first = seed_demo_data(db)
    second = seed_demo_data(db)
    assert first == second == {"brands": 5, "official_social_accounts": 5, "official_apps": 5, "official_assets": 10, "social_candidates": 13, "app_candidates": 11}
    assert db.query(Brand).filter_by(slug="nike").one().social_candidates


def test_domain_api_serializes_and_rejects_duplicate_brand() -> None:
    db = make_session()
    seed_demo_data(db)

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    try:
        client = TestClient(app)
        brands = client.get("/api/brands")
        assert brands.status_code == 200
        nike = next(item for item in brands.json() if item["slug"] == "nike")
        assert client.get(f"/api/brands/{nike['id']}/assets").status_code == 200
        assert len(client.get(f"/api/brands/{nike['id']}/social-candidates").json()) == 4
        assert len(client.get(f"/api/brands/{nike['id']}/app-candidates").json()) == 3
        payload = {"name": "Extra Brand", "slug": "extra-brand", "official_domain": "extra.demo.example"}
        assert client.post("/api/brands", json=payload).status_code == 201
        assert client.post("/api/brands", json=payload).status_code == 409
        assert client.post("/api/brands", json={"name": "Bad", "slug": "bad", "official_domain": "https://bad.example"}).status_code == 422
    finally:
        app.dependency_overrides.clear()
        db.close()
