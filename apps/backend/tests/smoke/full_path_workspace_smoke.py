from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


EXPECTED_WORK_ORDER_CODE = "WO-001"
EXPECTED_WORK_ORDER_ID = "6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0401"
EXPECTED_AOI_ID = "6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0100"
EXPECTED_FEATURE_COUNT = 19
EXPECTED_ASSOCIATION_COUNT = 9

JsonPayload = dict[str, Any]
UrlOpen = Callable[..., Any]


class SmokeFailure(RuntimeError):
    """Raised when the live full path smoke finds a broken runtime contract."""


@dataclass(frozen=True)
class SmokeConfig:
    base_url: str
    editor_email: str
    editor_password: str

    @classmethod
    def from_env(cls) -> "SmokeConfig":
        return cls(
            base_url=os.getenv("GEOSERVICE_BASE_URL", "http://127.0.0.1:8000").rstrip("/"),
            editor_email=os.getenv(
                "GEOSERVICE_EDITOR_EMAIL",
                "alexey.editor@example.local",
            ),
            editor_password=os.getenv(
                "GEOSERVICE_EDITOR_PASSWORD",
                "alexey-editor-password",
            ),
        )


def request_json(
    config: SmokeConfig,
    method: str,
    path: str,
    *,
    token: str | None = None,
    payload: JsonPayload | None = None,
    opener: UrlOpen = urlopen,
) -> JsonPayload:
    url = f"{config.base_url}{path}"
    headers = {"Accept": "application/json"}
    data: bytes | None = None

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif method in {"POST", "PUT", "PATCH"}:
        data = b""

    if token is not None:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(url, data=data, headers=headers, method=method)

    try:
        with opener(request, timeout=10) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        raise SmokeFailure(f"HTTP {exc.code} для {method} {path}: {body}") from exc
    except (OSError, URLError, TimeoutError) as exc:
        raise SmokeFailure(f"HTTP-запрос не выполнен для {method} {path}: {exc}") from exc

    if not body:
        return {}

    try:
        decoded = json.loads(body)
    except json.JSONDecodeError as exc:
        raise SmokeFailure(f"Некорректный JSON для {method} {path}: {body[:500]}") from exc

    if not isinstance(decoded, dict):
        raise SmokeFailure(f"Неожиданная форма JSON для {method} {path}: {decoded!r}")
    return decoded


def login(config: SmokeConfig, *, opener: UrlOpen = urlopen) -> str:
    payload = request_json(
        config,
        "POST",
        "/api/v1/auth/login",
        payload={
            "email": config.editor_email,
            "password": config.editor_password,
        },
        opener=opener,
    )
    token = payload.get("access_token")
    if not isinstance(token, str) or not token:
        raise SmokeFailure("Проверка входа не прошла: login не вернул access_token")
    return token


def load_assigned_work_order(
    config: SmokeConfig,
    token: str,
    *,
    opener: UrlOpen = urlopen,
) -> JsonPayload:
    payload = request_json(
        config,
        "GET",
        "/api/v1/work-orders/assigned-to-me",
        token=token,
        opener=opener,
    )
    work_orders = payload.get("workOrders")
    if not isinstance(work_orders, list):
        raise SmokeFailure(
            "Проверка назначенного наряда не прошла: response не содержит список workOrders"
        )

    for item in work_orders:
        if not isinstance(item, dict):
            continue
        if item.get("code") == EXPECTED_WORK_ORDER_CODE:
            work_order_id = item.get("id")
            if work_order_id != EXPECTED_WORK_ORDER_ID:
                raise SmokeFailure(
                    "Проверка назначенного наряда не прошла: "
                    f"id {EXPECTED_WORK_ORDER_CODE} равен {work_order_id!r}, "
                    f"ожидается {EXPECTED_WORK_ORDER_ID}"
                )
            return item

    codes = [item.get("code") for item in work_orders if isinstance(item, dict)]
    raise SmokeFailure(
        "Проверка назначенного наряда не прошла: "
        f"{EXPECTED_WORK_ORDER_CODE} не найден в assigned list {codes!r}"
    )


