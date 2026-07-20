import json
import logging
from uuid import UUID

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from utility_service.use_cases.domain.exceptions.auth_api_error import AuthApiError
from utility_service.use_cases.domain.exceptions.business_validation_exception import (
    BusinessValidationException,
)
from utility_service.use_cases.domain.exceptions.utility_network_api_error import (
    UtilityNetworkApiError,
)
from utility_service.use_cases.domain.exceptions.work_order_api_error import WorkOrderApiError
from utility_service.web_api.api.exception_handlers import install_exception_handlers
from utility_service.web_api.middleware.correlation_id import (
    CORRELATION_ID_HEADER,
    CorrelationIdMiddleware,
)
from utility_service.web_api.observability.api_error_logging import API_ERROR_LOGGER_NAME


def create_test_app():
    api = FastAPI()
    api.add_middleware(CorrelationIdMiddleware)
    install_exception_handlers(api)

    @api.get("/business-validation")
    def business_validation() -> None:
        raise BusinessValidationException("Некорректный bbox")

    @api.get("/unexpected-value-error")
    def unexpected_value_error() -> None:
        raise ValueError("Это программистская ошибка")

    @api.get("/utility-not-found")
    def utility_not_found() -> None:
        raise UtilityNetworkApiError(404, "FEEDER_NOT_FOUND", "Фидер не найден.")

    @api.get("/auth-required")
    def auth_required() -> None:
        raise AuthApiError(401, "AUTH_REQUIRED", "Требуется вход в систему.")

    @api.get("/work-order-context")
    def work_order_context() -> None:
        raise WorkOrderApiError(
            422,
            "WORK_ORDER_CONTEXT_INVALID",
            "Контекст рабочей задачи поврежден или неполон.",
        )

    @api.get("/utility-invalid")
    def utility_invalid() -> None:
        raise UtilityNetworkApiError(
            500,
            "UTILITY_DATASET_INVALID",
            "Utility dataset поврежден и не может быть прочитан.",
        )

    @api.get("/work-orders/{work_order_id}")
    def work_order_failure(work_order_id: str) -> None:
        raise ValueError(f"Внутренняя ошибка для {work_order_id}")

    return CORSMiddleware(
        app=api,
        allow_origins=["http://frontend.local"],
        allow_methods=["GET"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=[CORRELATION_ID_HEADER],
    )


def test_business_validation_exception_returns_422() -> None:
    client = TestClient(create_test_app(), raise_server_exceptions=False)

    response = client.get("/business-validation")

    assert response.status_code == 422
    assert response.json() == {"error": "Некорректный bbox"}
    UUID(response.headers[CORRELATION_ID_HEADER])


def test_unexpected_value_error_returns_500() -> None:
    client = TestClient(create_test_app(), raise_server_exceptions=False)

    response = client.get("/unexpected-value-error")

    assert response.status_code == 500


def test_utility_network_api_error_returns_structured_response() -> None:
    client = TestClient(create_test_app(), raise_server_exceptions=False)

    response = client.get(
        "/utility-not-found",
        headers={CORRELATION_ID_HEADER: "test-correlation-id"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "code": "FEEDER_NOT_FOUND",
        "message": "Фидер не найден.",
        "correlationId": "test-correlation-id",
    }
    assert response.headers[CORRELATION_ID_HEADER] == "test-correlation-id"
    assert "details" not in response.json()


def test_auth_api_error_returns_strict_structured_response() -> None:
    client = TestClient(create_test_app(), raise_server_exceptions=False)

    response = client.get(
        "/auth-required",
        headers={CORRELATION_ID_HEADER: "auth-correlation-id"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "code": "AUTH_REQUIRED",
        "message": "Требуется вход в систему.",
        "correlationId": "auth-correlation-id",
    }
    assert response.headers[CORRELATION_ID_HEADER] == "auth-correlation-id"
    assert "detail" not in response.json()
    assert "details" not in response.json()


def test_work_order_api_error_returns_strict_structured_response() -> None:
    client = TestClient(create_test_app(), raise_server_exceptions=False)

    response = client.get(
        "/work-order-context",
        headers={CORRELATION_ID_HEADER: "workflow-correlation-id"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "code": "WORK_ORDER_CONTEXT_INVALID",
        "message": "Контекст рабочей задачи поврежден или неполон.",
        "correlationId": "workflow-correlation-id",
    }
    assert response.headers[CORRELATION_ID_HEADER] == "workflow-correlation-id"
    assert "detail" not in response.json()
    assert "details" not in response.json()


def test_unexpected_error_returns_safe_structured_500(caplog) -> None:
    client = TestClient(create_test_app(), raise_server_exceptions=False)

    with caplog.at_level(logging.ERROR, logger=API_ERROR_LOGGER_NAME):
        response = client.get(
            "/work-orders/wo-secret?token=query-secret",
            headers={
                "Origin": "http://frontend.local",
                "Authorization": "Bearer auth-secret",
                "Cookie": "geoservice_session=cookie-secret",
                CORRELATION_ID_HEADER: "internal-correlation-id",
            },
        )

    assert response.status_code == 500
    assert response.json() == {
        "code": "INTERNAL_ERROR",
        "message": "Внутренняя ошибка сервиса",
        "correlationId": "internal-correlation-id",
    }
    assert response.headers[CORRELATION_ID_HEADER] == "internal-correlation-id"
    assert response.headers["access-control-allow-origin"] == "http://frontend.local"
    assert "wo-secret" not in response.text

    records = [record for record in caplog.records if record.name == API_ERROR_LOGGER_NAME]
    assert len(records) == 1
    record = records[0]
    event = json.loads(record.getMessage())
    assert event == {
        "event": "api_error_unhandled",
        "correlationId": "internal-correlation-id",
        "code": "INTERNAL_ERROR",
        "status": 500,
        "method": "GET",
        "route": "/work-orders/{work_order_id}",
    }
    assert record.exc_info is not None
    assert "query-secret" not in record.getMessage()
    assert "auth-secret" not in record.getMessage()
    assert "cookie-secret" not in record.getMessage()


def test_handled_4xx_writes_sanitized_info_event(caplog) -> None:
    client = TestClient(create_test_app(), raise_server_exceptions=False)

    with caplog.at_level(logging.INFO, logger=API_ERROR_LOGGER_NAME):
        response = client.get(
            "/auth-required?token=query-secret",
            headers={
                "Authorization": "Bearer auth-secret",
                CORRELATION_ID_HEADER: "auth-correlation-id",
            },
        )

    records = [record for record in caplog.records if record.name == API_ERROR_LOGGER_NAME]
    assert len(records) == 1
    record = records[0]
    event = json.loads(record.getMessage())
    assert record.levelno == logging.INFO
    assert record.exc_info is None
    assert event == {
        "event": "api_error_handled",
        "correlationId": "auth-correlation-id",
        "code": "AUTH_REQUIRED",
        "status": 401,
        "method": "GET",
        "route": "/auth-required",
    }
    assert response.headers[CORRELATION_ID_HEADER] == "auth-correlation-id"
    assert "query-secret" not in record.getMessage()
    assert "auth-secret" not in record.getMessage()


def test_handled_5xx_writes_error_without_exception_trace(caplog) -> None:
    client = TestClient(create_test_app(), raise_server_exceptions=False)

    with caplog.at_level(logging.ERROR, logger=API_ERROR_LOGGER_NAME):
        response = client.get(
            "/utility-invalid",
            headers={CORRELATION_ID_HEADER: "utility-correlation-id"},
        )

    records = [record for record in caplog.records if record.name == API_ERROR_LOGGER_NAME]
    assert len(records) == 1
    record = records[0]
    event = json.loads(record.getMessage())
    assert response.status_code == 500
    assert record.levelno == logging.ERROR
    assert record.exc_info is None
    assert event["code"] == "UTILITY_DATASET_INVALID"
    assert event["correlationId"] == "utility-correlation-id"
