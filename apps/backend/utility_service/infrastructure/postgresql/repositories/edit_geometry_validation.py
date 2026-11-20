from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.domain_services.edit_geometry.save_policy import (
    EditRejection,
    begin_baseline,
    check_saved_line,
)
from utility_service.domain_services.edit_geometry.types import (
    GeometryValue,
    InvalidGeometryContext,
)
from utility_service.infrastructure.postgresql.geometry_codec import decode_geometry
from utility_service.infrastructure.postgresql.repository_rows.edit_geometry import (
    EditGeometryContext,
    RepositoryRejection,
    SpatialVerdict,
)


SPATIAL_SQL = text(
    (Path(__file__).resolve().parents[1] / "sql" / "edit_geometry_spatial.sql").read_text(
        encoding="utf-8"
    )
)


async def inspect_spatial(
    session: AsyncSession,
    *,
    geometry_ewkb: bytes,
    aoi_ewkb: bytes,
) -> SpatialVerdict:
    with session.no_autoflush:
        row = (
            (
                await session.execute(
                    SPATIAL_SQL,
                    {
                        "geometry_ewkb": geometry_ewkb,
                        "aoi_ewkb": aoi_ewkb,
                    },
                )
            )
            .mappings()
            .one()
        )
    return SpatialVerdict(**row)


def read_baseline(context: EditGeometryContext) -> GeometryValue | EditRejection:
    current, baseline, state = context.current, context.baseline, context.default_state
    if baseline is None or state is None:
        return EditRejection.invalid_context("Базовое состояние отсутствует.")
    if (
        state.id != context.root.default_state_id
        or state.work_order_id != context.root.work_order_id
        or state.base_network_revision != context.root.base_network_revision
        or state.status != "active"
        or baseline.feature_id != current.feature_id
        or baseline.feature_type != current.feature_type
    ):
        return EditRejection.invalid_context("Базовое состояние не соответствует рабочей версии.")
    try:
        return decode_geometry(baseline.geometry_ewkb)
    except InvalidGeometryContext:
        return EditRejection.invalid_context("Геометрия базового состояния повреждена.")


def checked_baseline(context: EditGeometryContext) -> GeometryValue | RepositoryRejection:
    phase = begin_baseline(context.current.feature_type, context.current.operation)
    if isinstance(phase, EditRejection):
        return RepositoryRejection(phase.code, phase.reason)
    geometry = read_baseline(context)
    if isinstance(geometry, EditRejection):
        return RepositoryRejection(geometry.code, geometry.reason)
    rejection = phase.evaluate(geometry)
    if rejection is not None:
        return RepositoryRejection(rejection.code, rejection.reason)
    return geometry


def check_baseline(context: EditGeometryContext) -> RepositoryRejection | None:
    result = checked_baseline(context)
    return result if isinstance(result, RepositoryRejection) else None


def read_current(context: EditGeometryContext) -> GeometryValue | EditRejection:
    if context.aoi_ewkb is None:
        return EditRejection.invalid_context("Область работ отсутствует.")
    try:
        return decode_geometry(context.current.geometry_ewkb)
    except InvalidGeometryContext:
        return EditRejection.invalid_context("Текущая геометрия повреждена.")


def check_context(context: EditGeometryContext) -> RepositoryRejection | None:
    baseline = checked_baseline(context)
    if isinstance(baseline, RepositoryRejection):
        return baseline
    current = read_current(context)
    if isinstance(current, EditRejection):
        return RepositoryRejection(current.code, current.reason)
    rejection = check_saved_line(baseline, current, context.current.operation)
    return RepositoryRejection(rejection.code, rejection.reason) if rejection else None
