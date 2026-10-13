from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from utility_service.use_cases.domain.exceptions.work_order_api_error import WorkOrderApiError
from utility_service.use_cases.schemas.edit_version.geometry_save_out import SaveGeometryResult
from utility_service.web_api.tests.test_work_orders_api import auth_context, build_app


def save_body():
    return (
        '{"commandId":"00000000-0000-0000-0000-000000000001",'
        '"draftVersionToken":"01","geometry":{"type":"LineString",'
        '"coordinates":[[0,0],[0.000000149999999999999999999,1],[2,0]]}}'
    )


def api_context(
    role="editor",
    *,
    active=True,
):
    auth, token, actor_id = auth_context(
        role,
        is_active=active,
    )
    service = AsyncMock()
    ids = [uuid4() for _ in range(3)]
    path = f"/api/v1/work-orders/{ids[0]}/edit-versions/{ids[1]}/features/{ids[2]}/geometry"
    payload = {
        "commandId": "00000000-0000-0000-0000-000000000001",
        "commandState": "succeeded",
        "draftVersionToken": "2",
        "operation": "updated",
        "hasPersistedChangeSet": True,
        "updatedFeature": {
            "id": str(ids[2]),
            "geometry": {
                "type": "LineString",
                "coordinates": [[0, 0], [0.0000001, 1], [2, 0]],
            },
        },
        "basicValidation": {
            "geometryStatus": "passed",
            "aoiStatus": "passed",
            "positionalAccuracyStatus": "POSITIONAL_ACCURACY_UNVERIFIED",
            "dirtyRelativeToBaseline": "passed",
        },
    }
    service.save_geometry.return_value = SaveGeometryResult(
        200,
        payload,
    )
    app = build_app(
        auth,
        service,
        AsyncMock(),
    )
    return (
        TestClient(
            app,
            raise_server_exceptions=False,
        ),
        service,
        path,
        token,
        actor_id,
        ids,
        payload,
    )


def put(
    client,
    path,
    token,
    body=None,
):
    return client.put(
        path,
        content=save_body() if body is None else body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )


def assert_error(
    response,
    status,
    code,
):
    assert response.status_code == status, response.text
    body = response.json()
    assert set(body) == {"code", "message", "correlationId"}
    assert body["code"] == code
    assert body["correlationId"] == response.headers["X-Correlation-ID"]


def test_put_passes_exact_request_and_actor():
    client, service, path, token, actor, ids, payload = api_context()
    response = put(
        client,
        path,
        token,
    )
    assert response.status_code == 200, response.text
    assert response.json() == payload
    args = service.save_geometry.call_args.kwargs
    assert (args["work_order_id"], args["edit_version_id"], args["feature_id"]) == tuple(ids)
    assert args["actor_id"] == actor
    assert args["request"].draft_version_token == "01"
    assert args["request"].geometry.coordinates[1][0] == Decimal("0.000000149999999999999999999")


@pytest.mark.parametrize(
    "body",
    [
        "{",
        save_body().replace(
            '"LineString"',
            '"MultiLineString"',
        ),
        save_body().replace(
            "[[0,0],[0.000000149999999999999999999,1],[2,0]]",
            "[]",
        ),
        save_body().replace(
            "[[0,0],[0.000000149999999999999999999,1],[2,0]]",
            "[[0,0]]",
        ),
        save_body().replace(
            "[0,0]",
            "[0,0,0]",
        ),
        save_body().replace(
            '"type":',
            '"type":"LineString","type":',
        ),
        save_body().replace(
            '"geometry":',
            '"extra":1,"geometry":',
        ),
        save_body().replace(
            "[0,0]",
            '["0",0]',
        ),
        save_body().replace(
            "[0,0]",
            "[true,0]",
        ),
        save_body().replace(
            "[0,0]",
            "[NaN,0]",
        ),
        save_body().replace(
            "[0,0]",
            "[Infinity,0]",
        ),
        save_body().replace(
            "[0,0]",
            "[181,0]",
        ),
        save_body().replace(
            "[0,0]",
            "[1e-325,0]",
        ),
        save_body().replace(
            "[0,0]",
            "[0." + "1" * 63 + ",0]",
        ),
        save_body().replace(
            '"01"',
            "1",
        ),
        save_body().replace(
            '"01"',
            '""',
        ),
        save_body().replace(
            "00000000-0000-0000-0000-000000000001",
            "not-a-uuid",
        ),
    ],
)
def test_put_format_errors_do_not_call_save(body):
    client, service, path, token, *_ = api_context()
    assert_error(
        put(
            client,
            path,
            token,
            body,
        ),
        422,
        "REQUEST_VALIDATION_ERROR",
    )
    service.save_geometry.assert_not_called()


@pytest.mark.parametrize(
    "endpoint",
    ["put", "workspace"],
)
def test_edit_path_validation_is_structured(endpoint):
    client, service, path, token, _, ids, _ = api_context()
    if endpoint == "put":
        response = put(
            client,
            path.replace(
                str(ids[0]),
                "bad-id",
            ),
            token,
        )
    else:
        response = client.get(
            f"/api/v1/work-orders/bad-id/edit-versions/{ids[1]}/workspace",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )
    assert_error(
        response,
        422,
        "REQUEST_VALIDATION_ERROR",
    )
    service.save_geometry.assert_not_called()


@pytest.mark.parametrize(
    "role,active,anonymous,status,code",
    [
        ("editor", True, True, 401, "AUTH_REQUIRED"),
        ("reviewer", True, False, 403, "ROLE_NOT_ALLOWED"),
        ("editor", False, False, 403, "USER_INACTIVE"),
    ],
)
def test_put_auth_guards(
    role,
    active,
    anonymous,
    status,
    code,
):
    client, service, path, token, *_ = api_context(
        role,
        active=active,
    )
    response = (
        client.put(
            path,
            content=save_body(),
        )
        if anonymous
        else put(
            client,
            path,
            token,
        )
    )
    assert_error(
        response,
        status,
        code,
    )
    service.save_geometry.assert_not_called()


@pytest.mark.parametrize(
    "status,code",
    [(404, "EDIT_VERSION_NOT_FOUND"), (409, "DRAFT_VERSION_STALE"), (422, "GEOMETRY_INVALID")],
)
def test_put_preserves_domain_error(
    status,
    code,
):
    client, service, path, token, *_ = api_context()
    service.save_geometry.side_effect = WorkOrderApiError(
        status,
        code,
        "Доменный отказ.",
    )
    response = put(
        client,
        path,
        token,
    )
    assert_error(
        response,
        status,
        code,
    )
    assert response.json()["message"] == "Доменный отказ."


def test_put_internal_failure_is_not_success():
    client, service, path, token, *_ = api_context()
    service.save_geometry.side_effect = RuntimeError("failure")
    assert_error(
        put(
            client,
            path,
            token,
        ),
        500,
        "INTERNAL_ERROR",
    )


def test_open_validation_keeps_existing_format():
    client, _, _, token, *_ = api_context()
    response = client.post(
        "/api/v1/work-orders/bad-id/edit-versions",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )
    assert response.status_code == 422
    assert set(response.json()) == {"detail"}
