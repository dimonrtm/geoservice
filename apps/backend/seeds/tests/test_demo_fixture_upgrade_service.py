import asyncio
from dataclasses import fields, replace
import logging
from uuid import UUID

import pytest

from seeds.contracts.demo_fixture_upgrade import (
    DemoFixtureCopySource,
    DemoFixtureEditVersionSnapshot,
    DemoFixtureFeatureSnapshot,
    DemoFixtureGeometryUpdate,
    DemoFixtureHierarchy,
    DemoFixtureUpgradeError,
    DemoFixtureUpgradeResult,
)
from seeds.services.demo_fixture_upgrade_service import DemoFixtureUpgradeService
from seeds.services import demo_fixture_upgrade_service as upgrade_service_module
from seeds.specs.seed_utility_dataset_specs import UTILITY_EDITABLE_LINE_SPEC
from utility_service.infrastructure.postgresql.models.work_order.edit_version_feature import (
    EditVersionOperationState,
)


FEEDER_ID = UUID("10000000-0000-0000-0000-000000000001")
WORK_ORDER_ID = UUID("10000000-0000-0000-0000-000000000002")
DEFAULT_STATE_ID = UUID("10000000-0000-0000-0000-000000000003")
EDIT_VERSION_ID = UUID("10000000-0000-0000-0000-000000000004")
SECOND_EDIT_VERSION_ID = UUID("10000000-0000-0000-0000-000000000005")

OLD_TWO_VERTEX_WKT = "LINESTRING (65.520 44.820, 65.530 44.820)"
FEEDER_THREE_VERTEX_WKT = "LINESTRING (65.520 44.820, 65.524 44.821, 65.530 44.820)"
DEFAULT_THREE_VERTEX_WKT = "LINESTRING (65.520 44.820, 65.526 44.821, 65.530 44.820)"
EDIT_THREE_VERTEX_WKT = "LINESTRING (65.520 44.820, 65.527 44.821, 65.530 44.820)"


class FakeTransaction:
    def __init__(self, session: "FakeSession") -> None:
        self._session = session

    async def __aenter__(self) -> None:
        self._session.transaction_started = True
        return None

    async def __aexit__(self, exc_type, exc_value, traceback) -> bool:
        if exc_type is None:
            self._session.transaction_committed = True
        else:
            self._session.transaction_rolled_back = True
        return False


def test_edit_version_snapshot_records_default_state_lineage() -> None:
    field_names = {item.name for item in fields(DemoFixtureEditVersionSnapshot)}

    assert "default_state_id" in field_names


class FakeSession:
    def __init__(self) -> None:
        self.transaction_started = False
        self.transaction_committed = False
        self.transaction_rolled_back = False

    def begin(self) -> FakeTransaction:
        return FakeTransaction(self)


class RunnerSession(FakeSession):
    async def __aenter__(self) -> "RunnerSession":
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> bool:
        return False


class FakeRepository:
    def __init__(
        self,
        hierarchy: DemoFixtureHierarchy,
        *,
        fail_on_update_number: int | None = None,
    ) -> None:
        self.hierarchy = hierarchy
        self.fail_on_update_number = fail_on_update_number
        self.updates: list[DemoFixtureGeometryUpdate] = []
        self.update_attempts = 0

    async def load_hierarchy_for_update(self) -> DemoFixtureHierarchy:
        return self.hierarchy

    async def update_geometry(self, update: DemoFixtureGeometryUpdate) -> None:
        self.update_attempts += 1
        if self.update_attempts == self.fail_on_update_number:
            raise RuntimeError("synthetic write failure")
        self.updates.append(update)


def feature(
    owner_id: UUID,
    geometry_wkt: str,
    vertex_count: int,
    *,
    operation: EditVersionOperationState | None = None,
) -> DemoFixtureFeatureSnapshot:
    return DemoFixtureFeatureSnapshot(
        owner_id=owner_id,
        geometry_wkt=geometry_wkt,
        geometry_type="LINESTRING",
        vertex_count=vertex_count,
        network_version=1,
        operation=operation,
    )


def edit(
    geometry_wkt: str,
    vertex_count: int,
    *,
    edit_version_id: UUID = EDIT_VERSION_ID,
    operation: EditVersionOperationState = EditVersionOperationState.UNCHANGED,
) -> DemoFixtureEditVersionSnapshot:
    return DemoFixtureEditVersionSnapshot(
        edit_version_id=edit_version_id,
        default_state_id=DEFAULT_STATE_ID,
        feature=feature(
            edit_version_id,
            geometry_wkt,
            vertex_count,
            operation=operation,
        ),
    )


