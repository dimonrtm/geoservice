"""add work orders

Revision ID: e4b7a9c2d5f8
Revises: d3a01f4e9c21
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "e4b7a9c2d5f8"
down_revision: Union[str, Sequence[str], None] = "d3a01f4e9c21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "work_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "assigned",
                "in_progress",
                name="work_order_status",
                native_enum=False,
                create_constraint=False,
                length=16,
            ),
            server_default="assigned",
            nullable=False,
        ),
        sa.Column("assignee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("aoi_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("feeder_id", postgresql.UUID(as_uuid=True), nullable=False),
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
            "status IN ('assigned', 'in_progress')",
            name="ck_work_orders_status",
        ),
        sa.ForeignKeyConstraint(
            ["assignee_id"],
            ["users.id"],
            name="fk_work_orders_assignee",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["aoi_id"],
            ["utility_network.aois.id"],
            name="fk_work_orders_aoi",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["feeder_id"],
            ["utility_network.feeders.id"],
            name="fk_work_orders_feeder",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_work_orders_code"),
        schema="utility_network",
    )
    op.create_index(
        "ix_work_orders_assignee_id",
        "work_orders",
        ["assignee_id"],
        unique=False,
        schema="utility_network",
    )
    op.create_index(
        "ix_work_orders_status",
        "work_orders",
        ["status"],
        unique=False,
        schema="utility_network",
    )
    op.create_index(
        "ix_work_orders_aoi_id",
        "work_orders",
        ["aoi_id"],
        unique=False,
        schema="utility_network",
    )
    op.create_index(
        "ix_work_orders_feeder_id",
        "work_orders",
        ["feeder_id"],
        unique=False,
        schema="utility_network",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_work_orders_feeder_id",
        table_name="work_orders",
        schema="utility_network",
    )
    op.drop_index(
        "ix_work_orders_aoi_id",
        table_name="work_orders",
        schema="utility_network",
    )
    op.drop_index(
        "ix_work_orders_status",
        table_name="work_orders",
        schema="utility_network",
    )
    op.drop_index(
        "ix_work_orders_assignee_id",
        table_name="work_orders",
        schema="utility_network",
    )
    op.drop_table("work_orders", schema="utility_network")
