from dataclasses import dataclass
from typing import Any, Literal
from uuid import UUID


@dataclass(frozen=True)
class SaveGeometryResult:
    status_code: int
    payload: dict[str, Any]


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
