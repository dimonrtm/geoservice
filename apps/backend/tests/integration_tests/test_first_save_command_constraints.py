from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.integration_tests.first_save_schema_support import (
    finish_command,
    insert_running_command,
    run_scenario,
    seed_context,
    run_committed_scenario,
)


@pytest.mark.parametrize(
    "state,mutation",
    [
        ("succeeded", "completed_at=NULL"),
        ("succeeded", "response_payload='null'::jsonb"),
        ("succeeded", "response_payload='[]'::jsonb"),
        ("succeeded", "response_payload=NULL"),
        ("succeeded", "rejection_code='INVALID'"),
        ("succeeded", "response_status=NULL"),
        ("succeeded", "response_status=500"),
        ("succeeded", "retry_on_access_change=true"),
        ("rejected", "response_payload='{}'::jsonb"),
        ("rejected", "rejection_code=NULL"),
        ("rejected", "rejection_message='   '"),
        ("rejected", "completed_at=NULL"),
        ("rejected", "retry_on_access_change=true"),
        ("running", "response_status=200"),
        ("running", "retry_on_access_change=true"),
        ("running", "request_fingerprint=' '"),
        ("running", "state='unknown'"),
    ],
)
def test_command_result_shape_constraints(
    state,
    mutation,
) -> None:
    async def scenario(connection):
        ids = await seed_context(connection)
        command_id = uuid4()
        if state != "running":
            await insert_running_command(
                connection,
                ids,
                command_id,
            )
        # Finish and corrupt in one UPDATE so future final-state guards do not mask CHECKs.
        valid = {
            "running": {},
            "succeeded": {
                "state": "'succeeded'",
                "response_status": "200",
                "response_payload": '\'{"commandState":"succeeded"}\'::jsonb',
                "completed_at": "now()",
            },
            "rejected": {
                "state": "'rejected'",
                "response_status": "422",
                "rejection_code": "'GEOMETRY_INVALID'",
                "rejection_message": "'Invalid'",
                "completed_at": "now()",
            },
        }[state]
        field, value = mutation.split(
            "=",
            1,
        )
        valid[field] = value
        assignments = ",\n".join(f"{key}={value}" for key, value in valid.items())
        with pytest.raises(DBAPIError) as error:
            async with connection.begin_nested():
                if state == "running":
                    values = {
                        "command_id": ":id",
                        "edit_version_id": ":edit_version_id",
                        "feature_id": ":feature_id",
                        "actor_user_id": ":actor_user_id",
                        "request_fingerprint": "'fixture-fingerprint'",
                        "state": "'running'",
                        **valid,
                    }
                    columns = ",\n".join(values)
                    expressions = ",\n".join(values.values())
                    await connection.execute(
                        text(
                            "INSERT INTO work_order.edit_version_commands "
                            f"(\n{columns}\n) VALUES (\n{expressions}\n)"
                        ),
                        {
                            **ids,
                            "id": command_id,
                        },
                    )
                else:
                    await connection.execute(
                        text(
                            f"UPDATE work_order.edit_version_commands SET {assignments} WHERE command_id=:id"
                        ),
                        {
                            "id": command_id,
                        },
                    )
        assert error.value.orig.sqlstate == "23514"
        expected = "ck_ev_commands_result"
        if field == "request_fingerprint":
            expected = "ck_ev_commands_fingerprint"
        elif field == "retry_on_access_change":
            expected = "ck_ev_commands_access_retry"
        elif field == "state":
            expected = "ck_ev_commands_transition"
        assert error.value.orig.__cause__.constraint_name == expected

    run_scenario(scenario)


def test_command_feature_fk_is_version_scoped() -> None:
    async def scenario(connection):
        first = await seed_context(connection)
        second = await seed_context(connection)
        for feature_id in (second["feature_id"], uuid4()):
            with pytest.raises(DBAPIError) as error:
                async with connection.begin_nested():
                    await insert_running_command(
                        connection,
                        {
                            **first,
                            "feature_id": feature_id,
                        },
                        uuid4(),
                    )
            assert error.value.orig.sqlstate == "23503"
        command_id = uuid4()
        await insert_running_command(
            connection,
            first,
            command_id,
        )
        with pytest.raises(DBAPIError) as error:
            async with connection.begin_nested():
                await insert_running_command(
                    connection,
                    second,
                    command_id,
                )
        assert error.value.orig.sqlstate == "23505"

    run_scenario(scenario)


