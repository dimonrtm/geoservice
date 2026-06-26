from __future__ import annotations

import json
from urllib.parse import urlparse

import pytest

from tests.smoke.full_path_workspace_smoke import (
    EXPECTED_AOI_ID,
    EXPECTED_ASSOCIATION_COUNT,
    EXPECTED_FEATURE_COUNT,
    EXPECTED_WORK_ORDER_CODE,
    EXPECTED_WORK_ORDER_ID,
    SmokeConfig,
    SmokeFailure,
    assert_workspace,
    run_smoke,
)


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def workspace_payload(
    *,
    work_order_id: str = EXPECTED_WORK_ORDER_ID,
    edit_version_id: str = "edit-version-1",
    aoi_id: str = EXPECTED_AOI_ID,
    feature_count: int = EXPECTED_FEATURE_COUNT,
    association_count: int = EXPECTED_ASSOCIATION_COUNT,
) -> dict:
    return {
        "workOrder": {
            "id": work_order_id,
            "code": EXPECTED_WORK_ORDER_CODE,
            "scope": {
                "aoi": {
                    "id": aoi_id,
                },
            },
            "editVersion": {
                "id": edit_version_id,
                "features": {
                    "type": "FeatureCollection",
                    "features": [{"id": f"feature-{index}"} for index in range(feature_count)],
                },
                "associations": [
                    {"id": f"association-{index}"} for index in range(association_count)
                ],
            },
        }
    }


def fake_opener(routes: dict[tuple[str, str], dict], calls: list[tuple[str, str, str | None]]):
    def opener(request, timeout: int = 10) -> FakeResponse:
        parsed = urlparse(request.full_url)
        method = request.get_method()
        auth_header = request.headers.get("Authorization")
        calls.append((method, parsed.path, auth_header))
        payload = routes[(method, parsed.path)]
        return FakeResponse(payload)

    return opener


def test_run_smoke_uses_assigned_work_order_for_workspace_path(
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls: list[tuple[str, str, str | None]] = []
    edit_version_id = "edit-version-1"
    routes = {
        ("POST", "/api/v1/auth/login"): {
            "access_token": "token-1",
            "token_type": "bearer",
        },
        ("GET", "/api/v1/work-orders/assigned-to-me"): {
            "workOrders": [
                {
                    "id": EXPECTED_WORK_ORDER_ID,
                    "code": EXPECTED_WORK_ORDER_CODE,
                    "title": "Проверка участка фидера",
                    "description": "Открыть рабочий участок.",
                    "status": "assigned",
                }
            ]
        },
        ("POST", f"/api/v1/work-orders/{EXPECTED_WORK_ORDER_ID}/edit-versions"): {
            "created": False,
            "editVersion": {
                "id": edit_version_id,
                "workOrderId": EXPECTED_WORK_ORDER_ID,
                "ownerId": "editor-1",
                "status": "open",
                "baseNetworkRevision": 1,
            },
        },
        (
            "GET",
            f"/api/v1/work-orders/{EXPECTED_WORK_ORDER_ID}/edit-versions/"
            f"{edit_version_id}/workspace",
        ): workspace_payload(edit_version_id=edit_version_id),
    }

    config = SmokeConfig(
        base_url="http://utility_service:8000",
        editor_email="alexey.editor@example.local",
        editor_password="alexey-editor-password",
    )

    run_smoke(config, opener=fake_opener(routes, calls))

    assert calls == [
        ("POST", "/api/v1/auth/login", None),
        ("GET", "/api/v1/work-orders/assigned-to-me", "Bearer token-1"),
        ("POST", f"/api/v1/work-orders/{EXPECTED_WORK_ORDER_ID}/edit-versions", "Bearer token-1"),
        (
            "GET",
            f"/api/v1/work-orders/{EXPECTED_WORK_ORDER_ID}/edit-versions/"
            f"{edit_version_id}/workspace",
            "Bearer token-1",
        ),
    ]
    assert capsys.readouterr().out == (
        "Полный smoke-путь workspace прошел успешно: "
        f"{EXPECTED_WORK_ORDER_CODE} -> {edit_version_id}, "
        f"features={EXPECTED_FEATURE_COUNT}, associations={EXPECTED_ASSOCIATION_COUNT}\n"
    )


def test_run_smoke_fails_when_assigned_list_has_no_expected_work_order() -> None:
    calls: list[tuple[str, str, str | None]] = []
    routes = {
        ("POST", "/api/v1/auth/login"): {
            "access_token": "token-1",
            "token_type": "bearer",
        },
        ("GET", "/api/v1/work-orders/assigned-to-me"): {
            "workOrders": [
                {
                    "id": "other-work-order",
                    "code": "WO-999",
                    "title": "Другой наряд",
                    "description": None,
                    "status": "assigned",
                }
            ]
        },
    }
    config = SmokeConfig(
        base_url="http://utility_service:8000",
        editor_email="alexey.editor@example.local",
        editor_password="alexey-editor-password",
    )

    with pytest.raises(SmokeFailure, match="Проверка назначенного наряда не прошла"):
        run_smoke(config, opener=fake_opener(routes, calls))


def test_assert_workspace_reports_data_slice_mismatch() -> None:
    payload = workspace_payload(feature_count=18)

    with pytest.raises(SmokeFailure, match="Данные workspace не совпадают"):
        assert_workspace(
            payload,
            work_order_id=EXPECTED_WORK_ORDER_ID,
            edit_version_id="edit-version-1",
        )
