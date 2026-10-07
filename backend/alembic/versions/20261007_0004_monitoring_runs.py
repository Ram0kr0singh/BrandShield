"""add monitoring runs

Revision ID: 20261007_0004
Revises: 20261007_0003
"""
from alembic import op
import sqlalchemy as sa

revision = "20261007_0004"
down_revision = "20261007_0003"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("monitoring_runs",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("brand_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.Enum("RUNNING", "COMPLETED", "FAILED", name="monitoring_run_status", native_enum=False), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("candidate_count", sa.Integer(), nullable=False), sa.Column("social_candidate_count", sa.Integer(), nullable=False), sa.Column("app_candidate_count", sa.Integer(), nullable=False),
        sa.Column("safe_count", sa.Integer(), nullable=False), sa.Column("low_count", sa.Integer(), nullable=False), sa.Column("medium_count", sa.Integer(), nullable=False), sa.Column("high_count", sa.Integer(), nullable=False), sa.Column("critical_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_monitoring_run_brand_created", "monitoring_runs", ["brand_id", "created_at"])
    op.create_index("ix_monitoring_runs_brand_id", "monitoring_runs", ["brand_id"])

def downgrade() -> None:
    op.drop_table("monitoring_runs")
