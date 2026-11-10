import pytest

from utility_service.domain_services.bbox import Bbox, InvalidBboxError, parse_bbox


def test_parse_bbox_returns_bbox_for_valid_input() -> None:
    bbox = parse_bbox("10,20,30,40")

    assert bbox == Bbox(min_lon=10.0, min_lat=20.0, max_lon=30.0, max_lat=40.0)


@pytest.mark.parametrize(
    ("raw_bbox", "message"),
    [
        ("10,20,30", "Bbox должен содержать 4 вещественных числа"),
        ("x,20,30,40", "Bbox должен содержать 4 вещественных числа"),
        ("nan,20,30,40", "Долгота должна принадлежать диапазону от -180 до 180"),
        ("10,20,inf,40", "Долгота должна принадлежать диапазону от -180 до 180"),
        ("10,nan,30,40", "Широта должна принадлежать диапазону от -90 до 90"),
        ("10,20,30,inf", "Широта должна принадлежать диапазону от -90 до 90"),
        ("181,95,30,40", "Долгота должна принадлежать диапазону от -180 до 180"),
        ("10,20,10,40", "Минимальная долгота должна быть меньше максимальной"),
        ("10,20,30,20", "Минимальная широта должна быть меньше максимальной"),
        ("181,20,30,40", "Долгота должна принадлежать диапазону от -180 до 180"),
        ("10,95,30,40", "Широта должна принадлежать диапазону от -90 до 90"),
        ("10,50,30,40", "Минимальная широта должна быть меньше максимальной"),
        ("50,10,30,40", "Минимальная долгота должна быть меньше максимальной"),
    ],
)
def test_parse_bbox_preserves_validation_messages(raw_bbox: str, message: str) -> None:
    with pytest.raises(InvalidBboxError) as raised:
        parse_bbox(raw_bbox)
    assert str(raised.value) == message


def test_parse_bbox_accepts_coordinate_bounds() -> None:
    assert parse_bbox("-180,-90,180,90") == Bbox(-180.0, -90.0, 180.0, 90.0)


def test_parse_bbox_preserves_conversion_cause() -> None:
    with pytest.raises(InvalidBboxError) as raised:
        parse_bbox("x,20,30,40")
    assert isinstance(raised.value.__cause__, ValueError)