def hierarchy(
    feeder_feature: DemoFixtureFeatureSnapshot,
    default_feature: DemoFixtureFeatureSnapshot,
    *,
    edits: tuple[DemoFixtureEditVersionSnapshot, ...] = (),
) -> DemoFixtureHierarchy:
    return DemoFixtureHierarchy(
        feeder_id=FEEDER_ID,
        feeder_feature=feeder_feature,
        work_order_id=WORK_ORDER_ID,
        default_state_id=DEFAULT_STATE_ID,
        default_feature=default_feature,
        edit_versions=edits,
    )


def valid_three_vertex_hierarchy() -> DemoFixtureHierarchy:
    return hierarchy(
        feature(FEEDER_ID, FEEDER_THREE_VERTEX_WKT, 3),
        feature(DEFAULT_STATE_ID, DEFAULT_THREE_VERTEX_WKT, 3),
        edits=(edit(EDIT_THREE_VERTEX_WKT, 3),),
    )


async def _run_upgrade(
    hierarchy_snapshot: DemoFixtureHierarchy,
) -> tuple[FakeRepository, tuple[DemoFixtureGeometryUpdate, ...]]:
    repository = FakeRepository(hierarchy_snapshot)
    result = await DemoFixtureUpgradeService(
        FakeSession(),
        repository,
    ).upgrade_demo_fixture()
    return repository, result.updates


def run_upgrade(
    hierarchy_snapshot: DemoFixtureHierarchy,
) -> tuple[FakeRepository, tuple[DemoFixtureGeometryUpdate, ...]]:
    return asyncio.run(_run_upgrade(hierarchy_snapshot))


def execute_service(
    repository: FakeRepository,
    session: FakeSession | None = None,
) -> DemoFixtureUpgradeResult:
    actual_session = session or FakeSession()
    return asyncio.run(
        DemoFixtureUpgradeService(
            actual_session,
            repository,
        ).upgrade_demo_fixture()
    )


def test_upgrades_all_two_vertex_copies_from_seed_lineage() -> None:
    repository, updates = run_upgrade(
        hierarchy(
            feature(FEEDER_ID, OLD_TWO_VERTEX_WKT, 2),
            feature(DEFAULT_STATE_ID, OLD_TWO_VERTEX_WKT, 2),
            edits=(edit(OLD_TWO_VERTEX_WKT, 2),),
        )
    )

    expected = (
        DemoFixtureGeometryUpdate(
            source=DemoFixtureCopySource.FEEDER,
            owner_id=FEEDER_ID,
            geometry_wkt=UTILITY_EDITABLE_LINE_SPEC.geometry_wkt,
        ),
        DemoFixtureGeometryUpdate(
            source=DemoFixtureCopySource.DEFAULT_STATE,
            owner_id=DEFAULT_STATE_ID,
            geometry_wkt=UTILITY_EDITABLE_LINE_SPEC.geometry_wkt,
        ),
        DemoFixtureGeometryUpdate(
            source=DemoFixtureCopySource.EDIT_VERSION,
            owner_id=EDIT_VERSION_ID,
            geometry_wkt=UTILITY_EDITABLE_LINE_SPEC.geometry_wkt,
        ),
    )
    assert updates == expected
    assert tuple(repository.updates) == expected


def test_mixed_3_2_2_propagates_feeder_geometry_downstream() -> None:
    _, updates = run_upgrade(
        hierarchy(
            feature(FEEDER_ID, FEEDER_THREE_VERTEX_WKT, 3),
            feature(DEFAULT_STATE_ID, OLD_TWO_VERTEX_WKT, 2),
            edits=(edit(OLD_TWO_VERTEX_WKT, 2),),
        )
    )

    assert updates == (
        DemoFixtureGeometryUpdate(
            source=DemoFixtureCopySource.DEFAULT_STATE,
            owner_id=DEFAULT_STATE_ID,
            geometry_wkt=FEEDER_THREE_VERTEX_WKT,
        ),
        DemoFixtureGeometryUpdate(
            source=DemoFixtureCopySource.EDIT_VERSION,
            owner_id=EDIT_VERSION_ID,
            geometry_wkt=FEEDER_THREE_VERTEX_WKT,
        ),
    )


def test_mixed_2_3_2_preserves_default_and_propagates_it_to_edit() -> None:
    _, updates = run_upgrade(
        hierarchy(
            feature(FEEDER_ID, OLD_TWO_VERTEX_WKT, 2),
            feature(DEFAULT_STATE_ID, DEFAULT_THREE_VERTEX_WKT, 3),
            edits=(edit(OLD_TWO_VERTEX_WKT, 2),),
        )
    )

    assert updates == (
        DemoFixtureGeometryUpdate(
            source=DemoFixtureCopySource.FEEDER,
            owner_id=FEEDER_ID,
            geometry_wkt=UTILITY_EDITABLE_LINE_SPEC.geometry_wkt,
        ),
        DemoFixtureGeometryUpdate(
            source=DemoFixtureCopySource.EDIT_VERSION,
            owner_id=EDIT_VERSION_ID,
            geometry_wkt=DEFAULT_THREE_VERTEX_WKT,
        ),
    )


