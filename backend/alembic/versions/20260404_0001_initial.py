"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("locale", sa.String(length=8), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
    )
    op.create_index(op.f("ix_users_telegram_id"), "users", ["telegram_id"], unique=False)

    op.create_table(
        "cats",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("weight_kg", sa.Numeric(precision=6, scale=3), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cats_user_id"), "cats", ["user_id"], unique=False)

    scenario_type = sa.Enum(
        "new_capture",
        "adopted_home",
        "post_prep",
        "potential_adopter",
        "sterilization",
        name="scenario_type_enum",
        native_enum=False,
        length=32,
    )
    scenario_status = sa.Enum(
        "active", "completed", "cancelled", name="scenario_status_enum", native_enum=False, length=32
    )
    scenario_type.create(op.get_bind(), checkfirst=True)
    scenario_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "scenario_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cat_id", sa.Integer(), nullable=False),
        sa.Column("scenario_type", scenario_type, nullable=False),
        sa.Column("status", scenario_status, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["cat_id"], ["cats.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_scenario_runs_cat_id"), "scenario_runs", ["cat_id"], unique=False)

    op.create_table(
        "reminders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cat_id", sa.Integer(), nullable=False),
        sa.Column("scenario_run_id", sa.Integer(), nullable=True),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("message_key", sa.String(length=128), nullable=False),
        sa.Column("run_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled", sa.Boolean(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["cat_id"], ["cats.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scenario_run_id"], ["scenario_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reminders_cat_id"), "reminders", ["cat_id"], unique=False)
    op.create_index(op.f("ix_reminders_kind"), "reminders", ["kind"], unique=False)
    op.create_index(op.f("ix_reminders_run_at"), "reminders", ["run_at"], unique=False)
    op.create_index(
        op.f("ix_reminders_scenario_run_id"), "reminders", ["scenario_run_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_reminders_scenario_run_id"), table_name="reminders")
    op.drop_index(op.f("ix_reminders_run_at"), table_name="reminders")
    op.drop_index(op.f("ix_reminders_kind"), table_name="reminders")
    op.drop_index(op.f("ix_reminders_cat_id"), table_name="reminders")
    op.drop_table("reminders")
    op.drop_index(op.f("ix_scenario_runs_cat_id"), table_name="scenario_runs")
    op.drop_table("scenario_runs")
    op.drop_index(op.f("ix_cats_user_id"), table_name="cats")
    op.drop_table("cats")
    op.drop_index(op.f("ix_users_telegram_id"), table_name="users")
    op.drop_table("users")
    sa.Enum(name="scenario_status_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="scenario_type_enum").drop(op.get_bind(), checkfirst=True)