@pytest.mark.parametrize(
    "state,retry",
    [("succeeded", False), ("rejected", False), ("rejected", True)],
)
def test_command_valid_result_shape(
    state,
    retry,
) -> None:
    async def scenario(connection):
        ids = await seed_context(connection)
        command_id = uuid4()
        await insert_running_command(
            connection,
            ids,
            command_id,
        )
        await finish_command(
            connection,
            command_id,
            state=state,
            retry_on_access_change=retry,
        )
        row = (
            (
                await connection.execute(
                    text("SELECT * FROM work_order.edit_version_commands WHERE command_id=:id"),
                    {
                        "id": command_id,
                    },
                )
            )
            .mappings()
            .one()
        )
        assert row["state"] == state
        assert row["completed_at"] is not None
        assert row["retry_on_access_change"] is retry

    run_scenario(scenario)


@pytest.mark.parametrize(
    "state",
    ["succeeded", "rejected"],
)
def test_terminal_command_commits_after_running_insert(state) -> None:
    async def scenario(engine):
        command_id = uuid4()
        async with engine.begin() as connection:
            ids = await seed_context(connection)
            await insert_running_command(
                connection,
                ids,
                command_id,
            )
            await finish_command(
                connection,
                command_id,
                state=state,
            )
        async with engine.connect() as connection:
            assert (
                await connection.scalar(
                    text("SELECT state FROM work_order.edit_version_commands WHERE command_id=:id"),
                    {
                        "id": command_id,
                    },
                )
                == state
            )

    run_committed_scenario(scenario)


def test_running_command_cannot_commit() -> None:
    async def scenario(engine):
        command_id = uuid4()
        with pytest.raises(DBAPIError) as error:
            async with engine.begin() as connection:
                ids = await seed_context(connection)
                await insert_running_command(
                    connection,
                    ids,
                    command_id,
                )
        assert error.value.orig.sqlstate == "23514"
        async with engine.connect() as connection:
            assert (
                await connection.scalar(
                    text(
                        "SELECT count(*) FROM work_order.edit_version_commands WHERE command_id=:id"
                    ),
                    {
                        "id": command_id,
                    },
                )
                == 0
            )
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM work_order.edit_versions WHERE id=:id"),
                    {
                        "id": ids["edit_version_id"],
                    },
                )
                == 0
            )

    run_committed_scenario(scenario)


def test_successful_noop_without_event_can_commit() -> None:
    async def scenario(engine):
        command_id = uuid4()
        async with engine.begin() as connection:
            ids = await seed_context(connection)
            await insert_running_command(
                connection,
                ids,
                command_id,
            )
            await finish_command(
                connection,
                command_id,
                state="succeeded",
            )
        async with engine.connect() as connection:
            result = await connection.scalar(
                text(
                    "SELECT response_payload FROM work_order.edit_version_commands WHERE command_id=:id"
                ),
                {
                    "id": command_id,
                },
            )
            assert result["draftVersionToken"] == "1"
            assert result["operation"] == "unchanged"
            assert result["hasPersistedChangeSet"] is False
            assert (
                await connection.scalar(
                    text(
                        "SELECT count(*) FROM work_order.edit_version_change_events WHERE command_id=:id"
                    ),
                    {
                        "id": command_id,
                    },
                )
                == 0
            )

    run_committed_scenario(scenario)


@pytest.mark.parametrize(
    "field",
    [
        "command_id",
        "edit_version_id",
        "feature_id",
        "actor_user_id",
        "request_fingerprint",
        "created_at",
    ],
)
def test_command_identity_is_immutable(field) -> None:
    async def scenario(connection):
        ids = await seed_context(connection)
        command_id = uuid4()
        await insert_running_command(
            connection,
            ids,
            command_id,
        )
        original = (
            (
                await connection.execute(
                    text("SELECT * FROM work_order.edit_version_commands WHERE command_id=:id"),
                    {
                        "id": command_id,
                    },
                )
            )
            .mappings()
            .one()
        )
        value = {
            "command_id": "gen_random_uuid()",
            "edit_version_id": "gen_random_uuid()",
            "feature_id": "gen_random_uuid()",
            "actor_user_id": "gen_random_uuid()",
            "request_fingerprint": "'different'",
            "created_at": "created_at + interval '1 day'",
        }[field]
        with pytest.raises(DBAPIError) as error:
            async with connection.begin_nested():
                await connection.execute(
                    text(
                        f"""
                        UPDATE work_order.edit_version_commands
                        SET
                            {field}={value},
                            state='succeeded',
                            response_status=200,
                            response_payload='{{}}'::jsonb,
                            completed_at=now()
                        WHERE command_id=:id
                        """
                    ),
                    {
                        "id": command_id,
                    },
                )
        assert error.value.orig.sqlstate == "23514"
        assert error.value.orig.__cause__.constraint_name == "ck_ev_commands_identity"
        after = (
            (
                await connection.execute(
                    text("SELECT * FROM work_order.edit_version_commands WHERE command_id=:id"),
                    {
                        "id": command_id,
                    },
                )
            )
            .mappings()
            .one()
        )
        assert after == original

    run_scenario(scenario)


