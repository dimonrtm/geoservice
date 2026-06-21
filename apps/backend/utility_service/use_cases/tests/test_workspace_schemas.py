from typing import get_args
from uuid import uuid4

from utility_service.use_cases.schemas.workspace import (
    WorkspaceAoiOut,
    WorkspaceEditVersionOut,
    WorkspaceFeatureCollectionOut,
    WorkspaceOut,
    WorkspaceScopeOut,
    WorkspaceWorkOrderOut,
)


def test_workspace_edit_version_uses_workspace_local_payload_schemas() -> None:
    features_type = WorkspaceEditVersionOut.model_fields["features"].annotation
    association_type = get_args(WorkspaceEditVersionOut.model_fields["associations"].annotation)[0]

    assert features_type.__module__.startswith("utility_service.use_cases.schemas.workspace")
    assert association_type.__module__.startswith("utility_service.use_cases.schemas.workspace")


def test_workspace_schema_uses_expected_wire_aliases() -> None:
    aoi = WorkspaceAoiOut(
        id=uuid4(),
        name="Рабочая область WO-001",
        description=None,
        geometry={
            "type": "Polygon",
            "coordinates": [],
        },
        extent=[65.495, 44.795, 65.545, 44.835],
    )
    edit_version = WorkspaceEditVersionOut(
        id=uuid4(),
        status="open",
        base_network_revision=1,
        features=WorkspaceFeatureCollectionOut(features=[]),
        associations=[],
    )
    payload = WorkspaceOut(
        work_order=WorkspaceWorkOrderOut(
            id=uuid4(),
            code="WO-001",
            title="Проверка участка фидера",
            description=None,
            status="in_progress",
            scope=WorkspaceScopeOut(aoi=aoi),
            edit_version=edit_version,
        )
    ).model_dump(by_alias=True)

    assert "workOrder" in payload
    assert payload["workOrder"]["scope"]["aoi"]["name"] == "Рабочая область WO-001"
    assert payload["workOrder"]["editVersion"]["baseNetworkRevision"] == 1
