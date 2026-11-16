import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from utility_service.use_cases.domain.exceptions.work_order_operation_error import (
    WorkOrderOperationCode,
    WorkOrderOperationError,
)
from utility_service.web_api.api.error_handling.exception_handlers import install_exception_handlers
from utility_service.web_api.middleware.correlation_id import CorrelationIdMiddleware


@pytest.mark.parametrize(
    ("code", "status"),
    [
        ("WORK_ORDER_ACTOR_NOT_FOUND", 404),
        ("ROLE_NOT_ALLOWED", 403),
        ("WORK_ORDER_NOT_FOUND", 404),
        ("WORK_ORDER_NOT_ASSIGNED", 403),
        ("WORK_ORDER_STATE_CONFLICT", 409),
        ("WORK_ORDER_CONTEXT_INVALID", 422),
    ],
)
def test_operation_errors_preserve_http_contract(code, status):
    api = FastAPI()
    api.add_middleware(CorrelationIdMiddleware)
    install_exception_handlers(api)
    error = WorkOrderOperationError(WorkOrderOperationCode(code), "Ошибка операции наряда.")
    assert not hasattr(error, "status_code")

    @api.get("/failure")
    def fail():
        raise error

    response = TestClient(api, raise_server_exceptions=False).get(
        "/failure", headers={"X-Correlation-ID": "operation-error-test"}
    )
    assert response.status_code == status
    assert response.json() == {
        "code": code,
        "message": "Ошибка операции наряда.",
        "correlationId": "operation-error-test",
    }
    assert response.headers["X-Correlation-ID"] == "operation-error-test"


def test_mapping_covers_every_operation_code():
    from utility_service.web_api.api.error_handling.work_order_error_mapping import (
        work_order_error_status,
    )

    assert {code.value for code in WorkOrderOperationCode} == {
        "WORK_ORDER_ACTOR_NOT_FOUND",
        "ROLE_NOT_ALLOWED",
        "WORK_ORDER_NOT_FOUND",
        "WORK_ORDER_NOT_ASSIGNED",
        "WORK_ORDER_STATE_CONFLICT",
        "WORK_ORDER_CONTEXT_INVALID",
    }
    for code in WorkOrderOperationCode:
        assert isinstance(work_order_error_status(code), int)
