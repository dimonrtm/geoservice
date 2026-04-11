from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.exception_handlers import install_exception_handlers
from domain.exceptions.business_validation_exception import BusinessValidationException


def create_test_app() -> FastAPI:
    app = FastAPI()
    install_exception_handlers(app)

    @app.get("/business-validation")
    def business_validation() -> None:
        raise BusinessValidationException("Некорректный bbox")

    @app.get("/unexpected-value-error")
    def unexpected_value_error() -> None:
        raise ValueError("Это программистская ошибка")

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
