from decimal import Decimal

from utility_service.domain_services.edit_geometry.types import (
    GeometryRuleError,
    GeometryValue,
    InvalidGeometryContext,
    PreparedGeometry,
    TransitionResult,
)


def validate_geometry_value(value: GeometryValue) -> None:
    if value.srid != 4326 or value.type not in {"Point", "LineString"}:
        raise InvalidGeometryContext("Неподдерживаемый тип геометрии или SRID.")
    minimum = 1 if value.type == "Point" else 2
    if len(value.coordinates) < minimum or (value.type == "Point" and len(value.coordinates) != 1):
        raise InvalidGeometryContext("Неправильная структура геометрии.")
    for position in value.coordinates:
        if len(position) != 2 or any(
            not isinstance(
                ordinate,
                Decimal,
            )
            or not ordinate.is_finite()
            for ordinate in position
        ):
            raise InvalidGeometryContext("Ожидались конечные XY-координаты.")


def changed_vertices(
    baseline: GeometryValue,
    geometry: GeometryValue,
) -> tuple[int, ...]:
    return tuple(
        index
        for index, (before, after) in enumerate(
            zip(
                baseline.coordinates,
                geometry.coordinates,
                strict=True,
            ),
        )
        if before != after
    )


def has_matching_structure(
    baseline: GeometryValue,
    geometry: GeometryValue,
) -> bool:
    return (
        baseline.type == geometry.type == "LineString"
        and baseline.srid == geometry.srid
        and len(baseline.coordinates) == len(geometry.coordinates)
    )


def is_internal_diff(
    indices: tuple[int, ...],
    vertex_count: int,
) -> bool:
    return len(indices) <= 1 and all(0 < index < vertex_count - 1 for index in indices)


def validate_transition(
    baseline: GeometryValue,
    current: GeometryValue,
    prepared: PreparedGeometry,
) -> TransitionResult:
    if prepared.rejection_code is not None:
        raise GeometryRuleError(prepared.rejection_code)
    validate_geometry_value(baseline)
    validate_geometry_value(current)
    if not has_matching_structure(
        baseline,
        current,
    ):
        raise InvalidGeometryContext("Структура current отличается от baseline.")
    before = changed_vertices(
        baseline,
        current,
    )
    if not is_internal_diff(
        before,
        len(baseline.coordinates),
    ):
        raise InvalidGeometryContext("Current нарушает ограничение одной внутренней вершины.")
    after = changed_vertices(
        baseline,
        prepared.geometry,
    )
    if before and after and before != after:
        raise GeometryRuleError("GEOMETRY_STRUCTURE_CHANGED")
    return TransitionResult(
        operation="updated" if after else "unchanged",
        is_noop=prepared.geometry == current,
        vertex_index=prepared.vertex_index,
    )
