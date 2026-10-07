"""Brand domain models. Candidate records are observations, never threat verdicts."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class BrandStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class SocialPlatform(str, enum.Enum):
    INSTAGRAM = "INSTAGRAM"
    FACEBOOK = "FACEBOOK"
    X = "X"
    LINKEDIN = "LINKEDIN"
    YOUTUBE = "YOUTUBE"
    TIKTOK = "TIKTOK"
    OTHER = "OTHER"


class AppPlatform(str, enum.Enum):
    GOOGLE_PLAY = "GOOGLE_PLAY"
    APPLE_APP_STORE = "APPLE_APP_STORE"
    OTHER = "OTHER"


class AssetType(str, enum.Enum):
    LOGO = "LOGO"
    DOMAIN = "DOMAIN"
    SOCIAL_ACCOUNT = "SOCIAL_ACCOUNT"
    MOBILE_APP = "MOBILE_APP"
    OTHER = "OTHER"


class CandidateStatus(str, enum.Enum):
    NEW = "NEW"
    REVIEWED = "REVIEWED"
    IGNORED = "IGNORED"


class Timestamped:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Brand(Timestamped, Base):
    __tablename__ = "brands"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    official_domain: Mapped[Optional[str]] = mapped_column(String(253), unique=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(2048))
    status: Mapped[BrandStatus] = mapped_column(Enum(BrandStatus, name="brand_status", native_enum=False), default=BrandStatus.ACTIVE, nullable=False)
    social_accounts: Mapped[list[OfficialSocialAccount]] = relationship(back_populates="brand", cascade="all, delete-orphan")
    apps: Mapped[list[OfficialApp]] = relationship(back_populates="brand", cascade="all, delete-orphan")
    assets: Mapped[list[OfficialBrandAsset]] = relationship(back_populates="brand", cascade="all, delete-orphan")
    social_candidates: Mapped[list[SocialCandidate]] = relationship(back_populates="brand", cascade="all, delete-orphan")
    app_candidates: Mapped[list[AppCandidate]] = relationship(back_populates="brand", cascade="all, delete-orphan")


class OfficialSocialAccount(Timestamped, Base):
    __tablename__ = "official_social_accounts"
    __table_args__ = (UniqueConstraint("platform", "handle", name="uq_official_social_platform_handle"), Index("ix_official_social_brand_platform", "brand_id", "platform"))
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    brand_id: Mapped[UUID] = mapped_column(ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    platform: Mapped[SocialPlatform] = mapped_column(Enum(SocialPlatform, name="social_platform", native_enum=False), nullable=False)
    handle: Mapped[str] = mapped_column(String(255), nullable=False)
    profile_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255))
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[BrandStatus] = mapped_column(Enum(BrandStatus, name="official_social_status", native_enum=False), default=BrandStatus.ACTIVE, nullable=False)
    brand: Mapped[Brand] = relationship(back_populates="social_accounts")


class OfficialApp(Timestamped, Base):
    __tablename__ = "official_apps"
    __table_args__ = (UniqueConstraint("platform", "package_identifier", name="uq_official_app_platform_package"), Index("ix_official_app_brand_platform", "brand_id", "platform"))
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    brand_id: Mapped[UUID] = mapped_column(ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    platform: Mapped[AppPlatform] = mapped_column(Enum(AppPlatform, name="app_platform", native_enum=False), nullable=False)
    app_name: Mapped[str] = mapped_column(String(255), nullable=False)
    package_identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    store_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    developer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    developer_identifier: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    logo_url: Mapped[Optional[str]] = mapped_column(String(2048))
    status: Mapped[BrandStatus] = mapped_column(Enum(BrandStatus, name="official_app_status", native_enum=False), default=BrandStatus.ACTIVE, nullable=False)
    brand: Mapped[Brand] = relationship(back_populates="apps")


class OfficialBrandAsset(Timestamped, Base):
    __tablename__ = "official_brand_assets"
    __table_args__ = (UniqueConstraint("brand_id", "asset_type", "value", name="uq_brand_asset_value"), Index("ix_brand_asset_brand_type", "brand_id", "asset_type"))
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    brand_id: Mapped[UUID] = mapped_column(ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_type: Mapped[AssetType] = mapped_column(Enum(AssetType, name="asset_type", native_enum=False), nullable=False)
    value: Mapped[str] = mapped_column(String(2048), nullable=False)
    label: Mapped[Optional[str]] = mapped_column(String(255))
    brand: Mapped[Brand] = relationship(back_populates="assets")


class SocialCandidate(Base):
    __tablename__ = "social_candidates"
    __table_args__ = (UniqueConstraint("brand_id", "platform", "external_identifier", name="uq_social_candidate_external"), Index("ix_social_candidate_platform_handle", "platform", "handle"))
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    brand_id: Mapped[UUID] = mapped_column(ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    platform: Mapped[SocialPlatform] = mapped_column(Enum(SocialPlatform, name="candidate_social_platform", native_enum=False), nullable=False)
    handle: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255))
    profile_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    followers_count: Mapped[Optional[int]] = mapped_column(Integer)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(2048))
    external_identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    account_created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    discovery_source: Mapped[str] = mapped_column(String(100), nullable=False)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status: Mapped[CandidateStatus] = mapped_column(Enum(CandidateStatus, name="social_candidate_status", native_enum=False), default=CandidateStatus.NEW, nullable=False)
    brand: Mapped[Brand] = relationship(back_populates="social_candidates")


class AppCandidate(Base):
    __tablename__ = "app_candidates"
    __table_args__ = (UniqueConstraint("brand_id", "platform", "package_identifier", name="uq_app_candidate_package"), Index("ix_app_candidate_platform_package", "platform", "package_identifier"))
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    brand_id: Mapped[UUID] = mapped_column(ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    platform: Mapped[AppPlatform] = mapped_column(Enum(AppPlatform, name="candidate_app_platform", native_enum=False), nullable=False)
    app_name: Mapped[str] = mapped_column(String(255), nullable=False)
    package_identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    store_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    developer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    developer_identifier: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    logo_url: Mapped[Optional[str]] = mapped_column(String(2048))
    rating: Mapped[Optional[float]] = mapped_column(Float)
    review_count: Mapped[Optional[int]] = mapped_column(Integer)
    downloads_text: Mapped[Optional[str]] = mapped_column(String(100))
    discovery_source: Mapped[str] = mapped_column(String(100), nullable=False)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status: Mapped[CandidateStatus] = mapped_column(Enum(CandidateStatus, name="app_candidate_status", native_enum=False), default=CandidateStatus.NEW, nullable=False)
    brand: Mapped[Brand] = relationship(back_populates="app_candidates")
