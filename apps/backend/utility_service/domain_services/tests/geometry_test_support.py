from decimal import Decimal

from utility_service.domain_services.edit_geometry.types import GeometryValue


def line(*positions):
    return GeometryValue(
        "LineString",
        tuple(tuple(Decimal(str(v)) for v in p) for p in positions),
    )


BASELINE = line(
    ("65.52", "44.82"),
    ("65.525", "44.8205"),
    ("65.53", "44.82"),
)
MOVED = line(
    ("65.52", "44.82"),
    ("65.525", "44.8215"),
    ("65.53", "44.82"),
)
