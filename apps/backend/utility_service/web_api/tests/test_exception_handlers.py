from fastapi import FastAPI
from fastapi.testclient import TestClient

from utility_service.web_api.api.exception_handlers import install_exception_handlers
from utility_service.use_cases.domain.exceptions.business_validation_exception import (
    BusinessValidationException,
)
from utility_service.use_cases.domain.exceptions.utility_network_api_error import (
    UtilityNetworkApiError,
)


def create_test_app() -> FastAPI:
    app = FastAPI()
    install_exception_handlers(app)

    @app.get("/business-validation")
    def business_validation() -> None:
        raise BusinessValidationException("Некорректный bbox")

    @app.get("/unexpected-value-error")
    def unexpected_value_error() -> None:
        raise ValueError("Это программистская ошибка")

    @app.get("/utility-not-found")
    def utility_not_found() -> None:
        raise UtilityNetworkApiError(404, "FEEDER_NOT_FOUND", "Фидер не найден.")

    return app


def test_business_validation_exception_returns_422() -> None:
    client = TestClient(create_test_app(), raise_server_exceptions=False)

    response = client.get("/business-validation")

    assert response.status_code == 422
    assert response.json() == {"error": "Некорректный bbox"}


def test_unexpected_value_error_returns_500() -> None:
    client = TestClient(create_test_app(), raise_server_exceptions=False)

    response = client.get("/unexpected-value-error")

    assert response.status_code == 500


def test_utility_network_api_error_returns_structured_response() -> None:
    client = TestClient(create_test_app(), raise_server_exceptions=False)

    response = client.get(
        "/utility-not-found",
        headers={"X-Correlation-ID": "test-correlation-id"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "code": "FEEDER_NOT_FOUND",
        "message": "Фидер не найден.",
        "correlationId": "test-correlation-id",
        "details": {},
    }
