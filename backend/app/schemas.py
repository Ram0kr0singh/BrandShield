from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import AppPlatform, AssetType, BrandStatus, CandidateStatus, DetectionCandidateType, DetectionStatus, InvestigationEventType, MonitoringRunStatus, RemediationDraftType, Severity, SocialPlatform, ThreatType


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BrandCreate(Schema):
    name: str = Field(min_length=1, max_length=160)
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=160)
    description: Optional[str] = None
    official_domain: Optional[str] = Field(default=None, max_length=253)
    logo_url: Optional[str] = None
    status: BrandStatus = BrandStatus.ACTIVE

    @field_validator("official_domain")
    @classmethod
    def domain_has_no_scheme_or_path(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and ("/" in value or ":" in value or "." not in value):
            raise ValueError("official_domain must be a hostname such as example.com")
        return value.lower() if value else value


class BrandRead(BrandCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime


class OfficialSocialCreate(Schema):
    platform: SocialPlatform
    handle: str = Field(min_length=1, max_length=255)
    profile_url: str
    display_name: Optional[str] = None
    verified: bool = False
    description: Optional[str] = None
    status: BrandStatus = BrandStatus.ACTIVE


class OfficialSocialRead(OfficialSocialCreate):
    id: UUID
    brand_id: UUID
    created_at: datetime
    updated_at: datetime


class OfficialAppCreate(Schema):
    platform: AppPlatform
    app_name: str = Field(min_length=1, max_length=255)
    package_identifier: str = Field(min_length=1, max_length=255)
    store_url: str
    developer_name: str = Field(min_length=1, max_length=255)
    developer_identifier: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    status: BrandStatus = BrandStatus.ACTIVE


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
