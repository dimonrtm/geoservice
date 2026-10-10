from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.domain_services.edit_geometry.structure import (
    changed_vertices,
    has_matching_structure,
    is_internal_diff,
)
from utility_service.domain_services.edit_geometry.types import InvalidGeometryContext
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


def reject_context(reason: str) -> RepositoryRejection:
    return RepositoryRejection(
        "WORK_ORDER_CONTEXT_INVALID",
        reason,
    )


def check_baseline(context: EditGeometryContext) -> RepositoryRejection | None:
    current, baseline, state = context.current, context.baseline, context.default_state
    if current.feature_type != "line" or current.operation in (
        "created",
        "deleted",
    ):
        return RepositoryRejection(
            "FEATURE_NOT_EDITABLE",
            "Объект не поддерживает изменение геометрии линии.",
        )
    if baseline is None or state is None:
        return reject_context("Базовое состояние отсутствует.")
    if (
        state.id != context.root.default_state_id
        or state.work_order_id != context.root.work_order_id
        or state.base_network_revision != context.root.base_network_revision
        or state.status != "active"
        or baseline.feature_id != current.feature_id
        or baseline.feature_type != current.feature_type
    ):
        return reject_context("Базовое состояние не соответствует рабочей версии.")
    try:
        geometry = decode_geometry(baseline.geometry_ewkb)
    except InvalidGeometryContext:
        return reject_context("Геометрия базового состояния повреждена.")
    if geometry.type != "LineString":
        return reject_context("Геометрия базового состояния не соответствует типу объекта.")
    if len(geometry.coordinates) < 3:
        return RepositoryRejection(
            "FEATURE_NOT_EDITABLE",
            "У линии нет внутренней вершины.",
        )
    return None


def check_context(context: EditGeometryContext) -> RepositoryRejection | None:
    rejection = check_baseline(context)
    if rejection is not None:
        return rejection
    if context.aoi_ewkb is None:
        return reject_context("Область работ отсутствует.")
    try:
        baseline = decode_geometry(context.baseline.geometry_ewkb)
        current = decode_geometry(context.current.geometry_ewkb)
    except InvalidGeometryContext:
        return reject_context("Текущая геометрия повреждена.")
    if not has_matching_structure(
        baseline,
        current,
    ):
        return reject_context("Структура текущей геометрии отличается от базового состояния.")
    indices = changed_vertices(
        baseline,
        current,
    )
    if not is_internal_diff(
        indices,
        len(baseline.coordinates),
    ):
        return reject_context(
            "Текущая геометрия нарушает правило изменения одной внутренней вершины."
        )
    expected_operation = "updated" if indices else "unchanged"
    if context.current.operation != expected_operation:
        return reject_context("Признак изменения объекта противоречит текущей геометрии.")
    return None
