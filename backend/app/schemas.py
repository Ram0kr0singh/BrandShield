from __future__ import annotations

from datetime import datetime
import re
from typing import Optional
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from app.models import AppPlatform, AssetType, BrandStatus, CandidateStatus, DetectionCandidateType, DetectionStatus, InvestigationEventType, MonitoringRunStatus, RemediationDraftType, Severity, SocialPlatform, ThreatType
from app.logos import STATIC_LOGO_PREFIX


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


def _validate_domain(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    value = value.strip().lower()
    if value.endswith(".."):
        raise ValueError("Enter a hostname such as example.com, without a scheme or path")
    value = value.removesuffix(".")
    if len(value) > 253 or not value:
        raise ValueError("Enter a hostname such as example.com, without a scheme or path")
    labels = value.split(".")
    if len(labels) < 2 or any(
        not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
        for label in labels
    ):
        raise ValueError("Enter a hostname such as example.com, without a scheme or path")
    return value


def _validate_http_url(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    value = value.strip()
    try:
        parsed = urlsplit(value)
        valid = (
            parsed.scheme in {"http", "https"}
            and bool(parsed.hostname)
            and not parsed.username
            and not parsed.password
            and not any(character.isspace() for character in value)
        )
        if parsed.port is not None:
            valid = valid and 1 <= parsed.port <= 65535
    except ValueError:
        valid = False
    if not valid:
        raise ValueError("Enter a complete http:// or https:// URL")
    return value


def _validate_logo_reference(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    value = value.strip()
    if value.startswith(STATIC_LOGO_PREFIX):
        relative = value.removeprefix(STATIC_LOGO_PREFIX)
        parts = relative.split("/")
        if parts and all(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", part) for part in parts):
            return value
    return _validate_http_url(value)


def _validate_handle(value: str) -> str:
    value = value.strip().removeprefix("@")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,254}", value):
        raise ValueError("Use letters, numbers, dots, underscores, or hyphens; do not include @")
    return value


def _validate_package_identifier(value: str, platform: AppPlatform) -> str:
    value = value.strip()
    if platform == AppPlatform.APPLE_APP_STORE and value.isdigit():
        return value
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+", value):
        raise ValueError("Use a reverse-domain package ID, for example com.example.app")
    return value


class BrandCreate(Schema):
    name: str = Field(min_length=1, max_length=160)
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=160)
    description: Optional[str] = None
    official_domain: Optional[str] = Field(default=None, max_length=253)
    logo_url: Optional[str] = Field(default=None, max_length=2048)
    status: BrandStatus = BrandStatus.ACTIVE

    @field_validator("name")
    @classmethod
    def brand_name_is_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Brand name cannot be empty")
        return value

    @field_validator("official_domain")
    @classmethod
    def domain_has_no_scheme_or_path(cls, value: Optional[str]) -> Optional[str]:
        return _validate_domain(value)

    @field_validator("logo_url")
    @classmethod
    def logo_is_http_url(cls, value: Optional[str]) -> Optional[str]:
        return _validate_logo_reference(value)


class BrandUpdate(Schema):
    name: Optional[str] = Field(default=None, min_length=1, max_length=160)
    description: Optional[str] = None
    official_domain: Optional[str] = Field(default=None, max_length=253)
    logo_url: Optional[str] = Field(default=None, max_length=2048)

    @field_validator("name")
    @classmethod
    def brand_name_is_not_blank(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Brand name cannot be empty")
        return value

    @field_validator("official_domain")
    @classmethod
    def domain_has_no_scheme_or_path(cls, value: Optional[str]) -> Optional[str]:
        return _validate_domain(value)

    @field_validator("logo_url")
    @classmethod
    def logo_is_http_url(cls, value: Optional[str]) -> Optional[str]:
        return _validate_logo_reference(value)


class BrandRead(BrandCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime


class OfficialSocialCreate(Schema):
    platform: SocialPlatform
    handle: str = Field(min_length=1, max_length=255)
    profile_url: str = Field(max_length=2048)
    display_name: Optional[str] = Field(default=None, max_length=255)
    verified: bool = False
    description: Optional[str] = None
    status: BrandStatus = BrandStatus.ACTIVE

    @field_validator("handle")
    @classmethod
    def valid_handle(cls, value: str) -> str:
        return _validate_handle(value)

    @field_validator("profile_url")
    @classmethod
    def valid_profile_url(cls, value: str) -> str:
        return _validate_http_url(value) or value


class OfficialSocialRead(OfficialSocialCreate):
    id: UUID
    brand_id: UUID
    created_at: datetime
    updated_at: datetime


class OfficialAppCreate(Schema):
    platform: AppPlatform
    app_name: str = Field(min_length=1, max_length=255)
    package_identifier: str = Field(min_length=1, max_length=255)
    store_url: str = Field(max_length=2048)
    developer_name: str = Field(min_length=1, max_length=255)
    developer_identifier: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = Field(default=None, max_length=2048)
    status: BrandStatus = BrandStatus.ACTIVE

    @field_validator("app_name", "developer_name")
    @classmethod
    def required_app_text_is_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty")
        return value

    @field_validator("package_identifier")
    @classmethod
    def valid_package_identifier(cls, value: str, info: ValidationInfo) -> str:
        platform = info.data.get("platform")
        if platform is None:
            return value
        return _validate_package_identifier(value, platform)

    @field_validator("store_url")
    @classmethod
    def valid_store_url(cls, value: str) -> str:
        return _validate_http_url(value) or value

    @field_validator("logo_url")
    @classmethod
    def valid_logo_url(cls, value: Optional[str]) -> Optional[str]:
        return _validate_logo_reference(value)


class OfficialAppRead(OfficialAppCreate):
    id: UUID
    brand_id: UUID
    created_at: datetime
    updated_at: datetime


class AssetRead(Schema):
    id: UUID
    brand_id: UUID
    asset_type: AssetType
    value: str
    label: Optional[str]
    created_at: datetime
    updated_at: datetime


class AssetCreate(Schema):
    asset_type: AssetType
    value: str = Field(min_length=1, max_length=2048)
    label: Optional[str] = Field(default=None, max_length=255)

    @field_validator("value")
    @classmethod
    def validate_asset_value(cls, value: str, info: ValidationInfo) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Asset value cannot be empty")
        asset_type = info.data.get("asset_type")
        if asset_type == AssetType.DOMAIN:
            return _validate_domain(value) or value
        if asset_type in {AssetType.LOGO, AssetType.SOCIAL_ACCOUNT, AssetType.MOBILE_APP}:
            return (_validate_logo_reference(value) if asset_type == AssetType.LOGO else _validate_http_url(value)) or value
        return value


class SocialCandidateCreate(Schema):
    platform: SocialPlatform
    handle: str = Field(min_length=1, max_length=255)
    display_name: Optional[str] = None
    profile_url: str
    description: Optional[str] = None
    followers_count: Optional[int] = Field(default=None, ge=0)
    verified: bool = False
    avatar_url: Optional[str] = None
    external_identifier: str = Field(min_length=1, max_length=255)
    account_created_at: Optional[datetime] = None
    discovery_source: str = Field(min_length=1, max_length=100)
    status: CandidateStatus = CandidateStatus.NEW


class SocialCandidateRead(SocialCandidateCreate):
    id: UUID
    brand_id: UUID
    discovered_at: datetime


class AppCandidateCreate(Schema):
    platform: AppPlatform
    app_name: str = Field(min_length=1, max_length=255)
    package_identifier: str = Field(min_length=1, max_length=255)
    store_url: str
    developer_name: str = Field(min_length=1, max_length=255)
    developer_identifier: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    rating: Optional[float] = Field(default=None, ge=0, le=5)
    review_count: Optional[int] = Field(default=None, ge=0)
    downloads_text: Optional[str] = None
    discovery_source: str = Field(min_length=1, max_length=100)
    status: CandidateStatus = CandidateStatus.NEW


class AppCandidateRead(AppCandidateCreate):
    id: UUID
    brand_id: UUID
    discovered_at: datetime


class EvidenceRead(Schema):
    id: UUID
    signal_type: str
    available: bool
    score: Optional[float]
    priority: int
    details: dict


class DetectionRead(Schema):
    id: UUID
    brand_id: UUID
    candidate_type: DetectionCandidateType
    candidate_id: UUID
    status: DetectionStatus
    threat_type: Optional[ThreatType]
    severity: Severity
    risk_score: float
    confidence: float
    official_match: bool
    lookalike_detected: bool
    detected_at: datetime
    created_at: datetime
    updated_at: datetime
    evidence: list[EvidenceRead]
    candidate: Optional[dict] = None


class NameAnalysisRequest(Schema):
    official_name: str = Field(min_length=1, max_length=255)
    candidate_name: str = Field(min_length=1, max_length=255)


class NameAnalysisRead(Schema):
    official_name: str
    candidate_name: str
    normalized_official: str
    normalized_candidate: str
    similarity: float
    detected: bool
    transformations: list[dict]


class ScanRead(Schema):
    analyzed: int
    created_or_updated: int
    by_severity: dict[str, int]


class MonitoringScanRequest(Schema):
    brand_id: UUID


class SourceWarning(Schema):
    id: str
    name: str
    status: str
    message: str


class MonitoringRunRead(Schema):
    id: UUID
    brand_id: UUID
    status: MonitoringRunStatus
    started_at: datetime
    completed_at: Optional[datetime]
    candidate_count: int
    social_candidate_count: int
    app_candidate_count: int
    safe_count: int
    low_count: int
    medium_count: int
    high_count: int
    critical_count: int
    created_at: datetime
    source_warnings: list[SourceWarning] = Field(default_factory=list)


class DashboardOverview(Schema):
    brand: dict
    summary: dict[str, int]
    risk_distribution: list[dict]
    source_distribution: list[dict]
    threat_type_distribution: list[dict]
    recent_threats: list[dict]
    last_scan: Optional[dict]


class StatusUpdate(Schema):
    status: DetectionStatus


class NoteCreate(Schema):
    content: str = Field(min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def content_is_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("content must not be blank")
        return value.strip()


class InvestigationNoteRead(Schema):
    id: UUID
    content: str
    actor: str
    created_at: datetime


class InvestigationActivityRead(Schema):
    id: UUID
    event_type: InvestigationEventType
    previous_value: Optional[str]
    new_value: Optional[str]
    details: dict
    actor: str
    created_at: datetime


class RemediationDraftCreate(Schema):
    draft_type: RemediationDraftType


class RemediationDraftRead(Schema):
    id: UUID
    draft_type: RemediationDraftType
    content: str
    evidence_summary: list
    actor: str
    created_at: datetime


class InvestigationRead(Schema):
    detection_id: UUID
    status: DetectionStatus
    notes: list[InvestigationNoteRead]
    activity: list[InvestigationActivityRead]
    drafts: list[RemediationDraftRead]


class AnalystEvidenceRead(Schema):
    signal_type: str
    summary: str
    score: Optional[float]
    details: dict


class AnalystAnalysisRead(Schema):
    summary: str
    risk_rationale: str
    key_evidence: list[AnalystEvidenceRead]
    uncertainties: list[str]
    recommended_actions: list[str]
    confidence: str
    source_facts: dict
    generated_at: datetime
    provider: str
