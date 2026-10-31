from fastapi.testclient import TestClient

from utility_service.utils.settings import settings
from utility_service.web_api.main import app


def test_refresh_preflight_allows_expected_session_id():
    origin = settings.cors_origins[0]
    client = TestClient(app)

    response = client.options(
        "/api/v1/auth/session/refresh",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "x-expected-session-id",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert response.headers["access-control-allow-credentials"] == "true"
    assert "x-expected-session-id" in {
        header.strip().lower()
        for header in response.headers["access-control-allow-headers"].split(",")
    }
