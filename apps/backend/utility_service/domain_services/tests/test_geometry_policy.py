from decimal import Context, Decimal, Inexact, ROUND_DOWN, Rounded, localcontext
from fractions import Fraction

import pytest

from utility_service.domain_services.edit_geometry.policy import GeometryPolicy
from utility_service.domain_services.edit_geometry.canonicalization import (
    decimal_text,
    quantize_ordinate,
)


@pytest.mark.parametrize(
    "grid",
    ["0.0000001", "0.0000002500", "0.0000003", "360"],
)
def test_policy_accepts_supported_grid(grid):
    policy = GeometryPolicy(Decimal(grid))
    assert policy.xy_resolution == Decimal(grid)


@pytest.mark.parametrize(
    "grid",
    [
        "0",
        "-1",
        "0.000000099",
        "360.000000001",
        "0.0000001001",
        "NaN",
        "Infinity",
        "-Infinity",
        "1E+1000",
    ],
)
def test_policy_rejects_unsupported_grid(grid):
    with pytest.raises(ValueError):
        GeometryPolicy(Decimal(grid))


def test_policy_rejects_unknown_mode_and_version():
    with pytest.raises(ValueError):
        GeometryPolicy(
            Decimal("0.0000001"),
            "ROUND_HALF_EVEN",
        )
    with pytest.raises(ValueError):
        GeometryPolicy(
            Decimal("0.0000001"),
            version=2,
        )


@pytest.mark.parametrize(
    "value, grid, expected",
    [
        ("0.00000015", "0.0000001", "0.0000002"),
        ("-0.00000015", "0.0000001", "-0.0000002"),
        ("0.000000149999999999999999999", "0.0000001", "0.0000001"),
        ("-0.000000149999999999999999999", "0.0000001", "-0.0000001"),
        ("0.000000375", "0.00000025", "0.0000005"),
        ("-0.000000375", "0.00000025", "-0.0000005"),
        ("0.00000045", "0.0000003", "0.0000006"),
        ("-0.0", "0.0000001", "0"),
        ("5E-324", "0.0000001", "0"),
    ],
)
def test_quantization_preserves_midpoints_under_hostile_context(
    value,
    grid,
    expected,
):
    context = Context(
        prec=2,
        rounding=ROUND_DOWN,
    )
    context.traps[Inexact] = True
    context.traps[Rounded] = True
    with localcontext(context):
        result = quantize_ordinate(
            Decimal(value),
            GeometryPolicy(Decimal(grid)),
        )
        assert result == Decimal(expected)


def test_quantization_matches_independent_rational_oracle():
    for grid in ["0.0000001", "0.00000025", "0.0000003", "0.123456789"]:
        policy = GeometryPolicy(Decimal(grid))
        for value in [
            "-179.999999999999999",
            "-0.000000150000000000001",
            "-5E-324",
            "0",
            "0.000000149999999999999",
            "44.820500001",
            "180",
        ]:
            ratio = Fraction(Decimal(value)) / Fraction(Decimal(grid))
            quotient, remainder = divmod(
                abs(ratio.numerator),
                ratio.denominator,
            )
            ticks = quotient + (2 * remainder >= ratio.denominator)
            if ratio < 0:
                ticks = -ticks
            assert Fraction(
                quantize_ordinate(
                    Decimal(value),
                    policy,
                )
            ) == ticks * Fraction(Decimal(grid))


@pytest.mark.parametrize(
    "value, expected",
    [("-0.00", "0"), ("1.00", "1"), ("1E+3", "1000"), ("0.0000002500", "0.00000025")],
)
def test_decimal_text_is_context_independent(
    value,
    expected,
):
    with localcontext(Context(prec=1)):
        assert decimal_text(Decimal(value)) == expected
