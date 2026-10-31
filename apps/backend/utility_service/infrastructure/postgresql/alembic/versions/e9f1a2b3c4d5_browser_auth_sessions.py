"""Родительские сессии браузеров; завершение старых credentials.

Revision ID: e9f1a2b3c4d5
Revises: c8e3f0a5b7d9
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e9f1a2b3c4d5"
down_revision: Union[str, Sequence[str], None] = "c8e3f0a5b7d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def end_credentials() -> None:
    op.execute(
        """
        UPDATE "user".auth_sessions
        SET revoked_at = COALESCE(revoked_at, now())
        WHERE revoked_at IS NULL
        """
    )
    op.execute(
        """
        UPDATE "user".websocket_tickets
        SET used_at = COALESCE(used_at, now())
        WHERE used_at IS NULL
        """
    )


def upgrade() -> None:
    op.create_table(
        "browser_auth_sessions",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "id",
            "user_id",
            name="uq_browser_auth_sessions_id_user_id",
        ),
        schema="user",
    )
    for column in ("user_id", "expires_at"):
        op.create_index(
            f"ix_browser_auth_sessions_{column}",
            "browser_auth_sessions",
            [column],
            schema="user",
        )
    for table in ("auth_sessions", "websocket_tickets"):
        op.add_column(
            table,
            sa.Column(
                "browser_session_id",
                sa.UUID(),
                nullable=True,
            ),
            schema="user",
        )
        # У legacy rows нет надёжной идентичности браузера. Каждая получает
        # отдельного отозванного родителя, включая tickets без refresh row.
        op.execute(
            f"""
            UPDATE "user".{table}
            SET browser_session_id = gen_random_uuid()
            """
        )
        op.execute(
            f"""
            INSERT INTO "user".browser_auth_sessions (
                id,
                user_id,
                created_at,
                expires_at,
                revoked_at
            )
            SELECT
                browser_session_id,
                user_id,
                created_at,
                expires_at,
                now()
            FROM "user".{table}
            """
        )
        op.alter_column(
            table,
            "browser_session_id",
            nullable=False,
            schema="user",
        )
        op.create_foreign_key(
            f"fk_{table}_browser_session_owner",
            table,
            "browser_auth_sessions",
            ["browser_session_id", "user_id"],
            ["id", "user_id"],
            source_schema="user",
            referent_schema="user",
        )
        op.create_index(
            f"ix_{table}_browser_session_id",
            table,
            ["browser_session_id"],
            schema="user",
        )
    end_credentials()


def downgrade() -> None:
    # Старое приложение не проверяет parent: активные credentials тоже должны
    # завершиться до удаления связей. Исторические timestamps сохраняются.
    end_credentials()
    for table in ("websocket_tickets", "auth_sessions"):
        op.drop_index(
            f"ix_{table}_browser_session_id",
            table_name=table,
            schema="user",
        )
        op.drop_constraint(
            f"fk_{table}_browser_session_owner",
            table,
            type_="foreignkey",
            schema="user",
        )
        op.drop_column(
            table,
            "browser_session_id",
            schema="user",
        )
    for column in ("expires_at", "user_id"):
        op.drop_index(
            f"ix_browser_auth_sessions_{column}",
            table_name="browser_auth_sessions",
            schema="user",
        )
    op.drop_table(
        "browser_auth_sessions",
        schema="user",
    )
