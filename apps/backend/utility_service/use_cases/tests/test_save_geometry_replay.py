import asyncio
from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
from uuid import uuid4

import pytest

from utility_service.infrastructure.postgresql.models.work_order import EditVersionCommandState
from utility_service.infrastructure.postgresql.repository_rows.edit_geometry import (
    RepositoryProtocolError,
    RepositoryRejection,
)
from utility_service.use_cases.domain.exceptions.work_order_api_error import WorkOrderApiError
from utility_service.use_cases.tests.save_geometry_service_support import (
    SaveFixture,
    BASELINE,
    MOVED,
)


def test_replay_a_after_b_preserves_current_and_saved_payload():
    async def scenario():
        fixture = SaveFixture()
        request = fixture.request()
        result = await fixture.save(request)
        original = deepcopy(result.payload)
        await fixture.save(fixture.request(BASELINE))
        validations = fixture.validations
        result.payload["updatedFeature"]["geometry"]["coordinates"][1][0] = 0
        replay = await fixture.save(request)
        assert replay.payload == original
        assert fixture.context.root.draft_revision == 3
        assert fixture.context.current.operation == "unchanged"
        assert fixture.validations == validations
        assert fixture.mutations == 2
        equivalent = replace(
            request,
            geometry=replace(
                MOVED,
                coordinates=(
                    MOVED.coordinates[0],
                    (Decimal("65.52500001"), Decimal("44.82150001")),
                    MOVED.coordinates[2],
                ),
            ),
        )
        assert (await fixture.save(equivalent)).payload == original

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "field",
    ["fingerprint", "actor", "target"],
)
def test_reused_identity_never_changes_original_command(field):
    async def scenario():
        fixture = SaveFixture()
        request = fixture.request()
        await fixture.save(request)
        if field == "fingerprint":
            request = replace(
                request,
                draft_version_token="2",
            )
        else:
            row = fixture.commands[request.command_id]
            name = "actor_user_id" if field == "actor" else "edit_version_id"
            fixture.commands[request.command_id] = replace(
                row,
                **{
                    name: uuid4(),
                },
            )
        original = deepcopy(fixture.commands)
        with pytest.raises(WorkOrderApiError) as error:
            await fixture.save(request)
        assert error.value.code == "COMMAND_ID_REUSED"
        assert fixture.commands == original
        assert fixture.mutations == 1

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "condition,code",
    [
        ("role", "ROLE_NOT_ALLOWED"),
        ("access", "EDIT_VERSION_NOT_FOUND"),
        ("closed", "SAVE_CONTEXT_CLOSED"),
    ],
)
def test_current_access_and_lifecycle_precede_replay(
    condition,
    code,
):
    async def scenario():
        fixture = SaveFixture()
        request = fixture.request()
        await fixture.save(request)
        if condition == "role":
            fixture.actor.is_active = False
        elif condition == "access":
            fixture.context = replace(
                fixture.context,
                assignee_user_id=uuid4(),
            )

            # Сохранить caller как исходного Editor, меняя только assignment.
            async def get_actor(actor_id):
                return fixture.actor

            fixture.get_by_id = get_actor
        else:
            fixture.context = replace(
                fixture.context,
                work_order_status="assigned",
            )
        with pytest.raises(WorkOrderApiError) as error:
            await fixture.service.save_geometry(
                work_order_id=fixture.context.root.work_order_id,
                edit_version_id=fixture.context.root.id,
                feature_id=fixture.context.current.feature_id,
                actor_id=fixture.actor.id,
                request=request,
            )
        assert error.value.code == code
        assert fixture.mutations == 1

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "history",
    [False, True],
)
def test_disappeared_reservation_winner_never_mutates(history):
    async def scenario():
        fixture = SaveFixture()
        request = fixture.request()

        async def lose_reservation(
            *args,
            **kwargs,
        ):
            if history:
                fixture.history.add(request.command_id)
            return False

        fixture.reserve_command = lose_reservation
        with pytest.raises(WorkOrderApiError if history else RepositoryProtocolError) as error:
            await fixture.save(request)
        if history:
            assert error.value.code == "COMMAND_ID_REUSED"
        assert fixture.mutations == 0

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "code,status",
    [
        ("MULTIPLE_FEATURE_CHANGE_NOT_ALLOWED", 409),
        ("FEATURE_NOT_EDITABLE", 422),
        ("WORK_ORDER_CONTEXT_INVALID", 422),
        ("GEOMETRY_STRUCTURE_CHANGED", 422),
        ("GEOMETRY_INVALID", 422),
        ("GEOMETRY_OUTSIDE_AOI", 422),
    ],
)
def test_domain_rejection_rolls_back_new_registry(
    code,
    status,
):
    async def scenario():
        fixture = SaveFixture()

        async def reject(*args):
            return RepositoryRejection(
                code,
                "Отклонено.",
            )

        fixture.validate_candidate = reject
        with pytest.raises(WorkOrderApiError) as error:
            await fixture.save(fixture.request())
        assert (error.value.code, error.value.status_code) == (code, status)
        assert fixture.commands == {}
        assert fixture.mutations == 0

    asyncio.run(scenario())


def test_existing_access_rejection_is_not_resumed():
    async def scenario():
        fixture = SaveFixture()
        request = fixture.request()
        await fixture.save(request)
        fixture.commands[request.command_id] = replace(
            fixture.commands[request.command_id],
            state=EditVersionCommandState.REJECTED,
            response_payload=None,
            response_status=404,
            rejection_code="EDIT_VERSION_NOT_FOUND",
            rejection_message="Исходный отказ.",
            retry_on_access_change=True,
        )
        with pytest.raises(WorkOrderApiError) as error:
            await fixture.save(request)
        assert error.value.message == "Исходный отказ."
        assert fixture.mutations == 1

    asyncio.run(scenario())
