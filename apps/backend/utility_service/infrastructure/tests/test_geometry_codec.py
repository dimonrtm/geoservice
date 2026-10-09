from decimal import Decimal
import struct

import pytest
from shapely import from_wkt, set_srid, to_wkb

from utility_service.domain_services.edit_geometry.types import (
    GeometryValue,
    InvalidGeometryContext,
)
from utility_service.domain_services.tests.geometry_test_support import line
from utility_service.infrastructure.postgresql.geometry_codec import (
    decode_geometry,
    encode_geometry,
    geometry_to_geojson,
)


@pytest.mark.parametrize(
    "value",
    [
        GeometryValue(
            "Point",
            ((Decimal("-0.0"), Decimal("44.82000000001")),),
        ),
        line(
            ("65.520000000001", "44.82"),
            ("65.5250000499", "44.8205000501"),
            ("65.53", "44.82"),
        ),
        line(
            (0, 0),
            ("0.00000025", "-0.00000025"),
            (1, 1),
        ),
    ],
)
def test_codec_roundtrip_preserves_storage_ordinates(value):
    encoded = encode_geometry(value)
    decoded = decode_geometry(encoded)
    assert decoded == value
    assert encode_geometry(decoded) == encoded
    for before, after in zip(
        value.coordinates,
        decoded.coordinates,
        strict=True,
    ):
        for x, y in zip(
            before,
            after,
            strict=True,
        ):
            assert x.is_signed() == y.is_signed()
    assert geometry_to_geojson(decoded)["type"] == value.type


@pytest.mark.parametrize(
    "wkt,srid",
    [
        ("POINT(1 2)", 3857),
        ("POINT(1 2)", 0),
        ("POINT Z(1 2 3)", 4326),
        ("LINESTRING Z(1 2 3,4 5 6)", 4326),
        ("POINT EMPTY", 4326),
        ("MULTILINESTRING((1 2,3 4))", 4326),
        ("POINT(Infinity 2)", 4326),
    ],
)
def test_codec_rejects_unsupported_storage(
    wkt,
    srid,
):
    with pytest.raises(InvalidGeometryContext):
        decode_geometry(
            to_wkb(
                set_srid(
                    from_wkt(wkt),
                    srid,
                ),
                include_srid=True,
            )
        )


def test_codec_rejects_m_ordinate_and_malformed_wkb():
    # EWKB Point M + SRID, independent of installed Shapely's M support.
    ewkb = struct.pack(
        "<BII3d",
        1,
        0x60000001,
        4326,
        1.0,
        2.0,
        3.0,
    )
    for raw in (ewkb, b"broken", b""):
        with pytest.raises(InvalidGeometryContext):
            decode_geometry(raw)


def test_codec_refuses_irreversible_decimal_to_double():
    value = GeometryValue(
        "Point",
        ((Decimal("65.1234567890123456789"), Decimal("0")),),
    )
    with pytest.raises(InvalidGeometryContext):
        encode_geometry(value)
    with pytest.raises(InvalidGeometryContext):
        geometry_to_geojson(value)


def test_codec_work_is_bounded_for_representative_line():
    value = line(*[(str(i / 1000), "44.82") for i in range(2000)])
    assert decode_geometry(encode_geometry(value)) == value
