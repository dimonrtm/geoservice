"""add websocket tickets

Revision ID: a6f4c9b8d2e1
Revises: c9d0e1f2a3b4
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a6f4c9b8d2e1"
down_revision: Union[str, Sequence[str], None] = "c9d0e1f2a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "websocket_tickets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("ticket_hash", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("layer_id", sa.UUID(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticket_hash", name="uq_websocket_tickets_ticket_hash"),
        schema="user",
    )
    op.create_index(
        "ix_websocket_tickets_expires_at",
        "websocket_tickets",
        ["expires_at"],
        schema="user",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_websocket_tickets_expires_at",
        table_name="websocket_tickets",
        schema="user",
    )
    op.drop_table("websocket_tickets", schema="user")
