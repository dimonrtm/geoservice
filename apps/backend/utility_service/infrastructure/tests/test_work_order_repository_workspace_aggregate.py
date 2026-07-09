import asyncio
from uuid import uuid4

from utility_service.infrastructure.postgresql.models.work_order import (
    EditVersionStatus,
    WorkOrderStatus,
)
from utility_service.infrastructure.postgresql.repositories.work_order_repository import (
    WORKSPACE_AGGREGATE_SQL,
    WORKSPACE_AGGREGATE_SQL_PATH,
    WorkOrderRepository,
)
from utility_service.infrastructure.postgresql.repository_rows.workspace import (
    WorkspaceAggregateRow,
)


class FakeMappingResult:
    def __init__(self, row):
        self.row = row

    def one_or_none(self):
        return self.row


class FakeResult:
    def __init__(self, row):
        self.row = row

    def mappings(self):
        return FakeMappingResult(self.row)


class FakeSession:
    def __init__(self, row):
        self.row = row
        self.execute_calls = []
        self.scalars_calls = []

    async def execute(self, statement, params):
        self.execute_calls.append((statement, params))
        return FakeResult(self.row)

    async def scalars(self, *args, **kwargs):
        self.scalars_calls.append((args, kwargs))
        raise AssertionError("Workspace aggregate read must use one execute call")


def test_workspace_aggregate_sql_lives_in_sql_file() -> None:
    assert WORKSPACE_AGGREGATE_SQL_PATH.name == "workspace_aggregate.sql"
    sql_text = WORKSPACE_AGGREGATE_SQL_PATH.read_text(encoding="utf-8")
    assert "workspace_features AS MATERIALIZED" in sql_text
    assert "JOIN workspace_features AS from_feature" in sql_text
    assert "JOIN workspace_features AS to_feature" in sql_text
    assert "ST_Intersects(context.aoi_geometry, feature.geometry)" in sql_text


def test_workspace_aggregate_row_dataclasses_live_next_to_repositories() -> None:
    assert WorkspaceAggregateRow.__module__.endswith(
        ".infrastructure.postgresql.repository_rows.workspace"
    )


def test_get_workspace_aggregate_uses_one_sql_round_trip_and_maps_row() -> None:
    work_order_id = uuid4()
    edit_version_id = uuid4()
    aoi_id = uuid4()
    assignee_user_id = uuid4()
    feature_id = uuid4()
    connected_feature_id = uuid4()
    association_id = uuid4()
    session = FakeSession(
        {
            "work_order_id": work_order_id,
            "work_order_code": "WO-001",
            "work_order_title": "Feeder area check",
            "work_order_description": None,
            "work_order_status": "in_progress",
            "work_order_assignee_user_id": assignee_user_id,
            "edit_version_id": edit_version_id,
            "edit_version_status": "open",
            "edit_version_base_network_revision": 12,
            "aoi_id": aoi_id,
            "aoi_name": "Workspace WO-001",
            "aoi_description": None,
            "aoi_geometry_data": {"type": "Polygon", "coordinates": []},
            "aoi_extent": [65.495, 44.795, 65.545, 44.835],
            "features_data": [
                {
                    "id": str(feature_id),
                    "asset_code": "J-001",
                    "feature_type": "junction",
                    "geometry_data": {"type": "Point", "coordinates": [65.5, 44.82]},
                    "properties": {"name": "Junction"},
                    "network_version": 1,
                    "operation": "unchanged",
                }
            ],
            "associations_data": [
                {
                    "id": str(association_id),
                    "from_feature_id": str(feature_id),
                    "to_feature_id": str(connected_feature_id),
                    "association_type": "connectivity",
                    "version": 1,
                }
            ],
        }
    )
    repository = WorkOrderRepository(session)

    aggregate = asyncio.run(
        repository.get_workspace_aggregate(
            work_order_id=work_order_id,
            edit_version_id=edit_version_id,
        )
    )

    assert aggregate is not None
    assert len(session.execute_calls) == 1
    assert session.execute_calls[0] == (
        WORKSPACE_AGGREGATE_SQL,
        {
            "work_order_id": work_order_id,
            "edit_version_id": edit_version_id,
        },
    )
    assert session.scalars_calls == []
    assert aggregate.work_order.id == work_order_id
    assert aggregate.work_order.code == "WO-001"
    assert aggregate.work_order.status is WorkOrderStatus.IN_PROGRESS
    assert aggregate.work_order.assignee_user_id == assignee_user_id
    assert aggregate.edit_version.id == edit_version_id
    assert aggregate.edit_version.status is EditVersionStatus.OPEN
    assert aggregate.edit_version.base_network_revision == 12
    assert aggregate.aoi.id == aoi_id
    assert aggregate.aoi.extent == [65.495, 44.795, 65.545, 44.835]
    assert aggregate.features_data[0]["asset_code"] == "J-001"
    assert aggregate.associations_data[0]["id"] == str(association_id)


def test_get_workspace_aggregate_returns_none_when_sql_finds_no_context() -> None:
    repository = WorkOrderRepository(FakeSession(None))

    aggregate = asyncio.run(
        repository.get_workspace_aggregate(
            work_order_id=uuid4(),
            edit_version_id=uuid4(),
        )
    )

    assert aggregate is None
