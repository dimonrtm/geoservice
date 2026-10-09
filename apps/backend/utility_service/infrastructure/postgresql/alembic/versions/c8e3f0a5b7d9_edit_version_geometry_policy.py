"""Persist immutable geometry policy; downgrade discards policy snapshots."""

import os
from decimal import Decimal, InvalidOperation

from alembic import op
import sqlalchemy as sa


revision = "c8e3f0a5b7d9"
down_revision = "b7d2e9f4a6c8"
branch_labels = None
depends_on = None


def configured_policy() -> tuple[Decimal, str, int]:
    # Frozen migration-local validation: no runtime Settings/JWT dependency.
    try:
        grid = Decimal(
            os.environ.get(
                "UTILITY_GEOMETRY_XY_RESOLUTION",
                "0.0000001",
            )
        )
    except InvalidOperation as error:
        raise ValueError("Некорректный шаг координатной сетки.") from error
    mode = os.environ.get(
        "UTILITY_GEOMETRY_ROUNDING_MODE",
        "ROUND_HALF_AWAY_FROM_ZERO",
    )
    if not grid.is_finite() or not Decimal("0.0000001") <= grid <= Decimal("360"):
        raise ValueError(
            "Шаг координатной сетки должен быть конечным числом в диапазоне [0.0000001, 360]."
        )
    _, digits, exponent = grid.as_tuple()
    digits = list(digits)
    while digits and digits[-1] == 0:
        digits.pop()
        exponent += 1
    if exponent < -9 or mode != "ROUND_HALF_AWAY_FROM_ZERO":
        raise ValueError(
            "Недопустимое число дробных знаков шага координатной сетки или режим округления."
        )
    return grid, mode, 1


def upgrade() -> None:
    grid, mode, version = configured_policy()
    for column in (
        sa.Column(
            "geometry_xy_resolution",
            sa.Numeric(),
            nullable=True,
        ),
        sa.Column(
            "geometry_rounding_mode",
            sa.String(32),
            nullable=True,
        ),
        sa.Column(
            "geometry_policy_version",
            sa.SmallInteger(),
            nullable=True,
        ),
    ):
        op.add_column(
            "edit_versions",
            column,
            schema="work_order",
        )
    op.get_bind().execute(
        sa.text(
            """
            UPDATE work_order.edit_versions
            SET
                geometry_xy_resolution = :grid,
                geometry_rounding_mode = :mode,
                geometry_policy_version = :version
            """
        ),
        {
            "grid": grid,
            "mode": mode,
            "version": version,
        },
    )
    for name in ("geometry_xy_resolution", "geometry_rounding_mode", "geometry_policy_version"):
        op.alter_column(
            "edit_versions",
            name,
            nullable=False,
            schema="work_order",
        )
    for name, expression in (
        (
            "ck_edit_versions_geometry_grid",
            """
            geometry_xy_resolution NOT IN (
                'NaN'::numeric,
                'Infinity'::numeric,
                '-Infinity'::numeric
            )
            AND geometry_xy_resolution BETWEEN 0.0000001 AND 360
            AND geometry_xy_resolution * 1000000000
                = trunc(geometry_xy_resolution * 1000000000)
            """,
        ),
        (
            "ck_edit_versions_geometry_rounding",
            "geometry_rounding_mode = 'ROUND_HALF_AWAY_FROM_ZERO'",
        ),
        ("ck_edit_versions_geometry_policy_version", "geometry_policy_version = 1"),
    ):
        op.create_check_constraint(
            name,
            "edit_versions",
            expression,
            schema="work_order",
        )
    op.execute(
        """
        CREATE FUNCTION work_order.guard_edit_version_geometry_policy() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            IF ROW(
                NEW.geometry_xy_resolution,
                NEW.geometry_rounding_mode,
                NEW.geometry_policy_version
            ) IS DISTINCT FROM ROW(
                OLD.geometry_xy_resolution,
                OLD.geometry_rounding_mode,
                OLD.geometry_policy_version
            )
            THEN
                RAISE EXCEPTION 'Параметры обработки геометрии нельзя изменять после создания версии.'
                    USING ERRCODE='23514', CONSTRAINT='ck_edit_versions_geometry_policy_immutable';
            END IF;
            RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_edit_version_geometry_policy
        BEFORE UPDATE ON work_order.edit_versions
        FOR EACH ROW EXECUTE FUNCTION work_order.guard_edit_version_geometry_policy()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER trg_edit_version_geometry_policy ON work_order.edit_versions")
    op.execute("DROP FUNCTION work_order.guard_edit_version_geometry_policy()")
    for name in (
        "ck_edit_versions_geometry_grid",
        "ck_edit_versions_geometry_rounding",
        "ck_edit_versions_geometry_policy_version",
    ):
        op.drop_constraint(
            name,
            "edit_versions",
            schema="work_order",
            type_="check",
        )
    for name in ("geometry_xy_resolution", "geometry_rounding_mode", "geometry_policy_version"):
        op.drop_column(
            "edit_versions",
            name,
            schema="work_order",
        )
