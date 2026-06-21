"""add edit versions

Revision ID: a8c1f2d3e4b5
Revises: e4b7a9c2d5f8
"""

from typing import Sequence, Union

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "a8c1f2d3e4b5"
down_revision: Union[str, Sequence[str], None] = "e4b7a9c2d5f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "network_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("current_revision", sa.Integer(), server_default="1", nullable=False),
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
            "current_revision >= 1",
            name="ck_network_states_current_revision_positive",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_network_states_name"),
        schema="utility_network",
    )
    op.create_table(
        "default_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("work_order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("network_state_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("base_network_revision", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "active",
                name="default_state_status",
                native_enum=False,
                create_constraint=False,
                length=16,
            ),
            server_default="active",
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
            "base_network_revision >= 1",
            name="ck_default_states_base_network_revision_positive",
        ),
        sa.CheckConstraint(
            "status IN ('active')",
            name="ck_default_states_status",
        ),
        sa.ForeignKeyConstraint(
            ["network_state_id"],
            ["utility_network.network_states.id"],
            name="fk_default_states_network_state",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("work_order_id", name="uq_default_states_work_order"),
        schema="utility_network",
    )
    op.create_table(
        "default_state_features",
        sa.Column("default_state_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("feature_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_code", sa.String(length=100), nullable=False),
        sa.Column(
            "feature_type",
            sa.Enum(
                "junction",
                "line",
                "device",
                name="default_state_feature_type",
                native_enum=False,
                create_constraint=False,
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
        sa.Column(
            "properties",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("network_version", sa.Integer(), server_default="1", nullable=False),
        sa.CheckConstraint(
            "NOT ST_IsEmpty(geometry)",
            name="ck_default_state_features_geometry_not_empty",
        ),
        sa.CheckConstraint(
            "ST_IsValid(geometry)",
            name="ck_default_state_features_geometry_valid",
        ),
        sa.CheckConstraint(
            "ST_SRID(geometry) = 4326",
            name="ck_default_state_features_geometry_srid",
        ),
        sa.CheckConstraint(
            """
            (feature_type IN ('junction', 'device')
             AND GeometryType(geometry) = 'POINT')
            OR
            (feature_type = 'line'
             AND GeometryType(geometry) = 'LINESTRING')
            """,
            name="ck_default_state_features_geometry_matches_type",
        ),
        sa.CheckConstraint(
            "network_version >= 1",
            name="ck_default_state_features_network_version_positive",
        ),
        sa.ForeignKeyConstraint(
            ["default_state_id"],
            ["utility_network.default_states.id"],
            name="fk_default_state_features_default_state",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("default_state_id", "feature_id"),
        sa.UniqueConstraint(
            "default_state_id",
            "asset_code",
            name="uq_default_state_features_default_state_asset_code",
        ),
        sa.UniqueConstraint(
            "default_state_id",
            "feature_id",
            name="uq_default_state_features_default_state_id_feature_id",
        ),
        schema="utility_network",
    )
    op.create_table(
        "default_state_associations",
        sa.Column("default_state_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("association_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "association_type",
            sa.Enum(
                "connectivity",
                "containment",
                "attachment",
                name="default_state_association_type",
                native_enum=False,
                create_constraint=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("from_feature_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("to_feature_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "properties",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("network_version", sa.Integer(), server_default="1", nullable=False),
        sa.CheckConstraint(
            "from_feature_id <> to_feature_id",
            name="ck_default_state_associations_no_self_reference",
        ),
        sa.CheckConstraint(
            "network_version >= 1",
            name="ck_default_state_associations_network_version_positive",
        ),
        sa.ForeignKeyConstraint(
            ["default_state_id"],
            ["utility_network.default_states.id"],
            name="fk_default_state_associations_default_state",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["default_state_id", "from_feature_id"],
            [
                "utility_network.default_state_features.default_state_id",
                "utility_network.default_state_features.feature_id",
            ],
            name="fk_default_state_associations_from_feature",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["default_state_id", "to_feature_id"],
            [
                "utility_network.default_state_features.default_state_id",
                "utility_network.default_state_features.feature_id",
            ],
            name="fk_default_state_associations_to_feature",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("default_state_id", "association_id"),
        sa.UniqueConstraint(
            "default_state_id",
            "association_id",
            name="uq_default_state_associations_default_state_id_association_id",
        ),
        sa.UniqueConstraint(
            "default_state_id",
            "from_feature_id",
            "to_feature_id",
            "association_type",
            name="uq_default_state_associations_directed_edge",
        ),
        schema="utility_network",
    )
    op.create_table(
        "edit_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("work_order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("default_state_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("base_network_revision", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "open",
                name="edit_version_status",
                native_enum=False,
                create_constraint=False,
                length=16,
            ),
            server_default="open",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_opened_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "base_network_revision >= 1",
            name="ck_edit_versions_base_network_revision_positive",
        ),
        sa.CheckConstraint(
            "status IN ('open')",
            name="ck_edit_versions_status",
        ),
        sa.ForeignKeyConstraint(
            ["work_order_id"],
            ["work_order.work_orders.id"],
            name="fk_edit_versions_work_order",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="work_order",
    )
    op.create_index(
        "uq_edit_versions_open_work_order",
        "edit_versions",
        ["work_order_id"],
        unique=True,
        schema="work_order",
        postgresql_where=sa.text("status = 'open'"),
    )
    op.create_table(
        "edit_version_features",
        sa.Column("edit_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("feature_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_code", sa.String(length=100), nullable=False),
        sa.Column(
            "feature_type",
            sa.Enum(
                "junction",
                "line",
                "device",
                name="edit_version_feature_type",
                native_enum=False,
                create_constraint=False,
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
        sa.Column(
            "properties",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("network_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "operation",
            sa.Enum(
                "unchanged",
                "created",
                "updated",
                "deleted",
                name="edit_version_operation_state",
                native_enum=False,
                create_constraint=False,
                length=16,
            ),
            server_default="unchanged",
            nullable=False,
        ),
        sa.CheckConstraint(
            "NOT ST_IsEmpty(geometry)",
            name="ck_edit_version_features_geometry_not_empty",
        ),
        sa.CheckConstraint(
            "ST_IsValid(geometry)",
            name="ck_edit_version_features_geometry_valid",
        ),
        sa.CheckConstraint(
            "ST_SRID(geometry) = 4326",
            name="ck_edit_version_features_geometry_srid",
        ),
        sa.CheckConstraint(
            """
            (feature_type IN ('junction', 'device')
             AND GeometryType(geometry) = 'POINT')
            OR
            (feature_type = 'line'
             AND GeometryType(geometry) = 'LINESTRING')
            """,
            name="ck_edit_version_features_geometry_matches_type",
        ),
        sa.CheckConstraint(
            "network_version >= 1",
            name="ck_edit_version_features_network_version_positive",
        ),
        sa.CheckConstraint(
            "operation IN ('unchanged', 'created', 'updated', 'deleted')",
            name="ck_edit_version_features_operation",
        ),
        sa.ForeignKeyConstraint(
            ["edit_version_id"],
            ["work_order.edit_versions.id"],
            name="fk_edit_version_features_edit_version",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("edit_version_id", "feature_id"),
        sa.UniqueConstraint(
            "edit_version_id",
            "asset_code",
            name="uq_edit_version_features_edit_version_asset_code",
        ),
        sa.UniqueConstraint(
            "edit_version_id",
            "feature_id",
            name="uq_edit_version_features_edit_version_id_feature_id",
        ),
        schema="work_order",
    )
    op.create_table(
        "edit_version_associations",
        sa.Column("edit_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("association_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "association_type",
            sa.Enum(
                "connectivity",
                "containment",
                "attachment",
                name="edit_version_association_type",
                native_enum=False,
                create_constraint=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("from_feature_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("to_feature_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "properties",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("network_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "operation",
            sa.Enum(
                "unchanged",
                "created",
                "updated",
                "deleted",
                name="edit_version_operation_state",
                native_enum=False,
                create_constraint=False,
                length=16,
            ),
            server_default="unchanged",
            nullable=False,
        ),
        sa.CheckConstraint(
            "from_feature_id <> to_feature_id",
            name="ck_edit_version_associations_no_self_reference",
        ),
        sa.CheckConstraint(
            "network_version >= 1",
            name="ck_edit_version_associations_network_version_positive",
        ),
        sa.CheckConstraint(
            "operation IN ('unchanged', 'created', 'updated', 'deleted')",
            name="ck_edit_version_associations_operation",
        ),
        sa.ForeignKeyConstraint(
            ["edit_version_id"],
            ["work_order.edit_versions.id"],
            name="fk_edit_version_associations_edit_version",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["edit_version_id", "from_feature_id"],
            [
                "work_order.edit_version_features.edit_version_id",
                "work_order.edit_version_features.feature_id",
            ],
            name="fk_edit_version_associations_from_feature",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["edit_version_id", "to_feature_id"],
            [
                "work_order.edit_version_features.edit_version_id",
                "work_order.edit_version_features.feature_id",
            ],
            name="fk_edit_version_associations_to_feature",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("edit_version_id", "association_id"),
        sa.UniqueConstraint(
            "edit_version_id",
            "association_id",
            name="uq_edit_version_associations_edit_version_id_association_id",
        ),
        sa.UniqueConstraint(
            "edit_version_id",
            "from_feature_id",
            "to_feature_id",
            "association_type",
            name="uq_edit_version_associations_directed_edge",
        ),
        schema="work_order",
    )


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS work_order.edit_version_associations"))
    op.execute(sa.text("DROP TABLE IF EXISTS work_order.edit_version_features"))
    op.execute(sa.text("DROP INDEX IF EXISTS work_order.uq_edit_versions_open_work_order"))
    op.execute(sa.text("DROP TABLE IF EXISTS work_order.edit_versions"))
    op.execute(sa.text("DROP TABLE IF EXISTS utility_network.default_state_associations"))
    op.execute(sa.text("DROP TABLE IF EXISTS utility_network.default_state_features"))
    op.execute(sa.text("DROP TABLE IF EXISTS utility_network.default_states"))
    op.execute(sa.text("DROP TABLE IF EXISTS utility_network.network_states"))
