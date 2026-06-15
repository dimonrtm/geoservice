from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.auth import create_access_token
from api.deps import get_auth_service, get_utility_network_service
from api.exception_handlers import install_exception_handlers
from api.utility_network import utility_network_router
from domain.exceptions.utility_network_api_error import UtilityNetworkApiError
from models.user import UserRole
from schemas.utility_network import (
    UtilityAssociationOut,
    UtilityFeatureCollectionOut,
    UtilityFeederOut,
)


FEEDER_ID = UUID("6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0101")
FROM_ID = UUID("6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0221")
TO_ID = UUID("6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0211")


def build_app(auth_service: object, utility_service: object) -> FastAPI:
    app = FastAPI()
    install_exception_handlers(app)
    app.include_router(utility_network_router)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_utility_network_service] = lambda: utility_service
    return app


def auth_context(role: UserRole, *, is_active: bool = True) -> tuple[AsyncMock, str]:
    user_id = uuid4()
    token = create_access_token(str(user_id), role.value)
    auth_service = AsyncMock()
    auth_service.get_user_by_id.return_value = SimpleNamespace(
        id=user_id,
        email=f"{role.value}@example.local",
        role=role,
        is_active=is_active,
    )
    return auth_service, token


def feeder_response() -> UtilityFeederOut:
    return UtilityFeederOut(
        id=FEEDER_ID,
        code="synthetic_utility_feeder_01",
        name="Демонстрационный фидер 10 кВ",
        is_active=True,
        aois=UtilityFeatureCollectionOut(features=[]),
        network=UtilityFeatureCollectionOut(features=[]),
        associations=[
            UtilityAssociationOut(
                id=UUID("6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0301"),
                from_feature_id=FROM_ID,
                to_feature_id=TO_ID,
                association_type="connectivity",
                version=1,
            )
        ],
    )


def test_active_editor_gets_feeder_with_wire_aliases() -> None:
    auth_service, token = auth_context(UserRole.EDITOR)
    utility_service = AsyncMock()
    utility_service.get_feeder.return_value = feeder_response()

    response = TestClient(build_app(auth_service, utility_service)).get(
        f"/api/v1/utility-network/feeders/{FEEDER_ID}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(FEEDER_ID)
    assert response.json()["isActive"] is True
    assert response.json()["associations"][0]["fromFeatureId"] == str(FROM_ID)
    utility_service.get_feeder.assert_awaited_once_with(FEEDER_ID)


def test_reviewer_is_denied_before_utility_service_call() -> None:
    auth_service, token = auth_context(UserRole.REVIEWER)
    utility_service = AsyncMock()

    response = TestClient(build_app(auth_service, utility_service)).get(
        f"/api/v1/utility-network/feeders/{FEEDER_ID}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["code"] == "ROLE_NOT_ALLOWED"
    utility_service.get_feeder.assert_not_awaited()


def test_inactive_editor_is_denied_before_utility_service_call() -> None:
    auth_service, token = auth_context(UserRole.EDITOR, is_active=False)
    utility_service = AsyncMock()

    response = TestClient(build_app(auth_service, utility_service)).get(
        f"/api/v1/utility-network/feeders/{FEEDER_ID}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["code"] == "USER_INACTIVE"
    utility_service.get_feeder.assert_not_awaited()


def test_request_without_token_returns_structured_401() -> None:
    response = TestClient(build_app(AsyncMock(), AsyncMock())).get(
        f"/api/v1/utility-network/feeders/{FEEDER_ID}"
    )

    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_REQUIRED"


def test_invalid_feeder_uuid_returns_standard_422() -> None:
    auth_service, token = auth_context(UserRole.EDITOR)
    utility_service = AsyncMock()

    response = TestClient(build_app(auth_service, utility_service)).get(
        "/api/v1/utility-network/feeders/not-a-uuid",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    utility_service.get_feeder.assert_not_awaited()


def test_service_not_found_becomes_structured_404() -> None:
    auth_service, token = auth_context(UserRole.EDITOR)
    utility_service = AsyncMock()
    utility_service.get_feeder.side_effect = UtilityNetworkApiError(
        404,
        "FEEDER_NOT_FOUND",
        "Фидер не найден.",
    )

    response = TestClient(build_app(auth_service, utility_service)).get(
        f"/api/v1/utility-network/feeders/{FEEDER_ID}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["code"] == "FEEDER_NOT_FOUND"
