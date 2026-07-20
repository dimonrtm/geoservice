from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from utility_service.web_api.middleware.correlation_id import (
    CORRELATION_ID_HEADER,
    CorrelationIdMiddleware,
    is_valid_correlation_id,
)


def create_test_app():
    api = FastAPI()
    api.add_middleware(CorrelationIdMiddleware)

    @api.get("/ok")
    def ok() -> dict[str, bool]:
        return {"ok": True}

    return CORSMiddleware(
        app=api,
        allow_origins=["http://frontend.local"],
        allow_methods=["GET"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=[CORRELATION_ID_HEADER],
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("request-123", True),
        ("a.b_c:d-1", True),
        ("", False),
        ("contains space", False),
        ("x" * 129, False),
        (None, False),
    ],
)
def test_correlation_id_validation(value: object, expected: bool) -> None:
    assert is_valid_correlation_id(value) is expected


def test_missing_header_generates_uuid() -> None:
    response = TestClient(create_test_app()).get("/ok")

    assert response.status_code == 200
    UUID(response.headers[CORRELATION_ID_HEADER])


def test_valid_header_is_preserved() -> None:
    response = TestClient(create_test_app()).get(
        "/ok",
        headers={CORRELATION_ID_HEADER: "client-request-123"},
    )

    assert response.headers[CORRELATION_ID_HEADER] == "client-request-123"


def test_invalid_header_is_replaced() -> None:
    response = TestClient(create_test_app()).get(
        "/ok",
        headers={CORRELATION_ID_HEADER: "contains space"},
    )

    generated = response.headers[CORRELATION_ID_HEADER]
    UUID(generated)
    assert generated != "contains space"


def test_cors_exposes_correlation_header() -> None:
    response = TestClient(create_test_app()).get(
        "/ok",
        headers={"Origin": "http://frontend.local"},
    )

    assert response.headers["access-control-allow-origin"] == "http://frontend.local"
    assert CORRELATION_ID_HEADER in response.headers["access-control-expose-headers"]


def test_main_health_uses_production_correlation_boundary() -> None:
    from utility_service.web_api.main import app
    from utility_service.utils.settings import settings

    origin = settings.cors_origins[0]

    response = TestClient(app).get(
        "/health",
        headers={"Origin": origin},
    )

    assert response.status_code == 200
    UUID(response.headers[CORRELATION_ID_HEADER])
    assert response.headers["access-control-allow-origin"] == origin
    assert CORRELATION_ID_HEADER in response.headers["access-control-expose-headers"]
