from utility_service.use_cases.schemas.edit_version.change_set import VersionChangeSetOut
from typing import get_args
from uuid import uuid4

from utility_service.use_cases.schemas.edit_version.version_map import (
    MapAoiOut,
    MapEditVersionOut,
    MapFeatureCollectionOut,
    EditVersionMapOut,
    MapScopeOut,
    MapWorkOrderOut,
)


def test_workspace_edit_version_uses_workspace_local_payload_schemas() -> None:
    features_type = MapEditVersionOut.model_fields["features"].annotation
    association_type = get_args(MapEditVersionOut.model_fields["associations"].annotation)[0]

    assert features_type.__module__.startswith(
        "utility_service.use_cases.schemas.edit_version.version_map"
    )
    assert association_type.__module__.startswith(
        "utility_service.use_cases.schemas.edit_version.version_map"
    )


def test_workspace_schema_uses_expected_wire_aliases() -> None:
    aoi = MapAoiOut(
        id=uuid4(),
        name="Рабочая область WO-001",
        description=None,
        geometry={
            "type": "Polygon",
            "coordinates": [],
        },
        extent=[65.495, 44.795, 65.545, 44.835],
    )
    edit_version = MapEditVersionOut(
        id=uuid4(),
        status="open",
        base_network_revision=1,
        draft_version_token="1",
        features=MapFeatureCollectionOut(features=[]),
        associations=[],
    )
    payload = EditVersionMapOut(
        work_order=MapWorkOrderOut(
            id=uuid4(),
            code="WO-001",
            title="Проверка участка фидера",
            description=None,
            status="in_progress",
            scope=MapScopeOut(aoi=aoi),
            edit_version=edit_version,
        )
    ).model_dump(by_alias=True)

    assert "workOrder" in payload
    assert payload["workOrder"]["scope"]["aoi"]["name"] == "Рабочая область WO-001"
    assert payload["workOrder"]["editVersion"]["baseNetworkRevision"] == 1


def test_nullable_readback_fields_are_required():
    schema = VersionChangeSetOut.model_json_schema(mode="serialization")
    for field in ("draftVersionToken", "hasPersistedChangeSet", "basicValidation", "changeSet"):
        assert field in schema["required"]
    for field in ("basicValidation", "changeSet"):
        assert {"type": "null"} in schema["properties"][field]["anyOf"]
