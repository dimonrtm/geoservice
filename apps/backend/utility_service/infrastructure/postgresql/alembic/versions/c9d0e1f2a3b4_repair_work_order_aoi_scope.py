"""compatibility checkpoint for work-order AOI scope repair

Revision ID: c9d0e1f2a3b4
Revises: f2b3c4d5e6a7

The clean production-like baseline creates work_order.aois and
work_order.work_orders.aoi_id in e4b7a9c2d5f8. Old stamped dev volumes are not a
supported migration path, so this revision no longer creates fallback AOI rows
or drops legacy utility_network.aois.
"""

from typing import Sequence, Union


revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, Sequence[str], None] = "f2b3c4d5e6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
