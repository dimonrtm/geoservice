"""add auth sessions

Revision ID: f8a7b6c5d4e3
Revises: a6f4c9b8d2e1
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f8a7b6c5d4e3"
down_revision: Union[str, Sequence[str], None] = "a6f4c9b8d2e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_token_hash", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rotated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "session_token_hash",
            name="uq_auth_sessions_session_token_hash",
        ),
        schema="user",
    )
    op.create_index(
        "ix_auth_sessions_expires_at",
        "auth_sessions",
        ["expires_at"],
        schema="user",
    )
    op.create_index(
        "ix_auth_sessions_user_id",
        "auth_sessions",
        ["user_id"],
        schema="user",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_auth_sessions_user_id",
        table_name="auth_sessions",
        schema="user",
    )
    op.drop_index(
        "ix_auth_sessions_expires_at",
        table_name="auth_sessions",
        schema="user",
    )
    op.drop_table("auth_sessions", schema="user")
