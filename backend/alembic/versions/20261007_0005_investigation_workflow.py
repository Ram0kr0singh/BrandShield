"""add investigation workflow

Revision ID: 20261007_0005
Revises: 20261007_0004
"""
from alembic import op
import sqlalchemy as sa

revision = "20261007_0005"
down_revision = "20261007_0004"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("investigation_notes", sa.Column("id", sa.Uuid(), nullable=False), sa.Column("detection_id", sa.Uuid(), nullable=False), sa.Column("content", sa.Text(), nullable=False), sa.Column("actor", sa.String(length=80), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.ForeignKeyConstraint(["detection_id"], ["detections.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_investigation_note_detection_created", "investigation_notes", ["detection_id", "created_at"])
    op.create_table("investigation_activity", sa.Column("id", sa.Uuid(), nullable=False), sa.Column("detection_id", sa.Uuid(), nullable=False), sa.Column("event_type", sa.Enum("INVESTIGATION_CREATED", "STATUS_CHANGED", "NOTE_ADDED", "REMEDIATION_DRAFT_GENERATED", name="investigation_event_type", native_enum=False), nullable=False), sa.Column("previous_value", sa.String(length=80)), sa.Column("new_value", sa.String(length=80)), sa.Column("details", sa.JSON(), nullable=False), sa.Column("actor", sa.String(length=80), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.ForeignKeyConstraint(["detection_id"], ["detections.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_investigation_activity_detection_created", "investigation_activity", ["detection_id", "created_at"])
    op.create_table("remediation_drafts", sa.Column("id", sa.Uuid(), nullable=False), sa.Column("detection_id", sa.Uuid(), nullable=False), sa.Column("draft_type", sa.Enum("SOCIAL_PLATFORM", "APP_STORE", "DOMAIN_REGISTRAR", name="remediation_draft_type", native_enum=False), nullable=False), sa.Column("content", sa.Text(), nullable=False), sa.Column("evidence_summary", sa.JSON(), nullable=False), sa.Column("actor", sa.String(length=80), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.ForeignKeyConstraint(["detection_id"], ["detections.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_remediation_draft_detection_created", "remediation_drafts", ["detection_id", "created_at"])

def downgrade() -> None:
    op.drop_table("remediation_drafts")
    op.drop_table("investigation_activity")
    op.drop_table("investigation_notes")
