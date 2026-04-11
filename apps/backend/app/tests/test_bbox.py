import pytest

from domain.bbox import Bbox, parse_bbox
from domain.exceptions.business_validation_exception import (
    BusinessValidationException,
)


def test_parse_bbox_returns_bbox_for_valid_input() -> None:
    bbox = parse_bbox("10,20,30,40")

    assert bbox == Bbox(min_lon=10.0, min_lat=20.0, max_lon=30.0, max_lat=40.0)


@pytest.mark.parametrize(
    ("raw_bbox", "message"),
    [
        ("10,20,30", "Bbox должен содержать 4 вещественных числа"),
        ("181,20,30,40", "Долгота должна принадлежать диапазону от -180 до 180"),
        ("10,95,30,40", "Широта должна принадлежать диапазону от -90 до 90"),
        ("10,50,30,40", "Минимальная широта должна быть меньше максимальной"),
        ("50,10,30,40", "Минимальная долгота должна быть меньше максимальной"),
    ],
)
def test_parse_bbox_raises_business_validation_for_invalid_input(
    raw_bbox: str, message: str
) -> None:
    with pytest.raises(BusinessValidationException, match=message):
        parse_bbox(raw_bbox)
