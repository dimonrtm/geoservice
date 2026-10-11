import asyncio

import pytest

from utility_service.use_cases.tests.save_geometry_service_support import SaveFixture, BASELINE
from utility_service.use_cases.domain.exceptions.work_order_api_error import WorkOrderApiError
from utility_service.infrastructure.postgresql.repository_rows.edit_geometry import (
    RepositoryRejection,
)


def test_save_noop_and_revert_results():
    async def scenario():
        fixture = SaveFixture()
        baseline = await fixture.save(fixture.request(BASELINE))
        assert baseline.payload["basicValidation"] is None
        assert baseline.payload["draftVersionToken"] == "1"
        assert fixture.mutations == 0
        changed = await fixture.save(fixture.request())
        assert changed.status_code == 200
        assert changed.payload["draftVersionToken"] == "2"
        assert changed.payload["updatedFeature"]["geometry"]["coordinates"][1] == [65.525, 44.8215]
        assert changed.payload["operation"] == "updated"
        assert changed.payload["hasPersistedChangeSet"] is True
        assert changed.payload["basicValidation"] == {
            "geometryStatus": "passed",
            "aoiStatus": "passed",
            "positionalAccuracyStatus": "POSITIONAL_ACCURACY_UNVERIFIED",
            "dirtyRelativeToBaseline": "passed",
        }
        noop = await fixture.save(fixture.request())
        assert noop.payload["draftVersionToken"] == "2"
        assert noop.payload["basicValidation"] == changed.payload["basicValidation"]
        assert fixture.mutations == 1
        reverted = await fixture.save(fixture.request(BASELINE))
        assert reverted.payload["draftVersionToken"] == "3"
        assert reverted.payload["operation"] == "unchanged"
        assert reverted.payload["hasPersistedChangeSet"] is False
        assert reverted.payload["basicValidation"] is None
        assert fixture.mutations == 2
        assert fixture.commits == 4
        assert len(fixture.commands) == 4

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "token",
    ["01", "old", "2"],
)
def test_stale_rolls_back_reservation(token):
    async def scenario():
        fixture = SaveFixture()
        with pytest.raises(WorkOrderApiError) as error:
            await fixture.save(fixture.request(token=token))
        assert error.value.code == "DRAFT_VERSION_STALE"
        assert fixture.commands == {}
        assert fixture.mutations == 0
        assert fixture.validations == 0

    asyncio.run(scenario())


def test_commit_failure_does_not_return_success():
    async def scenario():
        fixture = SaveFixture()
        fixture.fail_commit = True
        with pytest.raises(
            RuntimeError,
            match="commit failed",
        ):
            await fixture.save(fixture.request())
        assert fixture.commands == {}
        assert fixture.context.root.draft_revision == 1
        assert fixture.mutations == 0

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "missing,code",
    [
        ("actor", "ROLE_NOT_ALLOWED"),
        ("root", "EDIT_VERSION_NOT_FOUND"),
        ("feature", "EDIT_VERSION_NOT_FOUND"),
        ("baseline", "WORK_ORDER_CONTEXT_INVALID"),
    ],
)
def test_missing_save_context_does_not_reserve_command(missing, code):
    async def scenario():
        fixture = SaveFixture()
        if missing == "actor":
            fixture.actor = None
        elif missing == "root":

            async def no_root(**kwargs):
                return None

            fixture.lock_version = no_root
        elif missing == "feature":

            async def no_feature(*args, **kwargs):
                return RepositoryRejection(code, "Объект отсутствует.")

            fixture.read_context = no_feature
        else:
            fixture.prepare_candidate = lambda *args: RepositoryRejection(
                code,
                "Базовое состояние отсутствует.",
            )
        with pytest.raises(WorkOrderApiError) as error:
            await fixture.save(fixture.request())
        assert error.value.code == code
        assert fixture.commands == {}
        assert fixture.mutations == 0

    asyncio.run(scenario())
