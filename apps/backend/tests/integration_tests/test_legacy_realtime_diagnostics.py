import asyncio
import logging

import pytest
from httpx import ASGITransport, AsyncClient

from tests.integration_tests.first_save_schema_support import run_committed_scenario
from tests.integration_tests.test_browser_auth_session_races import browser_context, issue
from tests.integration_tests.test_legacy_patch_properties import (
    ORIGINAL_GEOMETRY,
    seed_legacy_feature,
)
from tests.integration_tests.workspace_api_support import build_workspace_api
from utility_service.use_cases.services.feature_realtime_publisher import FeatureRealtimePublisher
from utility_service.use_cases.services.realtime_connection_manager import WebSocketUserContext
from utility_service.use_cases.tests.test_realtime_connection_manager import DummyWebSocket
from utility_service.use_cases.tests.test_realtime_publication_diagnostics import diagnostic_records
from utility_service.utils.settings import settings
from utility_service.web_api.api.auth import create_access_token
from utility_service.web_api.api.layers import layers_router


@pytest.mark.parametrize("operation", ["create", "update", "delete"])
@pytest.mark.parametrize("failure", ["publisher", "serialize", "send", "logging"])
def test_crud_commit_survives_publication_failure(monkeypatch, caplog, operation, failure):
    monkeypatch.setattr(settings, "legacy_gis_api_enabled", True)

    async def scenario(engine):
        app = build_workspace_api(engine)
        app.include_router(layers_router)
        manager = app.state.websocket_connection_manager
        layer, feature_id = await seed_legacy_feature(engine)
        sockets = [DummyWebSocket(), DummyWebSocket()]
        log_handler = None

        class FailingHandler(logging.Handler):
            def emit(self, record):
                raise OSError("sink unavailable")

        async def fail_publish(*args, **kwargs):
            raise RuntimeError("SECRET publisher")

        def fail_serialize(*args, **kwargs):
            raise ValueError("SECRET serialization")

        async with browser_context(engine) as user:
            session = await issue(engine, user)
            token = create_access_token(str(user.id), user.role, session.session_id)
            context = WebSocketUserContext(user.id, user.email, user.role, session.session_id)
            for socket in sockets:
                await manager.connect(layer, socket, context)
                await socket.next_event()
            if failure in ("publisher", "logging"):
                method = {"create": "created", "update": "updated", "delete": "deleted"}[operation]
                monkeypatch.setattr(
                    FeatureRealtimePublisher, f"publish_feature_{method}", fail_publish
                )
            elif failure == "serialize":
                monkeypatch.setattr(manager, "_serialize", fail_serialize)
            else:
                sockets[0].fail_on_send = True
            if failure == "logging":
                log_handler = FailingHandler()
                logging.getLogger("utility_service.realtime").addHandler(log_handler)
            try:
                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test",
                    headers={"Authorization": f"Bearer {token}"},
                ) as client:
                    url = f"/api/v1/layers/{layer}/features/{feature_id}"
                    if operation == "create":
                        response = await client.post(
                            f"/api/v1/layers/{layer}/features",
                            json={"geometry": ORIGINAL_GEOMETRY},
                        )
                        assert response.status_code == 201, response.text
                        url = response.headers["location"]
                        changed_id = response.json()["id"]
                        expected_version = 1
                    elif operation == "update":
                        response = await client.patch(
                            url,
                            json={"version": 1, "geometry": None, "properties": {"label": "v2"}},
                        )
                        assert response.status_code == 200, response.text
                        changed_id, expected_version = str(feature_id), 2
                    else:
                        response = await client.request("DELETE", url, json={"version": 1})
                        assert response.status_code == 200, response.text
                        changed_id, expected_version = str(feature_id), 1
                    # Independent HTTP request/session observes the committed state.
                    persisted = await client.get(url)
                    if operation == "delete":
                        assert persisted.status_code == 404
                    else:
                        assert persisted.status_code == 200
                        assert persisted.json()["version"] == expected_version
                    wire_event = None
                    if failure == "send":
                        wire_event = await sockets[1].next_event()
                        await asyncio.wait_for(sockets[0].close_event.wait(), 2)
                    records = diagnostic_records(caplog)
                    if failure == "logging":
                        assert records == []
                    else:
                        assert len(records) == (2 if failure == "serialize" else 1)
                        assert {item["featureId"] for item in records} == {changed_id}
                        assert {item["featureVersion"] for item in records} == {expected_version}
                        assert {item["layerId"] for item in records} == {str(layer)}
                        assert len({item["eventId"] for item in records}) == 1
                        if wire_event:
                            assert records[0]["eventId"] == wire_event["eventId"]
                            assert records[0]["connectionId"] != str(
                                manager._connections[layer][sockets[1]].connection_id
                            )
                    assert "SECRET" not in caplog.text
            finally:
                await manager.shutdown()
                if log_handler:
                    logging.getLogger("utility_service.realtime").removeHandler(log_handler)

    run_committed_scenario(scenario)


def test_rejected_crud_produces_no_realtime_failure(monkeypatch, caplog):
    monkeypatch.setattr(settings, "legacy_gis_api_enabled", True)

    async def scenario(engine):
        app = build_workspace_api(engine)
        app.include_router(layers_router)
        manager = app.state.websocket_connection_manager
        publication_attempts = []
        original_publish = manager.publish_event

        def observe_publication(context, build_event):
            publication_attempts.append(context.event_type)
            return original_publish(context, build_event)

        monkeypatch.setattr(manager, "publish_event", observe_publication)
        layer, feature_id = await seed_legacy_feature(engine)
        async with browser_context(engine) as user:
            session = await issue(engine, user)
            token = create_access_token(str(user.id), user.role, session.session_id)
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
                headers={"Authorization": f"Bearer {token}"},
            ) as client:
                url = f"/api/v1/layers/{layer}/features/{feature_id}"
                response = await client.patch(
                    url, json={"version": 99, "geometry": None, "properties": {}}
                )
                assert response.status_code == 409
                response = await client.request("DELETE", url, json={"version": 99})
                assert response.status_code == 409
                response = await client.post(
                    f"/api/v1/layers/{layer}/features",
                    json={"geometry": {"type": "Point", "coordinates": [10, 10]}},
                )
                assert response.status_code == 422
                assert (await client.get(url)).json()["version"] == 1
                assert diagnostic_records(caplog) == []
                assert publication_attempts == []
        await app.state.websocket_connection_manager.shutdown()

    run_committed_scenario(scenario)
