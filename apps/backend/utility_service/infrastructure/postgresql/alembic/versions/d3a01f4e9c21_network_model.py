"""add utility network model

Revision ID: d3a01f4e9c21
Revises: b82a5f2d91c3
"""

from typing import Sequence, Union

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "d3a01f4e9c21"
down_revision: Union[str, Sequence[str], None] = "b82a5f2d91c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("CREATE SCHEMA utility_network"))

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
        schema="utility_network",
    )
    op.create_index(
        "ix_aois_geometry",
        "aois",
        ["geometry"],
        unique=False,
        schema="utility_network",
        postgresql_using="gist",
    )

    op.create_table(
        "feeders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_feeders_code"),
        schema="utility_network",
    )

    op.create_table(
        "network_features",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("feeder_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_code", sa.String(length=100), nullable=False),
        sa.Column(
            "feature_type",
            sa.Enum(
                "junction",
                "line",
                "device",
                name="network_feature_type",
                native_enum=False,
                create_constraint=True,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column(
            "geometry",
            geoalchemy2.Geometry(
                geometry_type="GEOMETRY",
                srid=4326,
                spatial_index=False,
            ),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "properties",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "version",
            sa.Integer(),
            server_default=sa.text("1"),
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
            name="ck_network_features_geometry_not_empty",
        ),
        sa.CheckConstraint(
            "ST_IsValid(geometry)",
            name="ck_network_features_geometry_valid",
        ),
        sa.CheckConstraint(
            "ST_SRID(geometry) = 4326",
            name="ck_network_features_geometry_srid",
        ),
        sa.CheckConstraint(
            """
            (feature_type IN ('junction', 'device')
             AND GeometryType(geometry) = 'POINT')
            OR
            (feature_type = 'line'
             AND GeometryType(geometry) = 'LINESTRING')
            """,
            name="ck_network_features_geometry_matches_type",
        ),
        sa.CheckConstraint(
            "version >= 1",
            name="ck_network_features_version_positive",
        ),
        sa.ForeignKeyConstraint(
            ["feeder_id"],
            ["utility_network.feeders.id"],
            name="fk_network_features_feeder",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "feeder_id",
            "asset_code",
            name="uq_network_features_feeder_asset_code",
        ),
        sa.UniqueConstraint(
            "feeder_id",
            "id",
            name="uq_network_features_feeder_id_id",
        ),
        schema="utility_network",
    )
    op.create_index(
        "ix_network_features_geometry",
        "network_features",
        ["geometry"],
        unique=False,
        schema="utility_network",
        postgresql_using="gist",
    )

    op.create_table(
        "network_associations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("feeder_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "from_feature_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "to_feature_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "association_type",
            sa.Enum(
                "connectivity",
                "containment",
                "attachment",
                name="network_association_type",
                native_enum=False,
                create_constraint=True,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column(
            "version",
            sa.Integer(),
            server_default=sa.text("1"),
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
            "from_feature_id <> to_feature_id",
            name="ck_network_associations_no_self_reference",
        ),
        sa.CheckConstraint(
            "version >= 1",
            name="ck_network_associations_version_positive",
        ),
        sa.ForeignKeyConstraint(
            ["feeder_id"],
            ["utility_network.feeders.id"],
            name="fk_network_associations_feeder",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["feeder_id", "from_feature_id"],
            [
                "utility_network.network_features.feeder_id",
                "utility_network.network_features.id",
            ],
            name="fk_network_associations_from_feature",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["feeder_id", "to_feature_id"],
            [
                "utility_network.network_features.feeder_id",
                "utility_network.network_features.id",
            ],
            name="fk_network_associations_to_feature",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "feeder_id",
            "from_feature_id",
            "to_feature_id",
            "association_type",
            name="uq_network_associations_directed_edge",
        ),
        schema="utility_network",
    )


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS utility_network.network_associations"))
    op.execute(sa.text("DROP INDEX IF EXISTS utility_network.ix_network_features_geometry"))
    op.execute(sa.text("DROP TABLE IF EXISTS utility_network.network_features"))
    op.execute(sa.text("DROP TABLE IF EXISTS utility_network.feeders"))
    op.execute(sa.text("DROP INDEX IF EXISTS utility_network.ix_aois_geometry"))
    op.execute(sa.text("DROP TABLE IF EXISTS utility_network.aois"))
    op.execute(sa.text("DROP SCHEMA IF EXISTS utility_network"))
