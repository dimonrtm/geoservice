import asyncio

from tests.integration_tests.first_save_schema_support import run_committed_scenario
from tests.integration_tests.save_geometry_support import MOVED, seed_save_context
from tests.integration_tests.test_geometry_save_api_integration import body
from tests.integration_tests.workspace_api_support import (
    build_workspace_api,
    client_for,
    current_geometry,
    geometry_path,
    read_workspace,
)
from utility_service.infrastructure.postgresql.geometry_codec import geometry_to_geojson
from utility_service.infrastructure.postgresql.repositories.edit_version_repository import (
    EditVersionRepository,
)


def test_workspace_read_during_uncommitted_save(monkeypatch):
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_save_context(connection)
        written = asyncio.Event()
        release = asyncio.Event()
        complete_command = EditVersionRepository.complete_command

        async def paused_completion(
            repository,
            *args,
            **kwargs,
        ):
            written.set()
            await asyncio.wait_for(
                release.wait(),
                timeout=10,
            )
            return await complete_command(
                repository,
                *args,
                **kwargs,
            )

        monkeypatch.setattr(
            EditVersionRepository,
            "complete_command",
            paused_completion,
        )
        app = build_workspace_api(engine)
        async with (
            client_for(
                app,
                ids,
            ) as writer,
            client_for(
                app,
                ids,
            ) as reader,
        ):
            before = await read_workspace(
                reader,
                ids,
            )
            save_task = asyncio.create_task(
                writer.put(
                    geometry_path(ids),
                    json=body(),
                )
            )
            try:
                await asyncio.wait_for(
                    written.wait(),
                    timeout=5,
                )
                during = await asyncio.wait_for(
                    read_workspace(
                        reader,
                        ids,
                    ),
                    timeout=5,
                )
                assert during == before
                assert during["draftVersionToken"] == "1"
                assert during["changeSet"] is None
                assert not save_task.done()
            finally:
                release.set()
                response = await asyncio.wait_for(
                    save_task,
                    timeout=5,
                )
            assert response.status_code == 200, response.text
            after = await read_workspace(
                reader,
                ids,
            )
            assert after["draftVersionToken"] == "2"
            assert after["hasPersistedChangeSet"] is True
            assert after["changeSet"]["baselineGeometry"] == current_geometry(
                before,
                ids,
            )
            assert current_geometry(
                after,
                ids,
            ) == geometry_to_geojson(MOVED)

    run_committed_scenario(scenario)
