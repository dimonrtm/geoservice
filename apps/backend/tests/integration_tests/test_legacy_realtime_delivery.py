import asyncio

from httpx import ASGITransport, AsyncClient

from tests.integration_tests.first_save_schema_support import run_committed_scenario
from tests.integration_tests.test_browser_auth_session_races import (
    browser_context,
    issue,
)
from tests.integration_tests.test_legacy_patch_properties import (
    ORIGINAL_GEOMETRY,
    seed_legacy_feature,
)
from tests.integration_tests.workspace_api_support import build_workspace_api
from utility_service.use_cases.services.realtime_connection_manager import (
    WebSocketUserContext,
)
from utility_service.use_cases.tests.test_realtime_connection_manager import (
    DummyWebSocket,
)
from utility_service.utils.settings import settings
from utility_service.web_api.api.auth import create_access_token
from utility_service.web_api.api.layers import layers_router


def test_crud_and_fast_subscription_complete_while_slow_transport_is_blocked(
    monkeypatch,
):
    monkeypatch.setattr(settings, "legacy_gis_api_enabled", True)

    async def scenario(engine):
        app = build_workspace_api(engine)
        app.include_router(layers_router)
        manager = app.state.websocket_connection_manager
        layer, _ = await seed_legacy_feature(engine)
        entered, release = asyncio.Event(), asyncio.Event()

        class SlowSocket(DummyWebSocket):
            async def send_json(self, payload):
                if payload["type"] != "connected":
                    entered.set()
                    await release.wait()
                await super().send_json(payload)

        async with browser_context(engine) as user:
            session = await issue(engine, user)
            token = create_access_token(str(user.id), user.role, session.session_id)
            context = WebSocketUserContext(
                user.id, user.email, user.role, session.session_id
            )
            slow, fast = SlowSocket(), DummyWebSocket()
            for socket in (slow, fast):
                await manager.connect(layer, socket, context)
                assert (await socket.next_event())["type"] == "connected"
            try:
                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test",
                    headers={"Authorization": f"Bearer {token}"},
                ) as client:
                    url = f"/api/v1/layers/{layer}/features"
                    created = await asyncio.wait_for(
                        client.post(url, json={"geometry": ORIGINAL_GEOMETRY}), 3
                    )
                    assert created.status_code == 201, created.text
                    await asyncio.wait_for(entered.wait(), 2)
                    assert (await fast.next_event())["feature"] == created.json()
                    feature_url = created.headers["location"]
                    assert (await client.get(feature_url)).json() == created.json()
                    patched = await client.patch(
                        feature_url,
                        json={
                            "version": 1,
                            "geometry": None,
                            "properties": {"label": "v2"},
                        },
                    )
                    assert patched.status_code == 200, patched.text
                    assert (await fast.next_event())["feature"] == patched.json()[
                        "feature"
                    ]
                    assert (await client.get(feature_url)).json()["version"] == 2
                    conflict = await client.request(
                        "DELETE", feature_url, json={"version": 1}
                    )
                    assert conflict.status_code == 409
                    deleted = await client.request(
                        "DELETE", feature_url, json={"version": 2}
                    )
                    assert deleted.status_code == 200, deleted.text
                    event = await fast.next_event()
                    assert (
                        event["type"] == "feature_deleted"
                        and event["deletedVersion"] == 2
                    )
                    assert (await client.get(feature_url)).status_code == 404
                    assert (
                        not slow.closed
                        and not release.is_set()
                        and slow.received.empty()
                    )
            finally:
                release.set()
                await manager.shutdown()

    run_committed_scenario(scenario)
