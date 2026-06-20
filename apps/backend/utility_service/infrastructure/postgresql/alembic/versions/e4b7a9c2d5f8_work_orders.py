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
    op.execute(sa.text("CREATE SCHEMA work_order"))
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
        sa.Column("assignee_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_work_orders_code"),
        schema="work_order",
    )
    op.create_index(
        "ix_work_orders_assignee_user_id",
        "work_orders",
        ["assignee_user_id"],
        unique=False,
        schema="work_order",
    )
    op.create_index(
        "ix_work_orders_created_by_user_id",
        "work_orders",
        ["created_by_user_id"],
        unique=False,
        schema="work_order",
    )
    op.create_index(
        "ix_work_orders_status",
        "work_orders",
        ["status"],
        unique=False,
        schema="work_order",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_work_orders_status",
        table_name="work_orders",
        schema="work_order",
    )
    op.drop_index(
        "ix_work_orders_created_by_user_id",
        table_name="work_orders",
        schema="work_order",
    )
    op.drop_index(
        "ix_work_orders_assignee_user_id",
        table_name="work_orders",
        schema="work_order",
    )
    op.drop_table("work_orders", schema="work_order")
    op.execute(sa.text("DROP SCHEMA work_order"))
