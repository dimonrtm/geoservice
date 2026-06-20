import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from utility_service.infrastructure.postgresql.models.utility_network import (
    AssociationType,
    DefaultStateStatus,
    FeatureType,
)
from utility_service.infrastructure.postgresql.repositories.default_state_repository import (
    DEFAULT_STATE_AGGREGATE_SQL,
    DEFAULT_STATE_AGGREGATE_SQL_PATH,
    DefaultStateRepository,
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
        raise AssertionError("Aggregate read must use one execute call")


def test_default_state_aggregate_sql_lives_in_sql_file() -> None:
    assert DEFAULT_STATE_AGGREGATE_SQL_PATH.name == "default_state_aggregate.sql"
    sql_text = DEFAULT_STATE_AGGREGATE_SQL_PATH.read_text(encoding="utf-8")
    assert "jsonb_agg" in sql_text
    assert "utility_network.default_state_features" in sql_text


def test_get_active_aggregate_by_work_order_id_uses_one_sql_round_trip() -> None:
    default_state_id = uuid4()
    work_order_id = uuid4()
    network_state_id = uuid4()
    feature_id = uuid4()
    association_id = uuid4()
    target_feature_id = uuid4()
    now = datetime(2026, 6, 20, 12, 0, tzinfo=timezone.utc)
    session = FakeSession(
        {
            "id": default_state_id,
            "work_order_id": work_order_id,
            "network_state_id": network_state_id,
            "base_network_revision": 7,
            "status": "active",
            "created_at": now,
            "updated_at": now,
            "features": [
                {
                    "default_state_id": str(default_state_id),
                    "feature_id": str(feature_id),
                    "asset_code": "J-001",
                    "feature_type": "junction",
                    "geometry_ewkt": "SRID=4326;POINT(1 2)",
                    "properties": {"phase": "A"},
                    "network_version": 3,
                }
            ],
            "associations": [
                {
                    "default_state_id": str(default_state_id),
                    "association_id": str(association_id),
                    "association_type": "connectivity",
                    "from_feature_id": str(feature_id),
                    "to_feature_id": str(target_feature_id),
                    "properties": {"kind": "edge"},
                    "network_version": 4,
                }
            ],
        }
    )
    repository = DefaultStateRepository(session)

    aggregate = asyncio.run(repository.get_active_aggregate_by_work_order_id(work_order_id))

    assert aggregate is not None
    assert len(session.execute_calls) == 1
    assert session.execute_calls[0] == (
        DEFAULT_STATE_AGGREGATE_SQL,
        {
            "work_order_id": work_order_id,
            "active_status": DefaultStateStatus.ACTIVE.value,
        },
    )
    assert session.scalars_calls == []
    assert aggregate.state.id == default_state_id
    assert aggregate.state.base_network_revision == 7
    assert aggregate.state.status is DefaultStateStatus.ACTIVE
    assert aggregate.features[0].feature_id == feature_id
    assert aggregate.features[0].feature_type is FeatureType.JUNCTION
    assert str(aggregate.features[0].geometry) == "SRID=4326;POINT(1 2)"
    assert aggregate.features[0].properties == {"phase": "A"}
    assert aggregate.associations[0].association_id == association_id
    assert aggregate.associations[0].association_type is AssociationType.CONNECTIVITY
    assert aggregate.associations[0].to_feature_id == target_feature_id
