"""add BrandShield domain tables

Revision ID: 20261007_0001
Revises:
Create Date: 2026-10-07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261007_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _timestamps() -> list[sa.Column]:
    return [sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False)]


def upgrade() -> None:
    op.create_table("brands", sa.Column("id", sa.Uuid(), nullable=False), sa.Column("name", sa.String(160), nullable=False), sa.Column("slug", sa.String(160), nullable=False), sa.Column("description", sa.Text()), sa.Column("official_domain", sa.String(253)), sa.Column("logo_url", sa.String(2048)), sa.Column("status", sa.String(20), nullable=False), *_timestamps(), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("official_domain"), sa.UniqueConstraint("slug"))
    op.create_index("ix_brands_slug", "brands", ["slug"])
    op.create_table("official_social_accounts", sa.Column("id", sa.Uuid(), nullable=False), sa.Column("brand_id", sa.Uuid(), nullable=False), sa.Column("platform", sa.String(20), nullable=False), sa.Column("handle", sa.String(255), nullable=False), sa.Column("profile_url", sa.String(2048), nullable=False), sa.Column("display_name", sa.String(255)), sa.Column("verified", sa.Boolean(), nullable=False), sa.Column("description", sa.Text()), sa.Column("status", sa.String(20), nullable=False), *_timestamps(), sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("platform", "handle", name="uq_official_social_platform_handle"))
    op.create_index("ix_official_social_accounts_brand_id", "official_social_accounts", ["brand_id"])
    op.create_index("ix_official_social_brand_platform", "official_social_accounts", ["brand_id", "platform"])
    op.create_table("official_apps", sa.Column("id", sa.Uuid(), nullable=False), sa.Column("brand_id", sa.Uuid(), nullable=False), sa.Column("platform", sa.String(30), nullable=False), sa.Column("app_name", sa.String(255), nullable=False), sa.Column("package_identifier", sa.String(255), nullable=False), sa.Column("store_url", sa.String(2048), nullable=False), sa.Column("developer_name", sa.String(255), nullable=False), sa.Column("developer_identifier", sa.String(255)), sa.Column("description", sa.Text()), sa.Column("logo_url", sa.String(2048)), sa.Column("status", sa.String(20), nullable=False), *_timestamps(), sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("platform", "package_identifier", name="uq_official_app_platform_package"))
    op.create_index("ix_official_apps_brand_id", "official_apps", ["brand_id"])
    op.create_index("ix_official_app_brand_platform", "official_apps", ["brand_id", "platform"])
    op.create_table("official_brand_assets", sa.Column("id", sa.Uuid(), nullable=False), sa.Column("brand_id", sa.Uuid(), nullable=False), sa.Column("asset_type", sa.String(30), nullable=False), sa.Column("value", sa.String(2048), nullable=False), sa.Column("label", sa.String(255)), *_timestamps(), sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("brand_id", "asset_type", "value", name="uq_brand_asset_value"))
    op.create_index("ix_official_brand_assets_brand_id", "official_brand_assets", ["brand_id"])
    op.create_index("ix_brand_asset_brand_type", "official_brand_assets", ["brand_id", "asset_type"])
    op.create_table("social_candidates", sa.Column("id", sa.Uuid(), nullable=False), sa.Column("brand_id", sa.Uuid(), nullable=False), sa.Column("platform", sa.String(20), nullable=False), sa.Column("handle", sa.String(255), nullable=False), sa.Column("display_name", sa.String(255)), sa.Column("profile_url", sa.String(2048), nullable=False), sa.Column("description", sa.Text()), sa.Column("followers_count", sa.Integer()), sa.Column("verified", sa.Boolean(), nullable=False), sa.Column("avatar_url", sa.String(2048)), sa.Column("external_identifier", sa.String(255), nullable=False), sa.Column("account_created_at", sa.DateTime(timezone=True)), sa.Column("discovery_source", sa.String(100), nullable=False), sa.Column("discovered_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("brand_id", "platform", "external_identifier", name="uq_social_candidate_external"))
    op.create_index("ix_social_candidates_brand_id", "social_candidates", ["brand_id"])
    op.create_index("ix_social_candidate_platform_handle", "social_candidates", ["platform", "handle"])
    op.create_table("app_candidates", sa.Column("id", sa.Uuid(), nullable=False), sa.Column("brand_id", sa.Uuid(), nullable=False), sa.Column("platform", sa.String(30), nullable=False), sa.Column("app_name", sa.String(255), nullable=False), sa.Column("package_identifier", sa.String(255), nullable=False), sa.Column("store_url", sa.String(2048), nullable=False), sa.Column("developer_name", sa.String(255), nullable=False), sa.Column("developer_identifier", sa.String(255)), sa.Column("description", sa.Text()), sa.Column("logo_url", sa.String(2048)), sa.Column("rating", sa.Float()), sa.Column("review_count", sa.Integer()), sa.Column("downloads_text", sa.String(100)), sa.Column("discovery_source", sa.String(100), nullable=False), sa.Column("discovered_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("brand_id", "platform", "package_identifier", name="uq_app_candidate_package"))
    op.create_index("ix_app_candidates_brand_id", "app_candidates", ["brand_id"])
    op.create_index("ix_app_candidate_platform_package", "app_candidates", ["platform", "package_identifier"])


def downgrade() -> None:
    op.drop_table("app_candidates")
    op.drop_table("social_candidates")
    op.drop_table("official_brand_assets")
    op.drop_table("official_apps")
    op.drop_table("official_social_accounts")
    op.drop_table("brands")