def test_three_vertex_default_is_parent_for_two_vertex_edit() -> None:
    _, updates = run_upgrade(
        hierarchy(
            feature(FEEDER_ID, FEEDER_THREE_VERTEX_WKT, 3),
            feature(DEFAULT_STATE_ID, DEFAULT_THREE_VERTEX_WKT, 3),
            edits=(edit(OLD_TWO_VERTEX_WKT, 2),),
        )
    )

    assert updates == (
        DemoFixtureGeometryUpdate(
            source=DemoFixtureCopySource.EDIT_VERSION,
            owner_id=EDIT_VERSION_ID,
            geometry_wkt=DEFAULT_THREE_VERTEX_WKT,
        ),
    )


def test_preserves_distinct_three_vertex_copies_even_for_updated_edit() -> None:
    repository, updates = run_upgrade(
        hierarchy(
            feature(FEEDER_ID, FEEDER_THREE_VERTEX_WKT, 3),
            feature(DEFAULT_STATE_ID, DEFAULT_THREE_VERTEX_WKT, 3),
            edits=(
                edit(
                    EDIT_THREE_VERTEX_WKT,
                    3,
                    operation=EditVersionOperationState.UPDATED,
                ),
            ),
        )
    )

    assert updates == ()
    assert repository.updates == []


def test_fresh_hierarchy_without_edit_versions_is_valid_no_op() -> None:
    repository, updates = run_upgrade(
        hierarchy(
            feature(FEEDER_ID, UTILITY_EDITABLE_LINE_SPEC.geometry_wkt, 3),
            feature(DEFAULT_STATE_ID, UTILITY_EDITABLE_LINE_SPEC.geometry_wkt, 3),
        )
    )

    assert updates == ()
    assert repository.updates == []


@pytest.mark.parametrize(
    "missing_field",
    ["feeder_id", "feeder_feature", "work_order_id", "default_state_id", "default_feature"],
)
def test_rejects_missing_required_hierarchy_before_writes(missing_field: str) -> None:
    snapshot = replace(valid_three_vertex_hierarchy(), **{missing_field: None})
    repository = FakeRepository(snapshot)

    with pytest.raises(DemoFixtureUpgradeError, match="L-003"):
        execute_service(repository)

    assert repository.updates == []


def test_rejects_missing_copy_for_existing_edit_version_before_writes() -> None:
    snapshot = valid_three_vertex_hierarchy()
    missing_copy = replace(snapshot.edit_versions[0], feature=None)
    repository = FakeRepository(replace(snapshot, edit_versions=(missing_copy,)))

    with pytest.raises(DemoFixtureUpgradeError, match="L-003"):
        execute_service(repository)

    assert repository.updates == []


def test_rejects_edit_version_from_different_default_state_before_writes() -> None:
    snapshot = valid_three_vertex_hierarchy()
    wrong_lineage = replace(
        snapshot.edit_versions[0],
        default_state_id=UUID("20000000-0000-0000-0000-000000000001"),
    )
    repository = FakeRepository(replace(snapshot, edit_versions=(wrong_lineage,)))

    with pytest.raises(DemoFixtureUpgradeError, match="default_state_id"):
        execute_service(repository)

    assert repository.updates == []


@pytest.mark.parametrize("source", list(DemoFixtureCopySource))
def test_rejects_wrong_geometry_type_for_every_copy_source(
    source: DemoFixtureCopySource,
) -> None:
    snapshot = valid_three_vertex_hierarchy()
    if source is DemoFixtureCopySource.FEEDER:
        snapshot = replace(
            snapshot,
            feeder_feature=replace(snapshot.feeder_feature, geometry_type="POINT"),
        )
    elif source is DemoFixtureCopySource.DEFAULT_STATE:
        snapshot = replace(
            snapshot,
            default_feature=replace(snapshot.default_feature, geometry_type="MULTILINESTRING"),
        )
    else:
        changed_edit = replace(
            snapshot.edit_versions[0],
            feature=replace(snapshot.edit_versions[0].feature, geometry_type="POINT"),
        )
        snapshot = replace(snapshot, edit_versions=(changed_edit,))
    repository = FakeRepository(snapshot)

    with pytest.raises(DemoFixtureUpgradeError, match="L-003"):
        execute_service(repository)

    assert repository.updates == []


