from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WorkOrderEditErrorOut(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    code: str
    message: str
    correlation_id: str = Field(alias="correlationId")


EDIT_ERROR_RESPONSES = {
    code: {
        "model": WorkOrderEditErrorOut,
    }
    for code in (401, 403, 404, 409, 422, 500)
}

# Documentation only: runtime parsing must preserve raw JSON numeric tokens and duplicate keys.
GEOMETRY_SAVE_REQUEST_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["commandId", "draftVersionToken", "geometry"],
    "description": (
        "Запрос должен содержать только указанные поля, без повторяющихся имён. "
        "Координаты передаются числами без кавычек; NaN и бесконечность не допускаются. "
        "Запись каждого числа может содержать не более 64 символов. "
        "При записи через e или E показатель степени должен быть от -324 до 324. "
        "Если запрос отклонён из-за ошибки формата, его можно исправить "
        "и отправить с тем же commandId."
    ),
    "properties": {
        "commandId": {
            "type": "string",
            "format": "uuid",
        },
        "draftVersionToken": {
            "type": "string",
            "minLength": 1,
        },
        "geometry": {
            "type": "object",
            "additionalProperties": False,
            "required": ["type", "coordinates"],
            "properties": {
                "type": {
                    "type": "string",
                    "const": "LineString",
                },
                "coordinates": {
                    "type": "array",
                    "minItems": 2,
                    "items": {
                        "type": "array",
                        "minItems": 2,
                        "maxItems": 2,
                        "prefixItems": [
                            {
                                "type": "number",
                                "minimum": -180,
                                "maximum": 180,
                            },
                            {
                                "type": "number",
                                "minimum": -90,
                                "maximum": 90,
                            },
                        ],
                    },
                },
            },
        },
    },
}
