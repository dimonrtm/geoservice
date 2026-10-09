"""Lossless boundary between PostGIS binary64 storage and Decimal geometry."""

import math
import struct
from decimal import Decimal

from shapely import from_wkb, get_coordinate_dimension, get_srid, set_srid, to_wkb
from shapely.errors import GEOSException
from shapely.geometry import LineString, Point

from utility_service.domain_services.edit_geometry.structure import validate_geometry_value
from utility_service.domain_services.edit_geometry.types import (
    GeometryValue,
    InvalidGeometryContext,
)


def decode_geometry(ewkb: bytes) -> GeometryValue:
    try:
        if len(ewkb) < 9 or ewkb[0] not in (0, 1):
            raise ValueError("Некорректный заголовок EWKB.")
        endian = "<" if ewkb[0] == 1 else ">"
        type_code, srid = struct.unpack_from(
            endian + "II",
            ewkb,
            1,
        )
        if srid != 4326 or type_code not in (0x20000001, 0x20000002):
            raise ValueError(
                "Ожидалась геометрия Point или LineString с координатами XY и SRID 4326."
            )
        expected_length = (
            25
            if type_code == 0x20000001
            else 13
            + 16
            * struct.unpack_from(
                endian + "I",
                ewkb,
                9,
            )[0]
        )
        if len(ewkb) != expected_length:
            raise ValueError("Некорректная длина EWKB.")
        shape = from_wkb(ewkb)
        if shape.is_empty or get_srid(shape) != 4326 or get_coordinate_dimension(shape) != 2:
            raise ValueError("Некорректная геометрия в хранилище.")
        value = GeometryValue(
            shape.geom_type,
            tuple(tuple(Decimal(repr(v)) for v in p) for p in shape.coords),
        )
        validate_geometry_value(value)
        return value
    except (ValueError, TypeError, struct.error, GEOSException) as error:
        raise InvalidGeometryContext("Некорректная EWKB-геометрия.") from error


def reversible_float(ordinate: Decimal) -> float:
    number = float(ordinate)
    if not math.isfinite(number) or Decimal(repr(number)) != ordinate:
        raise InvalidGeometryContext("Координата теряет точность при записи в binary64.")
    return number


def geometry_to_geojson(value: GeometryValue) -> dict[str, object]:
    validate_geometry_value(value)
    positions = [[reversible_float(v) for v in p] for p in value.coordinates]
    return {
        "type": value.type,
        "coordinates": positions[0] if value.type == "Point" else positions,
    }


def encode_geometry(value: GeometryValue) -> bytes:
    coordinates = geometry_to_geojson(value)["coordinates"]
    shape = Point(coordinates) if value.type == "Point" else LineString(coordinates)
    return to_wkb(
        set_srid(
            shape,
            value.srid,
        ),
        include_srid=True,
        byte_order=1,
    )
