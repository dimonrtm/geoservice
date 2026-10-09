from decimal import Decimal
import json
from uuid import UUID

from utility_service.domain_services.edit_geometry.types import GeometryValue
from utility_service.use_cases.schemas.edit_version.geometry_save_in import GeometrySaveRequest


class GeometryRequestFormatError(ValueError):
    pass


def parse_number(token: str) -> Decimal:
    if len(token) > 64:
        raise GeometryRequestFormatError("Слишком длинное число координаты.")
    _, separator, exponent = token.lower().partition("e")
    if separator and abs(int(exponent)) > 324:
        raise GeometryRequestFormatError("Слишком большой по модулю показатель степени координаты.")
    return Decimal(token)


def reject_constant(token: str) -> None:
    raise GeometryRequestFormatError("Координаты должны быть конечными числами.")


def unique_object(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise GeometryRequestFormatError("Повторяющиеся поля JSON запрещены.")
        result[key] = value
    return result


def parse_geometry_save_request(body: bytes) -> GeometrySaveRequest:
    try:
        value = json.loads(
            body,
            parse_float=parse_number,
            parse_int=parse_number,
            parse_constant=reject_constant,
            object_pairs_hook=unique_object,
        )
        if not isinstance(
            value,
            dict,
        ) or set(value) != {
            "commandId",
            "draftVersionToken",
            "geometry",
        }:
            raise GeometryRequestFormatError("Неправильные поля запроса.")
        if not isinstance(
            value["commandId"],
            str,
        ):
            raise GeometryRequestFormatError("commandId должен быть UUID-строкой.")
        command_id = UUID(value["commandId"])
        token = value["draftVersionToken"]
        if (
            not isinstance(
                token,
                str,
            )
            or not token
        ):
            raise GeometryRequestFormatError("draftVersionToken должен быть непустой строкой.")
        geometry = value["geometry"]
        if not isinstance(
            geometry,
            dict,
        ) or set(
            geometry
        ) != {"type", "coordinates"}:
            raise GeometryRequestFormatError("Неправильные поля geometry.")
        if geometry["type"] != "LineString":
            raise GeometryRequestFormatError("Ожидался LineString.")
        coordinates = geometry["coordinates"]
        if (
            not isinstance(
                coordinates,
                list,
            )
            or len(coordinates) < 2
        ):
            raise GeometryRequestFormatError("LineString должен содержать минимум две вершины.")
        for position in coordinates:
            if (
                not isinstance(
                    position,
                    list,
                )
                or len(position) != 2
                or any(
                    not isinstance(
                        v,
                        Decimal,
                    )
                    or not v.is_finite()
                    for v in position
                )
            ):
                raise GeometryRequestFormatError("Ожидались конечные числовые XY-пары.")
            if not (-180 <= position[0] <= 180 and -90 <= position[1] <= 90):
                raise GeometryRequestFormatError("Координаты находятся вне диапазона EPSG:4326.")
        return GeometrySaveRequest(
            command_id=command_id,
            draft_version_token=token,
            geometry=GeometryValue(
                "LineString",
                tuple(tuple(p) for p in coordinates),
            ),
        )
    except GeometryRequestFormatError:
        raise
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        raise GeometryRequestFormatError("Некорректный JSON-запрос сохранения геометрии.") from exc
