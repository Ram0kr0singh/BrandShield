from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import AppCandidate, Brand, OfficialApp, OfficialBrandAsset, OfficialSocialAccount, SocialCandidate
from app.schemas import (AppCandidateCreate, AppCandidateRead, AssetRead, BrandCreate, BrandRead, OfficialAppCreate, OfficialAppRead, OfficialSocialCreate, OfficialSocialRead, SocialCandidateCreate, SocialCandidateRead)

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
    return save(Brand(**payload.model_dump()), db)  # type: ignore[return-value]


@router.get("/{brand_id}", response_model=BrandRead)
def get_brand(brand_id: UUID, db: Session = Depends(get_db)) -> Brand:
    return brand_or_404(brand_id, db)


@router.get("/{brand_id}/assets", response_model=list[AssetRead])
def list_assets(brand_id: UUID, db: Session = Depends(get_db)) -> list[OfficialBrandAsset]:
    brand_or_404(brand_id, db)
    return list(db.scalars(select(OfficialBrandAsset).where(OfficialBrandAsset.brand_id == brand_id)))


@router.get("/{brand_id}/social-accounts", response_model=list[OfficialSocialRead])
def list_social_accounts(brand_id: UUID, db: Session = Depends(get_db)) -> list[OfficialSocialAccount]:
    brand_or_404(brand_id, db)
    return list(db.scalars(select(OfficialSocialAccount).where(OfficialSocialAccount.brand_id == brand_id)))


@router.post("/{brand_id}/social-accounts", response_model=OfficialSocialRead, status_code=status.HTTP_201_CREATED)
def create_social_account(brand_id: UUID, payload: OfficialSocialCreate, db: Session = Depends(get_db)) -> OfficialSocialAccount:
    brand_or_404(brand_id, db)
    return save(OfficialSocialAccount(brand_id=brand_id, **payload.model_dump()), db)  # type: ignore[return-value]


@router.get("/{brand_id}/apps", response_model=list[OfficialAppRead])
def list_apps(brand_id: UUID, db: Session = Depends(get_db)) -> list[OfficialApp]:
    brand_or_404(brand_id, db)
    return list(db.scalars(select(OfficialApp).where(OfficialApp.brand_id == brand_id)))


@router.post("/{brand_id}/apps", response_model=OfficialAppRead, status_code=status.HTTP_201_CREATED)
def create_app(brand_id: UUID, payload: OfficialAppCreate, db: Session = Depends(get_db)) -> OfficialApp:
    brand_or_404(brand_id, db)
    return save(OfficialApp(brand_id=brand_id, **payload.model_dump()), db)  # type: ignore[return-value]


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