def open_edit_version(
    config: SmokeConfig,
    token: str,
    work_order_id: str,
    *,
    opener: UrlOpen = urlopen,
) -> str:
    payload = request_json(
        config,
        "POST",
        f"/api/v1/work-orders/{work_order_id}/edit-versions",
        token=token,
        opener=opener,
    )
    edit_version = payload.get("editVersion")
    if not isinstance(edit_version, dict):
        raise SmokeFailure(
            "Проверка EditVersion не прошла: response не содержит объект editVersion"
        )

    edit_version_id = edit_version.get("id")
    if not isinstance(edit_version_id, str) or not edit_version_id:
        raise SmokeFailure("Проверка EditVersion не прошла: editVersion.id отсутствует")

    returned_work_order_id = edit_version.get("workOrderId")
    if returned_work_order_id != work_order_id:
        raise SmokeFailure(
            "Проверка EditVersion не прошла: "
            f"editVersion.workOrderId равен {returned_work_order_id!r}, "
            f"ожидается {work_order_id}"
        )

    return edit_version_id


def load_workspace(
    config: SmokeConfig,
    token: str,
    work_order_id: str,
    edit_version_id: str,
    *,
    opener: UrlOpen = urlopen,
) -> JsonPayload:
    return request_json(
        config,
        "GET",
        f"/api/v1/work-orders/{work_order_id}/edit-versions/{edit_version_id}/workspace",
        token=token,
        opener=opener,
    )


def assert_workspace(
    payload: JsonPayload,
    *,
    work_order_id: str,
    edit_version_id: str,
) -> None:
    work_order = payload.get("workOrder")
    if not isinstance(work_order, dict):
        raise SmokeFailure("Агрегат workspace не совпадает: response не содержит объект workOrder")

    if work_order.get("id") != work_order_id:
        raise SmokeFailure(
            "Агрегат workspace не совпадает: "
            f"workOrder.id равен {work_order.get('id')!r}, ожидается {work_order_id}"
        )

    scope = work_order.get("scope")
    aoi = scope.get("aoi") if isinstance(scope, dict) else None
    if not isinstance(aoi, dict) or aoi.get("id") != EXPECTED_AOI_ID:
        actual_aoi_id = aoi.get("id") if isinstance(aoi, dict) else None
        raise SmokeFailure(
            "Данные workspace не совпадают: "
            f"AOI id равен {actual_aoi_id!r}, ожидается {EXPECTED_AOI_ID}"
        )

    edit_version = work_order.get("editVersion")
    if not isinstance(edit_version, dict) or edit_version.get("id") != edit_version_id:
        actual_edit_version_id = edit_version.get("id") if isinstance(edit_version, dict) else None
        raise SmokeFailure(
            "Агрегат workspace не совпадает: "
            f"editVersion.id равен {actual_edit_version_id!r}, ожидается {edit_version_id}"
        )

    features_payload = edit_version.get("features")
    features = features_payload.get("features") if isinstance(features_payload, dict) else None
    if not isinstance(features, list) or len(features) != EXPECTED_FEATURE_COUNT:
        actual_count = len(features) if isinstance(features, list) else None
        raise SmokeFailure(
            "Данные workspace не совпадают: "
            f"количество features равно {actual_count!r}, ожидается {EXPECTED_FEATURE_COUNT}"
        )

    associations = edit_version.get("associations")
    if not isinstance(associations, list) or len(associations) != EXPECTED_ASSOCIATION_COUNT:
        actual_count = len(associations) if isinstance(associations, list) else None
        raise SmokeFailure(
            "Данные workspace не совпадают: "
            f"количество associations равно {actual_count!r}, "
            f"ожидается {EXPECTED_ASSOCIATION_COUNT}"
        )


def run_smoke(config: SmokeConfig, *, opener: UrlOpen = urlopen) -> None:
    token = login(config, opener=opener)
    work_order = load_assigned_work_order(config, token, opener=opener)
    work_order_id = str(work_order["id"])
    edit_version_id = open_edit_version(config, token, work_order_id, opener=opener)
    workspace = load_workspace(config, token, work_order_id, edit_version_id, opener=opener)
    assert_workspace(
        workspace,
        work_order_id=work_order_id,
        edit_version_id=edit_version_id,
    )
    print(
        "Полный smoke-путь workspace прошел успешно: "
        f"{EXPECTED_WORK_ORDER_CODE} -> {edit_version_id}, "
        f"features={EXPECTED_FEATURE_COUNT}, associations={EXPECTED_ASSOCIATION_COUNT}"
    )


def main() -> int:
    try:
        run_smoke(SmokeConfig.from_env())
    except SmokeFailure as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
