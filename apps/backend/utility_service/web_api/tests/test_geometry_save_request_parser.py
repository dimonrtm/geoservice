from decimal import Decimal

import pytest

from utility_service.web_api.parsers.geometry_save_request import (
    GeometryRequestFormatError,
    parse_geometry_save_request,
)


def body(
    number="0.000000149999999999999999999",
    token='"01"',
):
    return (
        '{"commandId":"00000000-0000-0000-0000-000000000001",'
        '"draftVersionToken":' + token + ',"geometry":{"type":"LineString",'
        '"coordinates":[[0,0],[' + number + ",1],[2,0]]}}"
    ).encode()


def test_parser_retains_exact_decimal_before_midpoint():
    parsed = parse_geometry_save_request(body())
    assert parsed.geometry.coordinates[1][0] == Decimal("0.000000149999999999999999999")
    assert parsed.draft_version_token == "01"
    assert all(
        isinstance(
            v,
            Decimal,
        )
        for p in parsed.geometry.coordinates
        for v in p
    )


@pytest.mark.parametrize(
    "number",
    ["1", "1.0", "1e0"],
)
def test_numeric_notation_is_equivalent(number):
    assert parse_geometry_save_request(body(number)).geometry.coordinates[1][0] == Decimal(1)


def test_signed_zero_and_subnormal_storage_value_are_accepted():
    assert parse_geometry_save_request(body("-0")).geometry.coordinates[1][0].is_signed()
    assert parse_geometry_save_request(body("5e-324")).geometry.coordinates[1][0] == Decimal(
        "5e-324"
    )


@pytest.mark.parametrize(
    "number",
    ['"1"', "true", "null", "NaN", "Infinity", "-Infinity", "181", "1e-325", "0." + "1" * 63],
)
def test_parser_rejects_invalid_ordinate(number):
    with pytest.raises(GeometryRequestFormatError):
        parse_geometry_save_request(body(number))


@pytest.mark.parametrize(
    "token",
    ['""', "1", "true", "null"],
)
def test_token_is_nonempty_opaque_string(token):
    with pytest.raises(GeometryRequestFormatError):
        parse_geometry_save_request(body(token=token))


@pytest.mark.parametrize(
    "old, new",
    [
        (b'"LineString"', b'"MultiLineString"'),
        (b'"coordinates":[[0,0],[0.000000149999999999999999999,1],[2,0]]', b'"coordinates":[]'),
        (
            b'"coordinates":[[0,0],[0.000000149999999999999999999,1],[2,0]]',
            b'"coordinates":[[0,0]]',
        ),
        (b"[0,0]", b"[0,0,0]"),
        (b'"type":"LineString"', b'"type":"LineString","type":"LineString"'),
        (b'"type":"LineString"', b'"type":"LineString","extra":1'),
        (b'"commandId":', b'"extra":1,"commandId":'),
        (b"[2,0]", b"[2,91]"),
    ],
)
def test_parser_rejects_ambiguous_or_malformed_shape(
    old,
    new,
):
    with pytest.raises(GeometryRequestFormatError):
        parse_geometry_save_request(
            body().replace(
                old,
                new,
            )
        )


def test_two_vertex_line_is_valid_request_format():
    parsed = parse_geometry_save_request(
        body().replace(
            b",[2,0]",
            b"",
        )
    )
    assert len(parsed.geometry.coordinates) == 2


def test_number_token_length_boundary():
    assert parse_geometry_save_request(body("0." + "1" * 62)).geometry.coordinates[1][0] == Decimal(
        "0." + "1" * 62
    )
