from dataclasses import dataclass

from utility_service.infrastructure.postgresql.geometry_codec import (
    decode_geometry,
    geometry_to_geojson,
)
from utility_service.infrastructure.postgresql.repository_rows.workspace import (
    WorkspaceAggregateRow,
)
from utility_service.use_cases.schemas.edit_version.geometry_contract import BasicValidationOut
from utility_service.use_cases.schemas.workspace.change_set_out import WorkspaceChangeSetOut


@dataclass(frozen=True)
class WorkspaceDraftProjection:
    draft_version_token: str
    has_persisted_change_set: bool
    basic_validation: BasicValidationOut | None
    change_set: WorkspaceChangeSetOut | None


def project_workspace_draft(aggregate: WorkspaceAggregateRow) -> WorkspaceDraftProjection:
    version = aggregate.edit_version
    baseline = aggregate.baseline_state
    if (
        baseline is None
        or baseline.id != version.default_state_id
        or baseline.work_order_id != aggregate.work_order.id
        or baseline.base_network_revision != version.base_network_revision
        or baseline.status != "active"
        or version.draft_revision < 1
    ):
        raise ValueError("Несогласованное исходное состояние рабочей версии.")

    change_set = None
    for pair in aggregate.draft_feature_pairs:
        if (
            pair.current_geometry_ewkb is None
            or pair.baseline_geometry_ewkb is None
            or pair.current_feature_type != pair.baseline_feature_type
            or pair.current_feature_type not in ("line", "junction", "device")
            or pair.operation not in ("unchanged", "updated")
        ):
            raise ValueError("Текущая и исходная геометрия не согласованы.")
        current = decode_geometry(bytes.fromhex(pair.current_geometry_ewkb))
        original = decode_geometry(bytes.fromhex(pair.baseline_geometry_ewkb))
        expected_type = "LineString" if pair.current_feature_type == "line" else "Point"
        if current.type != expected_type or original.type != expected_type:
            raise ValueError("Тип геометрии не соответствует типу объекта.")
        if current == original:
            if pair.operation != "unchanged":
                raise ValueError("Операция не соответствует чистой геометрии.")
            continue
        if (
            change_set is not None
            or pair.operation != "updated"
            or not pair.visible
            or original.type != "LineString"
            or len(original.coordinates) < 3
            or len(current.coordinates) != len(original.coordinates)
        ):
            raise ValueError("Черновик выходит за границы первого редактирования.")
        changed_indices = [
            index
            for index, (before, after) in enumerate(
                zip(
                    original.coordinates,
                    current.coordinates,
                )
            )
            if before != after
        ]
        if len(changed_indices) != 1 or not 0 < changed_indices[0] < len(original.coordinates) - 1:
            raise ValueError("Ожидалось изменение одной внутренней вершины.")
        change_set = WorkspaceChangeSetOut(
            feature_id=pair.feature_id,
            vertex_index=changed_indices[0],
            baseline_geometry=geometry_to_geojson(original),
            operation="updated",
        )

    return WorkspaceDraftProjection(
        draft_version_token=str(version.draft_revision),
        has_persisted_change_set=change_set is not None,
        basic_validation=(
            BasicValidationOut(
                geometry_status="passed",
                aoi_status="passed",
                positional_accuracy_status="POSITIONAL_ACCURACY_UNVERIFIED",
                dirty_relative_to_baseline="passed",
            )
            if change_set is not None
            else None
        ),
        change_set=change_set,
    )
