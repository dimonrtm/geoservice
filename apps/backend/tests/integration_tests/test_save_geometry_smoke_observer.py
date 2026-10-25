from importlib import import_module, util

import pytest
from sqlalchemy import text

from tests.integration_tests.first_save_schema_support import run_committed_scenario
from tests.integration_tests.save_geometry_support import seed_save_context, call_save, request
from tests.smoke.full_path_workspace_smoke import SmokeFailure


def test_smoke_observer_reads_committed_state_and_rejects_wrong_identity():
    async def scenario(engine):
        name = "tests.smoke.save_geometry_observer"
        assert util.find_spec(name) is not None, "Отсутствует SQL observer"
        observer = import_module(name)
        async with engine.begin() as connection:
            ids = await seed_save_context(connection)
        target = {key: str(ids[key]) for key in ("work_order_id", "edit_version_id", "feature_id")}
        before = await observer.read_snapshot(engine, **target)
        assert before["revision"] == 1
        assert before["commands"] == before["events"] == []
        assert before["geometryBytes"] == before["baselineBytes"]
        assert before["owner"] == str(ids["actor_user_id"])
        assert await observer.read_snapshot(engine, **target) == before
        with pytest.raises(SmokeFailure):
            await observer.read_snapshot(
                engine, **{**target, "feature_id": str(ids["work_order_id"])}
            )
        value = request()
        await call_save(engine, ids, value)
        after = await observer.read_snapshot(engine, **target)
        assert after["revision"] == 2
        assert after["geometry"] == {
            "type": "LineString",
            "coordinates": [[65.52, 44.82], [65.525, 44.8215], [65.53, 44.82]],
        }
        assert after["baselineBytes"] == before["baselineBytes"]
        assert after["commands"][0]["command_id"] == str(value.command_id)
        assert after["commands"][0]["response_payload"]["draftVersionToken"] == "2"
        assert after["events"][0]["event_type"] == "change_set_persisted"
        assert after["events"][0]["beforeBytes"] == before["geometryBytes"]
        assert after["events"][0]["afterBytes"] == after["geometryBytes"]
        # The observer opens a read-only transaction; even an accidental write must fail.
        async with engine.connect() as connection:
            async with connection.begin():
                await observer.begin_read_only(connection)
                assert await connection.scalar(text("SHOW transaction_read_only")) == "on"

    run_committed_scenario(scenario)