@pytest.mark.parametrize("vertex_count", [0, 1, 4, 5])
@pytest.mark.parametrize("source", list(DemoFixtureCopySource))
def test_rejects_unsupported_vertex_count_for_every_copy_source(
    source: DemoFixtureCopySource,
    vertex_count: int,
) -> None:
    snapshot = valid_three_vertex_hierarchy()
    if source is DemoFixtureCopySource.FEEDER:
        snapshot = replace(
            snapshot,
            feeder_feature=replace(snapshot.feeder_feature, vertex_count=vertex_count),
        )
    elif source is DemoFixtureCopySource.DEFAULT_STATE:
        snapshot = replace(
            snapshot,
            default_feature=replace(snapshot.default_feature, vertex_count=vertex_count),
        )
    else:
        changed_edit = replace(
            snapshot.edit_versions[0],
            feature=replace(snapshot.edit_versions[0].feature, vertex_count=vertex_count),
        )
        snapshot = replace(snapshot, edit_versions=(changed_edit,))
    repository = FakeRepository(snapshot)

    with pytest.raises(DemoFixtureUpgradeError, match="L-003"):
        execute_service(repository)

    assert repository.updates == []


@pytest.mark.parametrize(
    "operation",
    [
        EditVersionOperationState.CREATED,
        EditVersionOperationState.UPDATED,
        EditVersionOperationState.DELETED,
    ],
)
def test_rejects_changed_two_vertex_edit_before_any_write(
    operation: EditVersionOperationState,
) -> None:
    repository = FakeRepository(
        hierarchy(
            feature(FEEDER_ID, OLD_TWO_VERTEX_WKT, 2),
            feature(DEFAULT_STATE_ID, OLD_TWO_VERTEX_WKT, 2),
            edits=(edit(OLD_TWO_VERTEX_WKT, 2, operation=operation),),
        )
    )

    with pytest.raises(DemoFixtureUpgradeError, match="operation"):
        execute_service(repository)

    assert repository.updates == []


def test_error_identifies_asset_source_and_owner() -> None:
    invalid_feeder = replace(
        feature(FEEDER_ID, FEEDER_THREE_VERTEX_WKT, 3),
        geometry_type="POINT",
    )
    repository = FakeRepository(
        hierarchy(
            invalid_feeder,
            feature(DEFAULT_STATE_ID, DEFAULT_THREE_VERTEX_WKT, 3),
        )
    )

    with pytest.raises(
        DemoFixtureUpgradeError,
        match=rf"L-003.*feeder.*{FEEDER_ID}",
    ):
        execute_service(repository)


def test_orders_edit_updates_by_edit_version_id() -> None:
    repository = FakeRepository(
        hierarchy(
            feature(FEEDER_ID, FEEDER_THREE_VERTEX_WKT, 3),
            feature(DEFAULT_STATE_ID, DEFAULT_THREE_VERTEX_WKT, 3),
            edits=(
                edit(
                    OLD_TWO_VERTEX_WKT,
                    2,
                    edit_version_id=SECOND_EDIT_VERSION_ID,
                ),
                edit(OLD_TWO_VERTEX_WKT, 2, edit_version_id=EDIT_VERSION_ID),
            ),
        )
    )

    result = execute_service(repository)

    assert [update.owner_id for update in result.updates] == [
        EDIT_VERSION_ID,
        SECOND_EDIT_VERSION_ID,
    ]


def test_rolls_back_transaction_when_repository_write_fails() -> None:
    session = FakeSession()
    repository = FakeRepository(
        hierarchy(
            feature(FEEDER_ID, OLD_TWO_VERTEX_WKT, 2),
            feature(DEFAULT_STATE_ID, OLD_TWO_VERTEX_WKT, 2),
            edits=(edit(OLD_TWO_VERTEX_WKT, 2),),
        ),
        fail_on_update_number=2,
    )

    with pytest.raises(RuntimeError, match="synthetic write failure"):
        execute_service(repository, session)

    assert session.transaction_started is True
    assert session.transaction_committed is False
    assert session.transaction_rolled_back is True
    assert len(repository.updates) == 1


def test_application_runner_returns_result_and_logs_updated_sources(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    repository = FakeRepository(valid_three_vertex_hierarchy())
    runner_session = RunnerSession()

    monkeypatch.setattr(
        "utility_service.infrastructure.postgresql.session.SessionFactory",
        lambda: runner_session,
    )
    monkeypatch.setattr(
        "seeds.repositories.demo_fixture_upgrade_repository.DemoFixtureUpgradeRepository",
        lambda session: repository,
    )
    caplog.set_level(logging.INFO)

    result = asyncio.run(upgrade_service_module.run_upgrade_demo_fixture())

    assert result.updated_copy_count == 0
    record = next(
        item for item in caplog.records if item.message == "Demo fixture upgrade завершён."
    )
    assert record.updated_copy_count == 0
    assert record.updated_sources == []
