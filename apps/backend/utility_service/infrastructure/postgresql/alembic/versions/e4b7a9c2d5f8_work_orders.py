"""add work orders

Revision ID: e4b7a9c2d5f8
Revises: d3a01f4e9c21
"""

from typing import Sequence, Union

import geoalchemy2
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
        "aois",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "geometry",
            geoalchemy2.Geometry(
                geometry_type="GEOMETRY",
                srid=4326,
                spatial_index=False,
            ),
            nullable=False,
        ),
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
            "NOT ST_IsEmpty(geometry)",
            name="ck_aois_geometry_not_empty",
        ),
        sa.CheckConstraint(
            "ST_IsValid(geometry)",
            name="ck_aois_geometry_valid",
        ),
        sa.CheckConstraint(
            "ST_SRID(geometry) = 4326",
            name="ck_aois_geometry_srid",
        ),
        sa.CheckConstraint(
            "GeometryType(geometry) IN ('POLYGON', 'MULTIPOLYGON')",
            name="ck_aois_geometry_type",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="work_order",
    )
    op.create_index(
        "ix_aois_geometry",
        "aois",
        ["geometry"],
        unique=False,
        schema="work_order",
        postgresql_using="gist",
    )

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
        sa.Column("aoi_id", postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["aoi_id"],
            ["work_order.aois.id"],
            name="fk_work_orders_aoi",
            ondelete="RESTRICT",
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
        "ix_work_orders_aoi_id",
        "work_orders",
        ["aoi_id"],
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
    op.execute(sa.text("DROP INDEX IF EXISTS work_order.ix_work_orders_status"))
    op.execute(sa.text("DROP INDEX IF EXISTS work_order.ix_work_orders_created_by_user_id"))
    op.execute(sa.text("DROP INDEX IF EXISTS work_order.ix_work_orders_aoi_id"))
    op.execute(sa.text("DROP INDEX IF EXISTS work_order.ix_work_orders_assignee_user_id"))
    op.execute(sa.text("DROP TABLE IF EXISTS work_order.work_orders"))
    op.execute(sa.text("DROP INDEX IF EXISTS work_order.ix_aois_geometry"))
    op.execute(sa.text("DROP TABLE IF EXISTS work_order.aois"))
    op.execute(sa.text("DROP SCHEMA IF EXISTS work_order"))