RESUME_SQL = """
    UPDATE work_order.edit_version_commands
    SET
        state='running',
        response_status=NULL,
        response_payload=NULL,
        rejection_code=NULL,
        rejection_message=NULL,
        completed_at=NULL,
        retry_on_access_change=false
    WHERE command_id=:id
"""


@pytest.mark.parametrize(
    "initial",
    ["succeeded", "rejected", "access_rejected"],
)
def test_only_access_rejection_can_resume(initial) -> None:
    async def scenario(connection):
        ids = await seed_context(connection)
        command_id = uuid4()
        await insert_running_command(
            connection,
            ids,
            command_id,
        )
        await finish_command(
            connection,
            command_id,
            state="succeeded" if initial == "succeeded" else "rejected",
            retry_on_access_change=initial == "access_rejected",
        )
        if initial == "access_rejected":
            await connection.execute(
                text(RESUME_SQL),
                {
                    "id": command_id,
                },
            )
            await finish_command(
                connection,
                command_id,
                state="succeeded",
            )
            await connection.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
            assert (
                await connection.scalar(
                    text("SELECT state FROM work_order.edit_version_commands WHERE command_id=:id"),
                    {
                        "id": command_id,
                    },
                )
                == "succeeded"
            )
        else:
            with pytest.raises(DBAPIError) as error:
                async with connection.begin_nested():
                    await connection.execute(
                        text(RESUME_SQL),
                        {
                            "id": command_id,
                        },
                    )
            assert error.value.orig.sqlstate == "23514"

    run_scenario(scenario)


@pytest.mark.parametrize(
    "state",
    ["succeeded", "rejected"],
)
def test_terminal_command_cannot_be_inserted_directly(state) -> None:
    async def scenario(connection):
        ids = await seed_context(connection)
        command_id = uuid4()
        await insert_running_command(
            connection,
            ids,
            command_id,
        )
        await finish_command(
            connection,
            command_id,
            state=state,
        )
        with pytest.raises(DBAPIError) as error:
            async with connection.begin_nested():
                await connection.execute(
                    text(
                        """
                    INSERT INTO work_order.edit_version_commands
                    SELECT
                        gen_random_uuid(),
                        edit_version_id,
                        feature_id,
                        actor_user_id,
                        request_fingerprint,
                        state,
                        retry_on_access_change,
                        response_status,
                        response_payload,
                        rejection_code,
                        rejection_message,
                        created_at,
                        completed_at
                    FROM work_order.edit_version_commands
                    WHERE command_id=:id
                """
                    ),
                    {
                        "id": command_id,
                    },
                )
        assert error.value.orig.sqlstate == "23514"

    run_scenario(scenario)


@pytest.mark.parametrize(
    "state",
    ["succeeded", "rejected"],
)
def test_terminal_response_cannot_be_overwritten(state) -> None:
    async def scenario(connection):
        ids = await seed_context(connection)
        command_id = uuid4()
        await insert_running_command(
            connection,
            ids,
            command_id,
        )
        await finish_command(
            connection,
            command_id,
            state=state,
        )
        mutation = (
            "response_payload='{}'::jsonb" if state == "succeeded" else "rejection_message='New'"
        )
        with pytest.raises(DBAPIError) as error:
            async with connection.begin_nested():
                await connection.execute(
                    text(
                        f"UPDATE work_order.edit_version_commands SET {mutation} WHERE command_id=:id"
                    ),
                    {
                        "id": command_id,
                    },
                )
        assert error.value.orig.sqlstate == "23514"

    run_scenario(scenario)


def test_failed_access_retry_preserves_previous_result() -> None:
    async def scenario(engine):
        command_id = uuid4()
        async with engine.begin() as connection:
            ids = await seed_context(connection)
            await insert_running_command(
                connection,
                ids,
                command_id,
            )
            await finish_command(
                connection,
                command_id,
                state="rejected",
                retry_on_access_change=True,
            )
            original = dict(
                (
                    await connection.execute(
                        text("SELECT * FROM work_order.edit_version_commands WHERE command_id=:id"),
                        {
                            "id": command_id,
                        },
                    )
                )
                .mappings()
                .one()
            )
        async with engine.connect() as connection:
            async with connection.begin():
                await connection.execute(
                    text(RESUME_SQL),
                    {
                        "id": command_id,
                    },
                )
                await connection.rollback()
        async with engine.connect() as connection:
            after = dict(
                (
                    await connection.execute(
                        text("SELECT * FROM work_order.edit_version_commands WHERE command_id=:id"),
                        {
                            "id": command_id,
                        },
                    )
                )
                .mappings()
                .one()
            )
            assert after == original

    run_committed_scenario(scenario)
