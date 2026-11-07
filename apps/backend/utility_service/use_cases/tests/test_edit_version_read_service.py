import asyncio
from types import SimpleNamespace
from typing import get_type_hints
from unittest.mock import AsyncMock
from uuid import uuid4
from decimal import Decimal

import pytest
from utility_service.domain_services.edit_geometry.types import GeometryValue
from utility_service.infrastructure.postgresql.geometry_codec import encode_geometry

from utility_service.infrastructure.postgresql.models.user import UserRole
from utility_service.infrastructure.postgresql.models.work_order import (
    EditVersionStatus,
    WorkOrderStatus,
)
from utility_service.infrastructure.postgresql.repository_rows.edit_version_read import (
    EditVersionMapRow,
)
from utility_service.use_cases.domain.exceptions.work_order_api_error import WorkOrderApiError
from utility_service.use_cases.services.edit_version_read_service import EditVersionReadService


def user(role: UserRole = UserRole.EDITOR, *, is_active: bool = True) -> SimpleNamespace:
    return SimpleNamespace(id=uuid4(), role=role, is_active=is_active)


def workspace_row(actor_id, *, work_order_status=WorkOrderStatus.IN_PROGRESS):
    feature_id = uuid4()
    connected_feature_id = uuid4()
    aggregate = SimpleNamespace(
        work_order=SimpleNamespace(
            id=uuid4(),
            code="WO-001",
            title="Проверка участка фидера",
            description=None,
            status=work_order_status,
            assignee_user_id=actor_id,
        ),
        edit_version=SimpleNamespace(
            id=uuid4(),
            status=EditVersionStatus.OPEN,
            base_network_revision=12,
            draft_revision=1,
            default_state_id=uuid4(),
        ),
        aoi=SimpleNamespace(
            id=uuid4(),
            name="Рабочая область WO-001",
            description=None,
            geometry_data={"type": "Polygon", "coordinates": []},
            extent=[65.495, 44.795, 65.545, 44.835],
        ),
        features_data=[
            {
                "id": feature_id,
                "asset_code": "J-001",
                "feature_type": "junction",
                "geometry_data": {"type": "Point", "coordinates": [65.5, 44.82]},
                "properties": {"name": "Junction"},
                "network_version": 1,
                "operation": "unchanged",
            },
            {
                "id": connected_feature_id,
                "asset_code": "L-001",
                "feature_type": "line",
                "geometry_data": {
                    "type": "LineString",
                    "coordinates": [[65.5, 44.82], [65.51, 44.821]],
                },
                "properties": {"name": "Line"},
                "network_version": 1,
                "operation": "unchanged",
            },
        ],
        associations_data=[
            {
                "id": uuid4(),
                "from_feature_id": feature_id,
                "to_feature_id": connected_feature_id,
                "association_type": "connectivity",
                "version": 1,
            }
        ],
    )
    for feature in aggregate.features_data:
        geojson = feature.pop("geometry_data")
        positions = (
            [geojson["coordinates"]] if geojson["type"] == "Point" else geojson["coordinates"]
        )
        ewkb = encode_geometry(
            GeometryValue(
                geojson["type"],
                tuple(tuple(Decimal(str(v)) for v in p) for p in positions),
            )
        ).hex()
        feature["geometry_ewkb"] = ewkb
    return aggregate


def repository(**methods):
    fake = SimpleNamespace()
    for name, return_value in methods.items():
        setattr(fake, name, AsyncMock(return_value=return_value))
    return fake


def build_service(actor, aggregate) -> EditVersionReadService:
    return EditVersionReadService(
        user_repository=repository(get_by_id=actor),
        work_order_repository=repository(get_edit_version_map=aggregate),
        default_state_repository=repository(),
    )


def test_workspace_from_aggregate_uses_repository_row_contract() -> None:
    annotation = get_type_hints(EditVersionReadService.map_response)["version_map"]

    assert annotation is EditVersionMapRow


def test_editor_gets_workspace_for_assigned_open_edit_version() -> None:
    actor = user()
    aggregate = workspace_row(actor.id)
    service = build_service(actor, aggregate)

    result = asyncio.run(
        service.get_version_map(
            work_order_id=aggregate.work_order.id,
            edit_version_id=aggregate.edit_version.id,
            actor_id=actor.id,
        )
    )

    payload = result.model_dump(by_alias=True)
    assert payload["workOrder"]["id"] == aggregate.work_order.id
    assert payload["workOrder"]["scope"]["aoi"]["name"] == "Рабочая область WO-001"
    assert payload["workOrder"]["editVersion"]["baseNetworkRevision"] == 12
    assert payload["workOrder"]["editVersion"]["draftVersionToken"] == "1"
    assert (
        payload["workOrder"]["editVersion"]["features"]["features"][0]["properties"]["assetCode"]
        == "J-001"
    )
    association = payload["workOrder"]["editVersion"]["associations"][0]
    assert association["fromFeatureId"] != association["toFeatureId"]


def test_reviewer_is_denied() -> None:
    actor = user(UserRole.REVIEWER)
    service = build_service(actor, None)

    with pytest.raises(WorkOrderApiError) as exc_info:
        asyncio.run(service.get_version_map(uuid4(), uuid4(), actor.id))

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "ROLE_NOT_ALLOWED"


def test_missing_workspace_returns_404() -> None:
    actor = user()
    service = build_service(actor, None)

    with pytest.raises(WorkOrderApiError) as exc_info:
        asyncio.run(service.get_version_map(uuid4(), uuid4(), actor.id))

    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "EDIT_VERSION_NOT_FOUND"


def test_wrong_assignee_is_masked_as_404() -> None:
    actor = user()
    aggregate = workspace_row(uuid4())
    service = build_service(actor, aggregate)

    with pytest.raises(WorkOrderApiError) as exc_info:
        asyncio.run(service.get_version_map(uuid4(), uuid4(), actor.id))

    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "EDIT_VERSION_NOT_FOUND"


def test_workspace_state_conflict_returns_409() -> None:
    actor = user()
    aggregate = workspace_row(actor.id, work_order_status=WorkOrderStatus.ASSIGNED)
    service = build_service(actor, aggregate)

    with pytest.raises(WorkOrderApiError) as exc_info:
        asyncio.run(service.get_version_map(uuid4(), uuid4(), actor.id))

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "EDIT_VERSION_STATE_CONFLICT"


def test_missing_aoi_returns_context_invalid() -> None:
    actor = user()
    aggregate = workspace_row(actor.id)
    aggregate.aoi = None
    service = build_service(actor, aggregate)

    with pytest.raises(WorkOrderApiError) as exc_info:
        asyncio.run(service.get_version_map(uuid4(), uuid4(), actor.id))

    assert exc_info.value.status_code == 422
    assert exc_info.value.code == "WORKSPACE_CONTEXT_INVALID"


@pytest.mark.parametrize(
    "assigned,expected",
    [(False, 404), (True, 422)],
)
def test_foreign_workspace_masks_corrupt_ewkb(
    assigned,
    expected,
):
    actor = user()
    aggregate = workspace_row(actor.id if assigned else uuid4())
    aggregate.features_data[0]["geometry_ewkb"] = "corrupt"
    service = build_service(
        actor,
        aggregate,
    )
    with pytest.raises(WorkOrderApiError) as error:
        asyncio.run(
            service.get_version_map(
                uuid4(),
                uuid4(),
                actor.id,
            )
        )
    assert error.value.status_code == expected
