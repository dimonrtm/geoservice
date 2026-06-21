"""repair work order AOI scope

Revision ID: c9d0e1f2a3b4
Revises: f2b3c4d5e6a7
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, Sequence[str], None] = "f2b3c4d5e6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("CREATE SCHEMA IF NOT EXISTS work_order"))
    op.execute(
        sa.text(
            """
            CREATE TABLE IF NOT EXISTS work_order.aois (
                id uuid PRIMARY KEY,
                name varchar(200) NOT NULL,
                description text NULL,
                geometry geometry(GEOMETRY, 4326) NOT NULL,
                created_at timestamptz NOT NULL DEFAULT now(),
                updated_at timestamptz NOT NULL DEFAULT now(),
                CONSTRAINT ck_aois_geometry_not_empty
                    CHECK (NOT ST_IsEmpty(geometry)),
                CONSTRAINT ck_aois_geometry_valid
                    CHECK (ST_IsValid(geometry)),
                CONSTRAINT ck_aois_geometry_srid
                    CHECK (ST_SRID(geometry) = 4326),
                CONSTRAINT ck_aois_geometry_type
                    CHECK (GeometryType(geometry) IN ('POLYGON', 'MULTIPOLYGON'))
            )
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE INDEX IF NOT EXISTS ix_aois_geometry
            ON work_order.aois
            USING gist (geometry)
            """
        )
    )
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF to_regclass('utility_network.aois') IS NOT NULL THEN
                    INSERT INTO work_order.aois (
                        id,
                        name,
                        description,
                        geometry,
                        created_at,
                        updated_at
                    )
                    SELECT
                        id,
                        name,
                        description,
                        geometry,
                        created_at,
                        updated_at
                    FROM utility_network.aois
                    ON CONFLICT (id) DO NOTHING;
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
                IF NOT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'work_order'
                      AND table_name = 'work_orders'
                      AND column_name = 'aoi_id'
                ) THEN
                    ALTER TABLE work_order.work_orders
                    ADD COLUMN aoi_id uuid;
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
                IF EXISTS (
                    SELECT 1
                    FROM work_order.work_orders AS work_order
                    WHERE work_order.aoi_id IS NULL
                       OR NOT EXISTS (
                           SELECT 1
                           FROM work_order.aois AS aoi
                           WHERE aoi.id = work_order.aoi_id
                       )
                ) THEN
                    INSERT INTO work_order.aois (
                        id,
                        name,
                        description,
                        geometry
                    )
                    VALUES (
                        '6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0100',
                        'Рабочая область WO-001',
                        'Рабочая область для проверки участка фидера WO-001.',
                        ST_GeomFromText(
                            'POLYGON ((65.495 44.795, 65.545 44.795, 65.545 44.835, 65.495 44.835, 65.495 44.795))',
                            4326
                        )
                    )
                    ON CONFLICT (id) DO NOTHING;

                    UPDATE work_order.work_orders AS work_order
                    SET aoi_id = '6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0100'
                    WHERE work_order.aoi_id IS NULL
                       OR NOT EXISTS (
                           SELECT 1
                           FROM work_order.aois AS aoi
                           WHERE aoi.id = work_order.aoi_id
                       );
                END IF;
            END $$;
            """
        )
    )
    op.execute(
        sa.text(
            """
            ALTER TABLE work_order.work_orders
            ALTER COLUMN aoi_id SET NOT NULL
            """
        )
    )
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_constraint
                    WHERE conname = 'fk_work_orders_aoi'
                      AND conrelid = 'work_order.work_orders'::regclass
                ) THEN
                    ALTER TABLE work_order.work_orders
                    ADD CONSTRAINT fk_work_orders_aoi
                    FOREIGN KEY (aoi_id)
                    REFERENCES work_order.aois(id)
                    ON DELETE RESTRICT;
                END IF;
            END $$;
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE INDEX IF NOT EXISTS ix_work_orders_aoi_id
            ON work_order.work_orders (aoi_id)
            """
        )
    )
    op.execute(sa.text("DROP TABLE IF EXISTS utility_network.aois CASCADE"))


def downgrade() -> None:
    pass
