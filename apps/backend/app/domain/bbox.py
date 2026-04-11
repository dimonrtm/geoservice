from dataclasses import dataclass

from domain.exceptions.business_validation_exception import BusinessValidationException


@dataclass
class Bbox:
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float


def parse_bbox(bbox: str) -> Bbox:
    bbox_list = bbox.split(",")
    if len(bbox_list) != 4:
        raise BusinessValidationException("Bbox должен содержать 4 вещественных числа")

    try:
        bbox_list = [float(x) for x in bbox_list]
    except (ValueError, TypeError) as e:
        raise BusinessValidationException("Bbox должен содержать 4 вещественных числа") from e

    min_lon, min_lat, max_lon, max_lat = bbox_list

    if not -180 <= min_lon <= 180 or not -180 <= max_lon <= 180:
        raise BusinessValidationException("Долгота должна принадлежать диапазону от -180 до 180")

    if not -90 <= min_lat <= 90 or not -90 <= max_lat <= 90:
        raise BusinessValidationException("Широта должна принадлежать диапазону от -90 до 90")

    if min_lat >= max_lat:
        raise BusinessValidationException("Минимальная широта должна быть меньше максимальной")

    if min_lon >= max_lon:
        raise BusinessValidationException("Минимальная долгота должна быть меньше максимальной")

    return Bbox(min_lon, min_lat, max_lon, max_lat)
