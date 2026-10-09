from decimal import Context, Decimal, ROUND_HALF_UP, localcontext

from utility_service.domain_services.edit_geometry.policy import GeometryPolicy
from utility_service.domain_services.edit_geometry.structure import (
    changed_vertices,
    has_matching_structure,
    is_internal_diff,
    validate_geometry_value,
)
from utility_service.domain_services.edit_geometry.types import GeometryValue, PreparedGeometry


def decimal_text(value: Decimal) -> str:
    if not value.is_finite():
        raise ValueError("Координата должна быть конечным числом.")
    if value.is_zero():
        return "0"
    result = format(
        value,
        "f",
    )
    if "." in result:
        result = result.rstrip("0").rstrip(".")
    return result


def quantize_ordinate(
    value: Decimal,
    policy: GeometryPolicy,
) -> Decimal:
    if (
        not isinstance(
            value,
            Decimal,
        )
        or not value.is_finite()
    ):
        raise ValueError("Координата должна быть конечным Decimal.")
    numerator, denominator = value.as_integer_ratio()
    grid_numerator, grid_denominator = policy.xy_resolution.as_integer_ratio()
    numerator *= grid_denominator
    denominator *= grid_numerator
    precision = len(str(abs(numerator))) + len(str(denominator)) + 2
    context = Context(
        prec=precision,
        rounding=ROUND_HALF_UP,
        Emin=-4096,
        Emax=4096,
    )
    with localcontext(context):
        ticks = (Decimal(numerator) / Decimal(denominator)).to_integral_value(
            rounding=ROUND_HALF_UP,
        )
        result = ticks * policy.xy_resolution
    return Decimal(0) if result.is_zero() else result


def prepare_geometry(
    request: GeometryValue,
    baseline: GeometryValue,
    policy: GeometryPolicy,
) -> PreparedGeometry:
    validate_geometry_value(baseline)
    validate_geometry_value(request)
    if baseline.type != "LineString" or len(baseline.coordinates) < 3:
        return PreparedGeometry(
            "unmatched_structure",
            request,
            None,
            "FEATURE_NOT_EDITABLE",
        )
    if not has_matching_structure(
        baseline,
        request,
    ):
        return PreparedGeometry(
            "unmatched_structure",
            request,
            None,
            "GEOMETRY_STRUCTURE_CHANGED",
        )
    positions = []
    for incoming, original in zip(
        request.coordinates,
        baseline.coordinates,
        strict=True,
    ):
        position = []
        for value, base in zip(
            incoming,
            original,
            strict=True,
        ):
            rounded = quantize_ordinate(
                value,
                policy,
            )
            position.append(
                base
                if rounded
                == quantize_ordinate(
                    base,
                    policy,
                )
                else rounded
            )
        positions.append(tuple(position))
    candidate = GeometryValue(
        "LineString",
        tuple(positions),
    )
    changed = changed_vertices(
        baseline,
        candidate,
    )
    valid_structure = is_internal_diff(
        changed,
        len(baseline.coordinates),
    )
    rejection = None
    if not valid_structure:
        rejection = "GEOMETRY_STRUCTURE_CHANGED"
    elif any(not (-180 <= x <= 180 and -90 <= y <= 90) for x, y in candidate.coordinates):
        rejection = "GEOMETRY_INVALID"
    return PreparedGeometry(
        representation="baseline_aligned",
        geometry=candidate,
        vertex_index=changed[0] if valid_structure and changed else None,
        rejection_code=rejection,
    )
