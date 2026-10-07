"""Deterministic, synthetic demo data for local BrandShield demonstrations."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models import AppCandidate, AppPlatform, AssetType, Brand, BrandStatus, CandidateStatus, OfficialApp, OfficialBrandAsset, OfficialSocialAccount, SocialCandidate, SocialPlatform

DEMO_SOURCE = "controlled_demo_seed"
BRANDS = [
    ("Nike", "nike", "nike.demo.example", "Nike demo profile"),
    ("Apple", "apple", "apple.demo.example", "Apple demo profile"),
    ("Samsung", "samsung", "samsung.demo.example", "Samsung demo profile"),
    ("Spotify", "spotify", "spotify.demo.example", "Spotify demo profile"),
    ("Adidas", "adidas", "adidas.demo.example", "Adidas demo profile"),
]


def _first_or_add(db: Session, model: type, defaults: dict, **where: object) -> object:
    existing = db.scalar(select(model).filter_by(**where))
    if existing is not None:
        return existing
    item = model(**where, **defaults)
    db.add(item)
    db.flush()
    return item


def seed_demo_data(db: Session) -> dict[str, int]:
    """Insert only missing synthetic records; safe to run repeatedly."""
    for name, slug, domain, description in BRANDS:
        brand = _first_or_add(db, Brand, {"name": name, "description": description, "official_domain": domain, "logo_url": f"https://assets.demo.example/{slug}/logo.png", "status": BrandStatus.ACTIVE}, slug=slug)
        assert isinstance(brand, Brand)
        _first_or_add(db, OfficialBrandAsset, {"label": f"{name} synthetic logo"}, brand_id=brand.id, asset_type=AssetType.LOGO, value=f"https://assets.demo.example/{slug}/logo.png")
        _first_or_add(db, OfficialBrandAsset, {"label": f"{name} demo domain"}, brand_id=brand.id, asset_type=AssetType.DOMAIN, value=domain)
        _first_or_add(db, OfficialSocialAccount, {"profile_url": f"https://social.demo.example/{slug}", "display_name": name, "verified": True, "description": f"Synthetic official {name} social account", "status": BrandStatus.ACTIVE}, brand_id=brand.id, platform=SocialPlatform.INSTAGRAM, handle=slug)
        _first_or_add(db, OfficialApp, {"app_name": f"{name} App", "store_url": f"https://store.demo.example/{slug}-official", "developer_name": f"{name} Demo Publisher", "developer_identifier": f"demo.{slug}.official", "description": f"Synthetic official {name} application", "logo_url": f"https://assets.demo.example/{slug}/logo.png", "status": BrandStatus.ACTIVE}, brand_id=brand.id, platform=AppPlatform.GOOGLE_PLAY, package_identifier=f"example.demo.{slug}.official")
        _first_or_add(db, SocialCandidate, {"display_name": name, "profile_url": f"https://social.demo.example/{slug}", "description": "Synthetic official-reference candidate for exclusion testing", "followers_count": 1000000, "verified": True, "avatar_url": f"https://assets.demo.example/{slug}/logo.png", "discovery_source": DEMO_SOURCE, "status": CandidateStatus.IGNORED}, brand_id=brand.id, platform=SocialPlatform.INSTAGRAM, external_identifier=f"official-{slug}", handle=slug)
        _first_or_add(db, AppCandidate, {"app_name": f"{name} App", "store_url": f"https://store.demo.example/{slug}-official", "developer_name": f"{name} Demo Publisher", "developer_identifier": f"demo.{slug}.official", "description": "Synthetic official-reference candidate for exclusion testing", "logo_url": f"https://assets.demo.example/{slug}/logo.png", "rating": 4.8, "review_count": 10000, "downloads_text": "1M+", "discovery_source": DEMO_SOURCE, "status": CandidateStatus.IGNORED}, brand_id=brand.id, platform=AppPlatform.GOOGLE_PLAY, package_identifier=f"example.demo.{slug}.official")

    candidates = [
        ("nike", SocialPlatform.INSTAGRAM, "n1ke_support", "N1ke Support", "Character-swap account offering customer support and reward claims."),
        ("nike", SocialPlatform.INSTAGRAM, "nike_customer_help", "Nike Customer Help", "Unofficial account claiming to resolve Nike orders."),
        ("nike", SocialPlatform.X, "nike_running_club_local", "Nike Running Club Local", "Local community running club; similar name is not a verdict."),
        ("apple", SocialPlatform.FACEBOOK, "apple_id_recovery", "Apple ID Recovery", "Account requesting customers to recover accounts through direct messages."),
        ("samsung", SocialPlatform.INSTAGRAM, "samsung_rewards_center", "Samsung Rewards Center", "Unofficial rewards promotion with synthetic branding."),
        ("spotify", SocialPlatform.TIKTOK, "spotify_premium_unlock", "Spotify Premium Unlock", "Account advertising premium access outside official channels."),
        ("adidas", SocialPlatform.INSTAGRAM, "adldas_deals", "ADlDAS Deals", "Look-alike display name using a visually confusable character."),
        ("adidas", SocialPlatform.INSTAGRAM, "adidas_store_fans", "AdidasStore Fans", "Fan community with a spacing variation; no threat label is stored."),
    ]
    for slug, platform, handle, display_name, description in candidates:
        brand = db.scalar(select(Brand).where(Brand.slug == slug))
        assert brand is not None
        _first_or_add(db, SocialCandidate, {"display_name": display_name, "profile_url": f"https://social.demo.example/{handle}", "description": description, "followers_count": 42, "verified": False, "avatar_url": f"https://assets.demo.example/{slug}/candidate-{handle}.png", "discovery_source": DEMO_SOURCE, "status": CandidateStatus.NEW}, brand_id=brand.id, platform=platform, external_identifier=f"candidate-{handle}", handle=handle)

    app_candidates = [
        ("nike", "Nike Rewards Pro", "example.demo.nike.rewardspro", "Rewardworks Demo LLC", "Similar branding and rewards wording; synthetic publisher mismatch."),
        ("nike", "N1ke Shopping", "example.demo.n1ke.shopping", "Market Mall Demo", "Character-swap app name with a different synthetic publisher."),
        ("apple", "Apple Cleaner Tools", "example.demo.applecleaner", "Utility Lab Demo", "Generic utility name; observation only, not a threat label."),
        ("samsung", "Samsung Deals Hub", "example.demo.samsung.deals", "DealSpark Demo", "Similar company wording with different publisher."),
        ("spotify", "Spotify Premium Player", "example.demo.spotify.premium", "Audio Freeware Demo", "Similar name and streaming description with different publisher."),
        ("adidas", "AdidasStore Coupons", "example.demo.adidas.coupons", "Coupon Factory Demo", "Spacing variation and unrelated publisher."),
    ]
    for slug, app_name, package, developer, description in app_candidates:
        brand = db.scalar(select(Brand).where(Brand.slug == slug))
        assert brand is not None
        _first_or_add(db, AppCandidate, {"app_name": app_name, "store_url": f"https://store.demo.example/{package}", "developer_name": developer, "developer_identifier": package + ".publisher", "description": description, "logo_url": f"https://assets.demo.example/{slug}/candidate-app.png", "rating": 3.1, "review_count": 19, "downloads_text": "500+", "discovery_source": DEMO_SOURCE, "status": CandidateStatus.NEW}, brand_id=brand.id, platform=AppPlatform.GOOGLE_PLAY, package_identifier=package)
    db.commit()
    return {"brands": db.scalar(select(func.count()).select_from(Brand)) or 0, "official_social_accounts": db.scalar(select(func.count()).select_from(OfficialSocialAccount)) or 0, "official_apps": db.scalar(select(func.count()).select_from(OfficialApp)) or 0, "official_assets": db.scalar(select(func.count()).select_from(OfficialBrandAsset)) or 0, "social_candidates": db.scalar(select(func.count()).select_from(SocialCandidate)) or 0, "app_candidates": db.scalar(select(func.count()).select_from(AppCandidate)) or 0}


def main() -> None:
    with SessionLocal() as db:
        counts = seed_demo_data(db)
    print("Controlled demo seed complete:", counts)


if __name__ == "__main__":
    main()
