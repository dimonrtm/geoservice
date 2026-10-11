from dataclasses import dataclass
from typing import Any, Literal
from uuid import UUID


@dataclass(frozen=True)
class SaveGeometryResult:
    status_code: int
    payload: dict[str, Any]


@dataclass(frozen=True)
class SaveGeometryRejection:
    status_code: int
    code: str
    message: str
    retry_on_access_change: bool = False

    @classmethod
    def from_code(
        cls,
        code: str,
        message: str,
        *,
        retry_on_access_change: bool = False,
    ) -> "SaveGeometryRejection":
        statuses = {
            "ROLE_NOT_ALLOWED": 403,
            "EDIT_VERSION_NOT_FOUND": 404,
            "SAVE_CONTEXT_CLOSED": 409,
            "DRAFT_VERSION_STALE": 409,
            "COMMAND_ID_REUSED": 409,
            "MULTIPLE_FEATURE_CHANGE_NOT_ALLOWED": 409,
            "FEATURE_NOT_EDITABLE": 422,
            "WORK_ORDER_CONTEXT_INVALID": 422,
            "GEOMETRY_STRUCTURE_CHANGED": 422,
            "GEOMETRY_INVALID": 422,
            "GEOMETRY_OUTSIDE_AOI": 422,
        }
        return cls(
            statuses[code],
            code,
            message,
            retry_on_access_change,
        )


def build_geometry_save_payload(
    *,
    command_id: UUID,
    feature_id: UUID,
    draft_revision: int,
    operation: Literal["unchanged", "updated"],
    geometry: dict[str, Any],
) -> dict[str, Any]:
    changed = operation == "updated"
    return {
        "commandId": str(command_id),
        "commandState": "succeeded",
        "draftVersionToken": str(draft_revision),
        "operation": operation,
        "hasPersistedChangeSet": changed,
        "updatedFeature": {
            "id": str(feature_id),
            "geometry": geometry,
        },
        "basicValidation": (
            {
                "geometryStatus": "passed",
                "aoiStatus": "passed",
                "positionalAccuracyStatus": "POSITIONAL_ACCURACY_UNVERIFIED",
                "dirtyRelativeToBaseline": "passed",
            }
            if changed
            else None
        ),
    }
