"""cat photo and organization

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-05

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    org_enum = sa.Enum(
        "catebi",
        "dogcat_batumi",
        "dogcat_tbilisi",
        "none",
        name="cat_organization_enum",
        native_enum=False,
        length=32,
    )
    org_enum.create(op.get_bind(), checkfirst=True)
    op.add_column("cats", sa.Column("photo_url", sa.String(length=1024), nullable=True))
    op.add_column(
        "cats",
        sa.Column(
            "organization",
            org_enum,
            nullable=False,
            server_default="none",
        ),
    )


def downgrade() -> None:
    op.drop_column("cats", "organization")
    op.drop_column("cats", "photo_url")
    sa.Enum(name="cat_organization_enum").drop(op.get_bind(), checkfirst=True)
