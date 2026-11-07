from utility_service.infrastructure.postgresql.geometry_codec import decode_geometry
from utility_service.infrastructure.postgresql.repository_rows.edit_geometry import (
    EditGeometryDefaultState,
)
from utility_service.infrastructure.postgresql.repository_rows.edit_version_read import (
    VersionComparisonRow,
)
from utility_service.infrastructure.postgresql.repositories.default_state_repository import (
    ComparisonBaseline,
)
from utility_service.use_cases.schemas.edit_version.geometry_contract import BasicValidationOut
from utility_service.use_cases.schemas.edit_version.change_set import (
    VersionChangeSetOut,
    ChangedVertexOut,
)


def validate_baseline(
    version_data: VersionComparisonRow, state: EditGeometryDefaultState | None
) -> None:
    version = version_data.edit_version
    if (
        state is None
        or state.id != version.default_state_id
        or state.work_order_id != version_data.work_order_id
        or state.base_network_revision != version.base_network_revision
        or state.status != "active"
        or version.draft_revision < 1
    ):
        raise ValueError("Несогласованное исходное состояние рабочей версии.")


def project_version_changes(
    version_data: VersionComparisonRow, baseline: ComparisonBaseline | None
) -> VersionChangeSetOut:
    if baseline is None:
        raise ValueError("Отсутствует исходный снимок.")
    validate_baseline(version_data, baseline.state)
    originals = {feature.feature_id: feature for feature in baseline.features}
    if originals.keys() != {feature.feature_id for feature in version_data.features}:
        raise ValueError("Наборы объектов рабочей версии и исходного снимка расходятся.")
    change_set = None
    for feature in version_data.features:
        baseline_feature = originals[feature.feature_id]
        if (
            feature.geometry_ewkb is None
            or baseline_feature.geometry_ewkb is None
            or feature.feature_type != baseline_feature.feature_type
            or feature.feature_type not in ("line", "junction", "device")
            or feature.operation not in ("unchanged", "updated")
        ):
            raise ValueError("Текущая и исходная геометрия не согласованы.")
        current = decode_geometry(bytes.fromhex(feature.geometry_ewkb))
        original = decode_geometry(bytes.fromhex(baseline_feature.geometry_ewkb))
        expected_type = "LineString" if feature.feature_type == "line" else "Point"
        if current.type != expected_type or original.type != expected_type:
            raise ValueError("Тип геометрии не соответствует типу объекта.")
        if current == original:
            if feature.operation != "unchanged":
                raise ValueError("Операция не соответствует чистой геометрии.")
            continue
        if (
            change_set is not None
            or feature.operation != "updated"
            or not feature.visible
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
        change_set = ChangedVertexOut(
            feature_id=feature.feature_id,
            vertex_index=changed_indices[0],
            operation="updated",
        )

    return VersionChangeSetOut(
        draft_version_token=str(version_data.edit_version.draft_revision),
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
