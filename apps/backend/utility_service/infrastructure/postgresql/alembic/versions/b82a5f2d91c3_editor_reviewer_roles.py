"""replace viewer with reviewer

Downgrade removes reviewer accounts because the legacy role set cannot
represent them safely.

Revision ID: b82a5f2d91c3
Revises: c6cef6320f1d
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b82a5f2d91c3"
down_revision: Union[str, Sequence[str], None] = "c6cef6320f1d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM "user".users
            WHERE role = 'viewer'
               OR email IN ('editor@example.com', 'viewer@example.com')
            """
        )
    )
    op.drop_constraint("user_role", "users", schema="user", type_="check")
    op.create_check_constraint(
        "user_role",
        "users",
        "role IN ('editor', 'reviewer')",
        schema="user",
    )
    op.add_column(
        "users",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        schema="user",
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM \"user\".users WHERE role = 'reviewer'"))
    op.drop_constraint("user_role", "users", schema="user", type_="check")
    op.create_check_constraint(
        "user_role",
        "users",
        "role IN ('viewer', 'editor')",
        schema="user",
    )
    op.drop_column("users", "is_active", schema="user")
