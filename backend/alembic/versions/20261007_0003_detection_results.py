"""add persisted deterministic detection results

Revision ID: 20261007_0003
Revises: 20261007_0002
Create Date: 2026-10-07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261007_0003"
down_revision: Union[str, Sequence[str], None] = "20261007_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "detections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("brand_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_type", sa.String(20), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("threat_type", sa.String(30)),
        sa.Column("severity", sa.String(10), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("official_match", sa.Boolean(), nullable=False),
        sa.Column("lookalike_detected", sa.Boolean(), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("candidate_type", "candidate_id", name="uq_detection_candidate"),
    )
    op.create_index("ix_detections_brand_id", "detections", ["brand_id"])
    op.create_index("ix_detections_candidate_id", "detections", ["candidate_id"])
    op.create_index("ix_detection_brand_severity", "detections", ["brand_id", "severity"])
    op.create_table(
        "detection_evidence",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("detection_id", sa.Uuid(), nullable=False),
        sa.Column("signal_type", sa.String(80), nullable=False),
        sa.Column("available", sa.Boolean(), nullable=False),
        sa.Column("score", sa.Float()),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["detection_id"], ["detections.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_detection_evidence_detection_id", "detection_evidence", ["detection_id"])
    op.create_index("ix_detection_evidence_detection_priority", "detection_evidence", ["detection_id", "priority"])


def downgrade() -> None:
    op.drop_table("detection_evidence")
    op.drop_table("detections")
