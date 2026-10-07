"""Deterministic, synthetic demo data for local BrandShield demonstrations."""

from PIL import Image, ImageDraw, ImageFont

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.logos import ensure_logo_directory, logo_url
from app.models import AppCandidate, AppPlatform, AssetType, Brand, BrandStatus, CandidateStatus, OfficialApp, OfficialBrandAsset, OfficialSocialAccount, SocialCandidate, SocialPlatform

DEMO_SOURCE = "controlled_demo_seed"
BRANDS = [
    ("Nike", "nike", "nike.demo.example", "Nike demo profile"),
    ("Apple", "apple", "apple.demo.example", "Apple demo profile"),
    ("Samsung", "samsung", "samsung.demo.example", "Samsung demo profile"),
    ("Spotify", "spotify", "spotify.demo.example", "Spotify demo profile"),
    ("Adidas", "adidas", "adidas.demo.example", "Adidas demo profile"),
]
BRAND_COLORS = {
    "nike": "#2f6fed", "apple": "#8b5cf6", "samsung": "#06b6d4", "spotify": "#22c55e", "adidas": "#f97316",
}


def _write_logo(filename: str, initial: str, color: str, variant: str = "official") -> str:
    """Create small local synthetic PNGs suitable for deterministic dHash comparison."""
    path = ensure_logo_directory() / filename
    image = Image.new("RGB", (128, 128), "#f8fafc")
    draw = ImageDraw.Draw(image)
    if variant == "different":
        # This gradient is plainly distinct, with a dHash edge pattern unlike
        # the official badge, so legitimate similarly named candidates stay low.
        for x in range(128):
            shade = round((127 - x) * 255 / 127)
            draw.line((x, 0, x, 127), fill=(shade, shade, shade))
    else:
        # One-pixel movement preserves the intended near-copy dHash distance
        # (at most three bits, therefore >= 90 after rescaling).
        shift = 1 if variant == "near" else 0
        draw.rounded_rectangle((22 + shift, 18 + shift, 106 + shift, 110 + shift), radius=20, fill=color)
        draw.ellipse((42 + shift, 36 + shift, 86 + shift, 80 + shift), fill="#ffffff")
        font = ImageFont.load_default()
        draw.text((59 + shift, 85 + shift), initial[:1].upper(), fill="#ffffff", font=font, anchor="mm")
    image.save(path, format="PNG")
    return logo_url(filename)


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
        official_logo = _write_logo(f"{slug}-official.png", name, BRAND_COLORS[slug])
        brand = _first_or_add(db, Brand, {"name": name, "description": description, "official_domain": domain, "logo_url": official_logo, "status": BrandStatus.ACTIVE}, slug=slug)
        assert isinstance(brand, Brand)
        brand.logo_url = official_logo
        logo_asset = db.scalar(select(OfficialBrandAsset).where(OfficialBrandAsset.brand_id == brand.id, OfficialBrandAsset.asset_type == AssetType.LOGO))
        if logo_asset is None:
            logo_asset = OfficialBrandAsset(brand_id=brand.id, asset_type=AssetType.LOGO, value=official_logo, label=f"{name} synthetic local logo")
            db.add(logo_asset)
        else:
            logo_asset.value, logo_asset.label = official_logo, f"{name} synthetic local logo"
        _first_or_add(db, OfficialBrandAsset, {"label": f"{name} demo domain"}, brand_id=brand.id, asset_type=AssetType.DOMAIN, value=domain)
        _first_or_add(db, OfficialSocialAccount, {"profile_url": f"https://social.demo.example/{slug}", "display_name": name, "verified": True, "description": f"Synthetic official {name} social account", "status": BrandStatus.ACTIVE}, brand_id=brand.id, platform=SocialPlatform.INSTAGRAM, handle=slug)
        official_app = _first_or_add(db, OfficialApp, {"app_name": f"{name} App", "store_url": f"https://store.demo.example/{slug}-official", "developer_name": f"{name} Demo Publisher", "developer_identifier": f"demo.{slug}.official", "description": f"Synthetic official {name} application", "logo_url": official_logo, "status": BrandStatus.ACTIVE}, brand_id=brand.id, platform=AppPlatform.GOOGLE_PLAY, package_identifier=f"example.demo.{slug}.official")
        official_app.logo_url = official_logo
        official_social = _first_or_add(db, SocialCandidate, {"display_name": name, "profile_url": f"https://social.demo.example/{slug}", "description": "Synthetic official-reference candidate for exclusion testing", "followers_count": 1000000, "verified": True, "avatar_url": official_logo, "discovery_source": DEMO_SOURCE, "status": CandidateStatus.IGNORED}, brand_id=brand.id, platform=SocialPlatform.INSTAGRAM, external_identifier=f"official-{slug}", handle=slug)
        official_social.avatar_url = official_logo
        official_candidate_app = _first_or_add(db, AppCandidate, {"app_name": f"{name} App", "store_url": f"https://store.demo.example/{slug}-official", "developer_name": f"{name} Demo Publisher", "developer_identifier": f"demo.{slug}.official", "description": "Synthetic official-reference candidate for exclusion testing", "logo_url": official_logo, "rating": 4.8, "review_count": 10000, "downloads_text": "1M+", "discovery_source": DEMO_SOURCE, "status": CandidateStatus.IGNORED}, brand_id=brand.id, platform=AppPlatform.GOOGLE_PLAY, package_identifier=f"example.demo.{slug}.official")
        official_candidate_app.logo_url = official_logo

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
        variant = "different" if handle == "nike_running_club_local" else "near"
        candidate_logo = _write_logo(f"candidate-{handle}.png", display_name, BRAND_COLORS[slug], variant)
        candidate = _first_or_add(db, SocialCandidate, {"display_name": display_name, "profile_url": f"https://social.demo.example/{handle}", "description": description, "followers_count": 42, "verified": False, "avatar_url": candidate_logo, "discovery_source": DEMO_SOURCE, "status": CandidateStatus.NEW}, brand_id=brand.id, platform=platform, external_identifier=f"candidate-{handle}", handle=handle)
        candidate.avatar_url = candidate_logo

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
        variant = "near" if package in {"example.demo.nike.rewardspro", "example.demo.n1ke.shopping"} else "different"
        candidate_logo = _write_logo(f"candidate-{package.rsplit('.', 1)[-1]}.png", app_name, BRAND_COLORS[slug], variant)
        candidate = _first_or_add(db, AppCandidate, {"app_name": app_name, "store_url": f"https://store.demo.example/{package}", "developer_name": developer, "developer_identifier": package + ".publisher", "description": description, "logo_url": candidate_logo, "rating": 3.1, "review_count": 19, "downloads_text": "500+", "discovery_source": DEMO_SOURCE, "status": CandidateStatus.NEW}, brand_id=brand.id, platform=AppPlatform.GOOGLE_PLAY, package_identifier=package)
        candidate.logo_url = candidate_logo
    db.commit()
    return {"brands": db.scalar(select(func.count()).select_from(Brand)) or 0, "official_social_accounts": db.scalar(select(func.count()).select_from(OfficialSocialAccount)) or 0, "official_apps": db.scalar(select(func.count()).select_from(OfficialApp)) or 0, "official_assets": db.scalar(select(func.count()).select_from(OfficialBrandAsset)) or 0, "social_candidates": db.scalar(select(func.count()).select_from(SocialCandidate)) or 0, "app_candidates": db.scalar(select(func.count()).select_from(AppCandidate)) or 0}


def main() -> None:
    with SessionLocal() as db:
        counts = seed_demo_data(db)
    print("Controlled demo seed complete:", counts)


if __name__ == "__main__":
    main()
