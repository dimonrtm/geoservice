"""compatibility checkpoint for editor/reviewer roles

Revision ID: b82a5f2d91c3
Revises: c6cef6320f1d

The clean production-like baseline now creates user.users with the target
editor/reviewer role set and is_active in c6cef6320f1d. This revision remains
in the Alembic graph so existing revision order is stable, but it must not
delete users or rewrite role constraints during upgrade.
"""

from typing import Sequence, Union


revision: str = "b82a5f2d91c3"
down_revision: Union[str, Sequence[str], None] = "c6cef6320f1d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
