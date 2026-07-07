"""compatibility checkpoint for sprint1 schema boundaries

Revision ID: f2b3c4d5e6a7
Revises: a8c1f2d3e4b5

The clean production-like baseline creates work_order AOI/work-order tables in
e4b7a9c2d5f8 and edit/default-state tables in a8c1f2d3e4b5. Old dev/demo
volumes are intentionally unsupported, so this revision no longer performs
legacy table cleanup or schema repair.
"""

from typing import Sequence, Union


revision: str = "f2b3c4d5e6a7"
down_revision: Union[str, Sequence[str], None] = "a8c1f2d3e4b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
