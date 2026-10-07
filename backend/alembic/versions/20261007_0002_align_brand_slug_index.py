"""align brand slug uniqueness with SQLAlchemy metadata

Revision ID: 20261007_0002
Revises: 20261007_0001
Create Date: 2026-10-07
"""

from typing import Sequence, Union

from alembic import op

revision: str = "20261007_0002"
down_revision: Union[str, Sequence[str], None] = "20261007_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("brands_slug_key", "brands", type_="unique")
    op.drop_index("ix_brands_slug", table_name="brands")
    op.create_index("ix_brands_slug", "brands", ["slug"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_brands_slug", table_name="brands")
    op.create_unique_constraint("brands_slug_key", "brands", ["slug"])
    op.create_index("ix_brands_slug", "brands", ["slug"])
