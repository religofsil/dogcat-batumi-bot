"""user daily reminder time

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-06

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, Sequence[str], None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "daily_reminder_time",
            sa.Time(),
            nullable=False,
            server_default="09:00:00",
        ),
    )
    op.alter_column("users", "daily_reminder_time", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "daily_reminder_time")
