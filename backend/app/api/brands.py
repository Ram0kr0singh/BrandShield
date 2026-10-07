from io import BytesIO
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.logos import ensure_upload_logo_directory, logo_url
from app.models import AppCandidate, Brand, OfficialApp, OfficialBrandAsset, OfficialSocialAccount, SocialCandidate
from app.schemas import (AppCandidateCreate, AppCandidateRead, AssetCreate, AssetRead, BrandCreate, BrandRead, BrandUpdate, OfficialAppCreate, OfficialAppRead, OfficialSocialCreate, OfficialSocialRead, SocialCandidateCreate, SocialCandidateRead)

router = APIRouter(prefix="/brands", tags=["brands"])


def brand_or_404(brand_id: UUID, db: Session) -> Brand:
    brand = db.get(Brand, brand_id)
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand


def save(instance: object, db: Session) -> object:
    db.add(instance)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="A record with this unique identifier already exists") from error
    db.refresh(instance)
    return instance


@router.get("", response_model=list[BrandRead])
def list_brands(db: Session = Depends(get_db)) -> list[Brand]:
    return list(db.scalars(select(Brand).order_by(Brand.name)))


@router.post("", response_model=BrandRead, status_code=status.HTTP_201_CREATED)
def create_brand(payload: BrandCreate, db: Session = Depends(get_db)) -> Brand:
    if payload.official_domain is not None:
        duplicate = db.scalar(select(Brand.id).where(func.lower(Brand.official_domain) == payload.official_domain.lower()))
        if duplicate is not None:
            raise HTTPException(status_code=409, detail="A brand with this official domain already exists")
    return save(Brand(**payload.model_dump()), db)  # type: ignore[return-value]


@router.patch("/{brand_id}", response_model=BrandRead)
def update_brand(brand_id: UUID, payload: BrandUpdate, db: Session = Depends(get_db)) -> Brand:
    brand = brand_or_404(brand_id, db)
    changes = payload.model_dump(exclude_unset=True)
    if "name" in changes and changes["name"] is None:
        raise HTTPException(status_code=422, detail="Brand name cannot be empty")
    domain = changes.get("official_domain")
    if domain is not None:
        duplicate = db.scalar(select(Brand.id).where(func.lower(Brand.official_domain) == domain.lower(), Brand.id != brand_id))
        if duplicate is not None:
            raise HTTPException(status_code=409, detail="A brand with this official domain already exists")
    for field, value in changes.items():
        setattr(brand, field, value)
    return save(brand, db)  # type: ignore[return-value]


