"""sprint1 schema boundaries

Revision ID: f2b3c4d5e6a7
Revises: a8c1f2d3e4b5
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "f2b3c4d5e6a7"
down_revision: Union[str, Sequence[str], None] = "a8c1f2d3e4b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text('CREATE SCHEMA IF NOT EXISTS "user"'))
    op.execute(sa.text("CREATE SCHEMA IF NOT EXISTS work_order"))

    op.execute(sa.text("DROP TABLE IF EXISTS utility_network.edit_versions CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS utility_network.work_orders CASCADE"))

    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF to_regclass('public.users') IS NOT NULL
                   AND to_regclass('"user".users') IS NULL THEN
                    ALTER TABLE public.users SET SCHEMA "user";
                END IF;
            END $$;
            """
        )
    )
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF to_regclass('utility_network.default_states') IS NOT NULL
                   AND EXISTS (
                       SELECT 1
                       FROM information_schema.columns
                       WHERE table_schema = 'utility_network'
                         AND table_name = 'default_states'
                         AND column_name = 'current_revision'
                   ) THEN
                    DROP TABLE utility_network.default_states CASCADE;
                END IF;
            END $$;
            """
        )
    )

    op.execute(
        sa.text(
            """
            CREATE TABLE IF NOT EXISTS work_order.work_orders (
                id uuid PRIMARY KEY,
                code varchar(100) NOT NULL,
                title varchar(200) NOT NULL,
                description text NULL,
                status varchar(16) NOT NULL DEFAULT 'assigned',
                assignee_user_id uuid NOT NULL,
                created_by_user_id uuid NOT NULL,
                created_at timestamptz NOT NULL DEFAULT now(),
                updated_at timestamptz NOT NULL DEFAULT now(),
                CONSTRAINT uq_work_orders_code UNIQUE (code),
                CONSTRAINT ck_work_orders_status
                    CHECK (status IN ('assigned', 'in_progress'))
            )
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE INDEX IF NOT EXISTS ix_work_orders_assignee_user_id
            ON work_order.work_orders (assignee_user_id)
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE INDEX IF NOT EXISTS ix_work_orders_created_by_user_id
            ON work_order.work_orders (created_by_user_id)
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE INDEX IF NOT EXISTS ix_work_orders_status
            ON work_order.work_orders (status)
            """
        )
    )

    op.execute(
        sa.text(
            """
            CREATE TABLE IF NOT EXISTS utility_network.network_states (
                id uuid PRIMARY KEY,
                name varchar(64) NOT NULL,
                current_revision integer NOT NULL DEFAULT 1,
                created_at timestamptz NOT NULL DEFAULT now(),
                updated_at timestamptz NOT NULL DEFAULT now(),
                CONSTRAINT uq_network_states_name UNIQUE (name),
                CONSTRAINT ck_network_states_current_revision_positive
                    CHECK (current_revision >= 1)
            )
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE TABLE IF NOT EXISTS utility_network.default_states (
                id uuid PRIMARY KEY,
                work_order_id uuid NOT NULL,
                network_state_id uuid NOT NULL,
                base_network_revision integer NOT NULL DEFAULT 1,
                status varchar(16) NOT NULL DEFAULT 'active',
                created_at timestamptz NOT NULL DEFAULT now(),
                updated_at timestamptz NOT NULL DEFAULT now(),
                CONSTRAINT uq_default_states_work_order UNIQUE (work_order_id),
                CONSTRAINT ck_default_states_base_network_revision_positive
                    CHECK (base_network_revision >= 1),
                CONSTRAINT ck_default_states_status CHECK (status IN ('active')),
                CONSTRAINT fk_default_states_network_state
                    FOREIGN KEY (network_state_id)
                    REFERENCES utility_network.network_states(id)
                    ON DELETE RESTRICT
            )
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE TABLE IF NOT EXISTS utility_network.default_state_features (
                default_state_id uuid NOT NULL,
                feature_id uuid NOT NULL,
                asset_code varchar(100) NOT NULL,
                feature_type varchar(16) NOT NULL,
                geometry geometry(GEOMETRY, 4326) NOT NULL,
                properties jsonb NOT NULL DEFAULT '{}'::jsonb,
                network_version integer NOT NULL DEFAULT 1,
                PRIMARY KEY (default_state_id, feature_id),
                CONSTRAINT fk_default_state_features_default_state
                    FOREIGN KEY (default_state_id)
                    REFERENCES utility_network.default_states(id)
                    ON DELETE CASCADE,
                CONSTRAINT uq_default_state_features_default_state_asset_code
                    UNIQUE (default_state_id, asset_code),
                CONSTRAINT uq_default_state_features_default_state_id_feature_id
                    UNIQUE (default_state_id, feature_id),
                CONSTRAINT ck_default_state_features_geometry_not_empty
                    CHECK (NOT ST_IsEmpty(geometry)),
                CONSTRAINT ck_default_state_features_geometry_valid
                    CHECK (ST_IsValid(geometry)),
                CONSTRAINT ck_default_state_features_geometry_srid
                    CHECK (ST_SRID(geometry) = 4326),
                CONSTRAINT ck_default_state_features_geometry_matches_type
                    CHECK (
                        (feature_type IN ('junction', 'device')
                         AND GeometryType(geometry) = 'POINT')
                        OR
                        (feature_type = 'line'
                         AND GeometryType(geometry) = 'LINESTRING')
                    ),
                CONSTRAINT ck_default_state_features_network_version_positive
                    CHECK (network_version >= 1)
            )
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE TABLE IF NOT EXISTS utility_network.default_state_associations (
                default_state_id uuid NOT NULL,
                association_id uuid NOT NULL,
                association_type varchar(16) NOT NULL,
                from_feature_id uuid NOT NULL,
                to_feature_id uuid NOT NULL,
                properties jsonb NOT NULL DEFAULT '{}'::jsonb,
                network_version integer NOT NULL DEFAULT 1,
                PRIMARY KEY (default_state_id, association_id),
                CONSTRAINT fk_default_state_associations_default_state
                    FOREIGN KEY (default_state_id)
                    REFERENCES utility_network.default_states(id)
                    ON DELETE CASCADE,
                CONSTRAINT fk_default_state_associations_from_feature
                    FOREIGN KEY (default_state_id, from_feature_id)
                    REFERENCES utility_network.default_state_features(default_state_id, feature_id)
                    ON DELETE RESTRICT,
                CONSTRAINT fk_default_state_associations_to_feature
                    FOREIGN KEY (default_state_id, to_feature_id)
                    REFERENCES utility_network.default_state_features(default_state_id, feature_id)
                    ON DELETE RESTRICT,
                CONSTRAINT uq_default_state_associations_default_state_id_association_id
                    UNIQUE (default_state_id, association_id),
                CONSTRAINT uq_default_state_associations_directed_edge
                    UNIQUE (default_state_id, from_feature_id, to_feature_id, association_type),
                CONSTRAINT ck_default_state_associations_no_self_reference
                    CHECK (from_feature_id <> to_feature_id),
                CONSTRAINT ck_default_state_associations_network_version_positive
                    CHECK (network_version >= 1)
            )
            """
        )
    )

    op.execute(
        sa.text(
            """
            CREATE TABLE IF NOT EXISTS work_order.edit_versions (
                id uuid PRIMARY KEY,
                work_order_id uuid NOT NULL,
                default_state_id uuid NOT NULL,
                owner_user_id uuid NOT NULL,
                base_network_revision integer NOT NULL DEFAULT 1,
                status varchar(16) NOT NULL DEFAULT 'open',
                created_at timestamptz NOT NULL DEFAULT now(),
                last_opened_at timestamptz NOT NULL DEFAULT now(),
                CONSTRAINT ck_edit_versions_base_network_revision_positive
                    CHECK (base_network_revision >= 1),
                CONSTRAINT ck_edit_versions_status CHECK (status IN ('open')),
                CONSTRAINT fk_edit_versions_work_order
                    FOREIGN KEY (work_order_id)
                    REFERENCES work_order.work_orders(id)
                    ON DELETE RESTRICT
            )
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS uq_edit_versions_open_work_order
            ON work_order.edit_versions (work_order_id)
            WHERE status = 'open'
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE TABLE IF NOT EXISTS work_order.edit_version_features (
                edit_version_id uuid NOT NULL,
                feature_id uuid NOT NULL,
                asset_code varchar(100) NOT NULL,
                feature_type varchar(16) NOT NULL,
                geometry geometry(GEOMETRY, 4326) NOT NULL,
                properties jsonb NOT NULL DEFAULT '{}'::jsonb,
                network_version integer NOT NULL DEFAULT 1,
                operation varchar(16) NOT NULL DEFAULT 'unchanged',
                PRIMARY KEY (edit_version_id, feature_id),
                CONSTRAINT fk_edit_version_features_edit_version
                    FOREIGN KEY (edit_version_id)
                    REFERENCES work_order.edit_versions(id)
                    ON DELETE CASCADE,
                CONSTRAINT uq_edit_version_features_edit_version_asset_code
                    UNIQUE (edit_version_id, asset_code),
                CONSTRAINT uq_edit_version_features_edit_version_id_feature_id
                    UNIQUE (edit_version_id, feature_id),
                CONSTRAINT ck_edit_version_features_geometry_not_empty
                    CHECK (NOT ST_IsEmpty(geometry)),
                CONSTRAINT ck_edit_version_features_geometry_valid
                    CHECK (ST_IsValid(geometry)),
                CONSTRAINT ck_edit_version_features_geometry_srid
                    CHECK (ST_SRID(geometry) = 4326),
                CONSTRAINT ck_edit_version_features_geometry_matches_type
                    CHECK (
                        (feature_type IN ('junction', 'device')
                         AND GeometryType(geometry) = 'POINT')
                        OR
                        (feature_type = 'line'
                         AND GeometryType(geometry) = 'LINESTRING')
                    ),
                CONSTRAINT ck_edit_version_features_network_version_positive
                    CHECK (network_version >= 1),
                CONSTRAINT ck_edit_version_features_operation
                    CHECK (operation IN ('unchanged', 'created', 'updated', 'deleted'))
            )
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE TABLE IF NOT EXISTS work_order.edit_version_associations (
                edit_version_id uuid NOT NULL,
                association_id uuid NOT NULL,
                association_type varchar(16) NOT NULL,
                from_feature_id uuid NOT NULL,
                to_feature_id uuid NOT NULL,
                properties jsonb NOT NULL DEFAULT '{}'::jsonb,
                network_version integer NOT NULL DEFAULT 1,
                operation varchar(16) NOT NULL DEFAULT 'unchanged',
                PRIMARY KEY (edit_version_id, association_id),
                CONSTRAINT fk_edit_version_associations_edit_version
                    FOREIGN KEY (edit_version_id)
                    REFERENCES work_order.edit_versions(id)
                    ON DELETE CASCADE,
                CONSTRAINT fk_edit_version_associations_from_feature
                    FOREIGN KEY (edit_version_id, from_feature_id)
                    REFERENCES work_order.edit_version_features(edit_version_id, feature_id)
                    ON DELETE RESTRICT,
                CONSTRAINT fk_edit_version_associations_to_feature
                    FOREIGN KEY (edit_version_id, to_feature_id)
                    REFERENCES work_order.edit_version_features(edit_version_id, feature_id)
                    ON DELETE RESTRICT,
                CONSTRAINT uq_edit_version_associations_edit_version_id_association_id
                    UNIQUE (edit_version_id, association_id),
                CONSTRAINT uq_edit_version_associations_directed_edge
                    UNIQUE (edit_version_id, from_feature_id, to_feature_id, association_type),
                CONSTRAINT ck_edit_version_associations_no_self_reference
                    CHECK (from_feature_id <> to_feature_id),
                CONSTRAINT ck_edit_version_associations_network_version_positive
                    CHECK (network_version >= 1),
                CONSTRAINT ck_edit_version_associations_operation
                    CHECK (operation IN ('unchanged', 'created', 'updated', 'deleted'))
            )
            """
        )
    )


def downgrade() -> None:
    pass
