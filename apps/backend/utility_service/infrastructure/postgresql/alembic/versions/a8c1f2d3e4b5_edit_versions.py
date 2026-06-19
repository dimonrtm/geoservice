"""add edit versions

Revision ID: a8c1f2d3e4b5
Revises: e4b7a9c2d5f8
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "a8c1f2d3e4b5"
down_revision: Union[str, Sequence[str], None] = "e4b7a9c2d5f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_STATE_ID = "11111111-1111-4111-8111-111111111111"


def upgrade() -> None:
    op.create_table(
        "default_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("current_revision", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "current_revision >= 1",
            name="ck_default_states_current_revision_positive",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_default_states_name"),
        schema="utility_network",
    )
    op.execute(
        sa.text(
            f"""
            INSERT INTO utility_network.default_states (id, name, current_revision)
            VALUES ('{DEFAULT_STATE_ID}', 'default', 1)
            ON CONFLICT (name) DO NOTHING
            """
        )
    )
    op.create_table(
        "edit_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("work_order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("base_revision", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "open",
                name="edit_version_status",
                native_enum=False,
                create_constraint=False,
                length=16,
            ),
            server_default="open",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_opened_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "base_revision >= 1",
            name="ck_edit_versions_base_revision_positive",
        ),
        sa.CheckConstraint(
            "status IN ('open')",
            name="ck_edit_versions_status",
        ),
        sa.ForeignKeyConstraint(
            ["work_order_id"],
            ["utility_network.work_orders.id"],
            name="fk_edit_versions_work_order",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name="fk_edit_versions_owner",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="utility_network",
    )
    op.create_index(
        "uq_edit_versions_open_work_order",
        "edit_versions",
        ["work_order_id"],
        unique=True,
        schema="utility_network",
        postgresql_where=sa.text("status = 'open'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_edit_versions_open_work_order",
        table_name="edit_versions",
        schema="utility_network",
    )
    op.drop_table("edit_versions", schema="utility_network")
    op.drop_table("default_states", schema="utility_network")