@router.post("/{brand_id}/logo", response_model=BrandRead)
async def upload_brand_logo(
    brand_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Brand:
    """Store a validated local image; detection never downloads remote image URLs."""
    brand = brand_or_404(brand_id, db)
    if file.content_type not in {"image/png", "image/jpeg"}:
        raise HTTPException(status_code=415, detail="Logo uploads must be PNG or JPEG images")
    content = await file.read(2 * 1024 * 1024 + 1)
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Logo upload must be 2 MB or smaller")
    if not content:
        raise HTTPException(status_code=422, detail="Logo upload is empty")
    try:
        with Image.open(BytesIO(content)) as source:
            source.verify()
        with Image.open(BytesIO(content)) as source:
            fmt = source.format
            if fmt not in {"PNG", "JPEG"}:
                raise ValueError("unsupported image format")
            image = source.convert("RGBA" if source.format == "PNG" else "RGB")
            image.load()
    except (OSError, UnidentifiedImageError, ValueError) as error:
        raise HTTPException(status_code=422, detail="Logo upload is not a readable PNG or JPEG image") from error
    suffix = ".png" if fmt == "PNG" else ".jpg"
    filename = f"brand-{brand.id}-{uuid4().hex}{suffix}"
    output = ensure_upload_logo_directory() / filename
    image.save(output, format="PNG" if suffix == ".png" else "JPEG")
    brand.logo_url = logo_url(f"uploads/{filename}")
    return save(brand, db)  # type: ignore[return-value]


@router.get("/{brand_id}", response_model=BrandRead)
def get_brand(brand_id: UUID, db: Session = Depends(get_db)) -> Brand:
    return brand_or_404(brand_id, db)


@router.get("/{brand_id}/assets", response_model=list[AssetRead])
def list_assets(brand_id: UUID, db: Session = Depends(get_db)) -> list[OfficialBrandAsset]:
    brand_or_404(brand_id, db)
    return list(db.scalars(select(OfficialBrandAsset).where(OfficialBrandAsset.brand_id == brand_id)))


@router.post("/{brand_id}/assets", response_model=AssetRead, status_code=status.HTTP_201_CREATED)
def create_asset(brand_id: UUID, payload: AssetCreate, db: Session = Depends(get_db)) -> OfficialBrandAsset:
    brand_or_404(brand_id, db)
    duplicate = db.scalar(select(OfficialBrandAsset.id).where(
        OfficialBrandAsset.brand_id == brand_id,
        OfficialBrandAsset.asset_type == payload.asset_type,
        func.lower(OfficialBrandAsset.value) == payload.value.lower(),
    ))
    if duplicate is not None:
        raise HTTPException(status_code=409, detail="This official asset is already registered")
    return save(OfficialBrandAsset(brand_id=brand_id, **payload.model_dump()), db)  # type: ignore[return-value]


@router.delete("/{brand_id}/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(brand_id: UUID, asset_id: UUID, db: Session = Depends(get_db)) -> None:
    brand_or_404(brand_id, db)
    asset = db.get(OfficialBrandAsset, asset_id)
    if asset is None or asset.brand_id != brand_id:
        raise HTTPException(status_code=404, detail="Official asset not found")
    db.delete(asset)
    db.commit()


@router.get("/{brand_id}/social-accounts", response_model=list[OfficialSocialRead])
def list_social_accounts(brand_id: UUID, db: Session = Depends(get_db)) -> list[OfficialSocialAccount]:
    brand_or_404(brand_id, db)
    return list(db.scalars(select(OfficialSocialAccount).where(OfficialSocialAccount.brand_id == brand_id)))


@router.post("/{brand_id}/social-accounts", response_model=OfficialSocialRead, status_code=status.HTTP_201_CREATED)
def create_social_account(brand_id: UUID, payload: OfficialSocialCreate, db: Session = Depends(get_db)) -> OfficialSocialAccount:
    brand_or_404(brand_id, db)
    duplicate = db.scalar(select(OfficialSocialAccount.id).where(
        OfficialSocialAccount.platform == payload.platform,
        func.lower(OfficialSocialAccount.handle) == payload.handle.lower(),
    ))
    if duplicate is not None:
        raise HTTPException(status_code=409, detail="This platform handle is already registered")
    return save(OfficialSocialAccount(brand_id=brand_id, **payload.model_dump()), db)  # type: ignore[return-value]


@router.delete("/{brand_id}/social-accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_social_account(brand_id: UUID, account_id: UUID, db: Session = Depends(get_db)) -> None:
    brand_or_404(brand_id, db)
    account = db.get(OfficialSocialAccount, account_id)
    if account is None or account.brand_id != brand_id:
        raise HTTPException(status_code=404, detail="Official social account not found")
    db.delete(account)
    db.commit()


@router.get("/{brand_id}/apps", response_model=list[OfficialAppRead])
def list_apps(brand_id: UUID, db: Session = Depends(get_db)) -> list[OfficialApp]:
    brand_or_404(brand_id, db)
    return list(db.scalars(select(OfficialApp).where(OfficialApp.brand_id == brand_id)))


@router.post("/{brand_id}/apps", response_model=OfficialAppRead, status_code=status.HTTP_201_CREATED)
def create_app(brand_id: UUID, payload: OfficialAppCreate, db: Session = Depends(get_db)) -> OfficialApp:
    brand_or_404(brand_id, db)
    duplicate = db.scalar(select(OfficialApp.id).where(
        OfficialApp.platform == payload.platform,
        func.lower(OfficialApp.package_identifier) == payload.package_identifier.lower(),
    ))
    if duplicate is not None:
        raise HTTPException(status_code=409, detail="This platform package ID is already registered")
    return save(OfficialApp(brand_id=brand_id, **payload.model_dump()), db)  # type: ignore[return-value]


@router.delete("/{brand_id}/apps/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_app(brand_id: UUID, app_id: UUID, db: Session = Depends(get_db)) -> None:
    brand_or_404(brand_id, db)
    official_app = db.get(OfficialApp, app_id)
    if official_app is None or official_app.brand_id != brand_id:
        raise HTTPException(status_code=404, detail="Official application not found")
    db.delete(official_app)
    db.commit()


@router.get("/{brand_id}/social-candidates", response_model=list[SocialCandidateRead])
def list_social_candidates(brand_id: UUID, db: Session = Depends(get_db)) -> list[SocialCandidate]:
    brand_or_404(brand_id, db)
    return list(db.scalars(select(SocialCandidate).where(SocialCandidate.brand_id == brand_id)))


@router.post("/{brand_id}/social-candidates", response_model=SocialCandidateRead, status_code=status.HTTP_201_CREATED)
def create_social_candidate(brand_id: UUID, payload: SocialCandidateCreate, db: Session = Depends(get_db)) -> SocialCandidate:
    brand_or_404(brand_id, db)
    return save(SocialCandidate(brand_id=brand_id, **payload.model_dump()), db)  # type: ignore[return-value]


@router.get("/{brand_id}/app-candidates", response_model=list[AppCandidateRead])
def list_app_candidates(brand_id: UUID, db: Session = Depends(get_db)) -> list[AppCandidate]:
    brand_or_404(brand_id, db)
    return list(db.scalars(select(AppCandidate).where(AppCandidate.brand_id == brand_id)))


@router.post("/{brand_id}/app-candidates", response_model=AppCandidateRead, status_code=status.HTTP_201_CREATED)
def create_app_candidate(brand_id: UUID, payload: AppCandidateCreate, db: Session = Depends(get_db)) -> AppCandidate:
    brand_or_404(brand_id, db)
    return save(AppCandidate(brand_id=brand_id, **payload.model_dump()), db)  # type: ignore[return-value]
