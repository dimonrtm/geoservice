import asyncio
from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
from uuid import uuid4

import pytest

from utility_service.use_cases.domain.exceptions.work_order_api_error import WorkOrderApiError
from utility_service.use_cases.tests.save_geometry_service_support import SaveFixture, MOVED
from utility_service.infrastructure.postgresql.repository_rows.edit_geometry import (
    RepositoryProtocolError,
    RepositoryRejection,
)


def test_rejection_commits_before_api_exception_and_replays():
    async def scenario():
        fixture = SaveFixture()
        request = fixture.request(token="old")
        for _ in range(2):
            with pytest.raises(WorkOrderApiError) as error:
                await fixture.save(request)
            assert error.value.code == "DRAFT_VERSION_STALE"
            assert fixture.commands[request.command_id].state == "rejected"
            assert not fixture.active
        assert fixture.commits == 2
        assert fixture.mutations == 0
        assert fixture.validations == 0

    asyncio.run(scenario())


def test_rejection_commit_failure_is_not_domain_result():
    async def scenario():
        fixture = SaveFixture()
        fixture.fail_commit = True
        with pytest.raises(
            RuntimeError,
            match="commit failed",
        ):
            await fixture.save(fixture.request(token="old"))
        assert fixture.commands == {}

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "damage",
    ["missing", "unreadable", "wrong_type"],
)
def test_repaired_baseline_keeps_contextless_rejection(damage):
    async def scenario():
        fixture = SaveFixture()
        valid_context = fixture.context
        from utility_service.infrastructure.postgresql.geometry_codec import encode_geometry
        from utility_service.domain_services.edit_geometry.types import GeometryValue

        baseline = (
            None
            if damage == "missing"
            else replace(
                valid_context.baseline,
                geometry_ewkb=(
                    b"broken"
                    if damage == "unreadable"
                    else encode_geometry(
                        GeometryValue(
                            "Point",
                            ((Decimal("65.52"), Decimal("44.82")),),
                        )
                    )
                ),
            )
        )
        fixture.context = replace(
            valid_context,
            baseline=baseline,
        )
        request = fixture.request()
        with pytest.raises(WorkOrderApiError) as first:
            await fixture.save(request)
        assert first.value.code == "WORK_ORDER_CONTEXT_INVALID"
        row = deepcopy(fixture.commands[request.command_id])
        assert row.request_fingerprint.startswith("geom-contextless-v1:sha256:")
        fixture.context = valid_context
        equivalent = replace(
            request,
            geometry=replace(
                MOVED,
                coordinates=(
                    MOVED.coordinates[0],
                    (Decimal("65.52500001"), Decimal("44.8215")),
                    MOVED.coordinates[2],
                ),
            ),
        )
        for retry in (request, equivalent):
            with pytest.raises(WorkOrderApiError) as replay:
                await fixture.save(retry)
            assert (replay.value.code, replay.value.message) == (
                first.value.code,
                first.value.message,
            )
            assert fixture.commands[request.command_id] == row
        with pytest.raises(WorkOrderApiError) as reuse:
            await fixture.save(
                replace(
                    request,
                    draft_version_token="2",
                )
            )
        assert reuse.value.code == "COMMAND_ID_REUSED"
        assert fixture.mutations == 0

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "broken_baseline",
    [False, True],
)
@pytest.mark.parametrize(
    "stale",
    [False, True],
)
def test_access_recovery_keeps_identity_and_revalidates(
    broken_baseline,
    stale,
):
    async def scenario():
        fixture = SaveFixture()
        context = fixture.context
        request = fixture.request(token="old" if stale else "1")
        fixture.context = replace(
            context,
            assignee_user_id=uuid4(),
            baseline=None if broken_baseline else context.baseline,
        )

        async def invoke(value):
            return await fixture.service.save_geometry(
                work_order_id=context.root.work_order_id,
                edit_version_id=context.root.id,
                feature_id=context.current.feature_id,
                actor_id=fixture.actor.id,
                request=value,
            )

        with pytest.raises(WorkOrderApiError) as denied:
            await invoke(request)
        assert denied.value.code == "EDIT_VERSION_NOT_FOUND"
        original = deepcopy(fixture.commands[request.command_id])
        assert original.retry_on_access_change
        with pytest.raises(WorkOrderApiError):
            await invoke(request)
        assert fixture.commands[request.command_id] == original
        fixture.context = context
        if stale:
            with pytest.raises(WorkOrderApiError) as outcome:
                await invoke(request)
            assert outcome.value.code == "DRAFT_VERSION_STALE"
        else:
            assert (await invoke(request)).status_code == 200
            assert fixture.validations == 1
        final = fixture.commands[request.command_id]
        assert final.request_fingerprint == original.request_fingerprint
        assert not final.retry_on_access_change

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "prefix",
    ["unknown:sha256:", "geom-v1:sha256:"],
)
def test_stored_identity_never_falls_back_when_baseline_breaks(prefix):
    async def scenario():
        fixture = SaveFixture()
        value = fixture.request()
        await fixture.save(value)
        if prefix.startswith("unknown"):
            fixture.commands[value.command_id] = replace(
                fixture.commands[value.command_id],
                request_fingerprint=prefix + "abc",
            )
        original = deepcopy(fixture.commands)
        fixture.context = replace(
            fixture.context,
            baseline=None,
        )
        with pytest.raises(
            RepositoryProtocolError if prefix.startswith("unknown") else WorkOrderApiError
        ):
            await fixture.save(value)
        assert fixture.commands == original
        assert fixture.mutations == 1

    asyncio.run(scenario())


def test_new_stale_precedes_candidate_validation_but_not_missing_baseline():
    async def scenario():
        fixture = SaveFixture()

        async def invalid(*args):
            raise AssertionError("Stale must not spatially validate candidate")

        fixture.validate_candidate = invalid
        with pytest.raises(WorkOrderApiError) as stale:
            await fixture.save(fixture.request(token="old"))
        assert stale.value.code == "DRAFT_VERSION_STALE"
        fixture.context = replace(
            fixture.context,
            baseline=None,
        )
        with pytest.raises(WorkOrderApiError) as context:
            await fixture.save(fixture.request(token="old"))
        assert context.value.code == "WORK_ORDER_CONTEXT_INVALID"

    asyncio.run(scenario())


def test_ordinary_rejection_survives_repaired_current_context():
    async def scenario():
        fixture = SaveFixture()
        original_validate = fixture.validate_candidate

        async def invalid(*args):
            return RepositoryRejection(
                "WORK_ORDER_CONTEXT_INVALID",
                "Исходный контекст повреждён.",
            )

        fixture.validate_candidate = invalid
        value = fixture.request()
        with pytest.raises(WorkOrderApiError) as first:
            await fixture.save(value)
        fixture.validate_candidate = original_validate
        with pytest.raises(WorkOrderApiError) as replay:
            await fixture.save(value)
        assert (replay.value.code, replay.value.message) == (first.value.code, first.value.message)
        assert fixture.mutations == 0

    asyncio.run(scenario())
