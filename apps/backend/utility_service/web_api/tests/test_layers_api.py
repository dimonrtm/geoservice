from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from utility_service.use_cases.deps import (
    get_auth_service,
    get_feature_service,
    get_layer_service,
)
from utility_service.use_cases.schemas.feature.delete_feature_response import (
    DeleteFeatureResponse,
)
from utility_service.use_cases.schemas.feature.feature_collection_out import (
    FeatureCollectionMetaOut,
    FeatureCollectionOut,
)
from utility_service.use_cases.schemas.feature.feature_out import FeatureOut
from utility_service.use_cases.schemas.layer.layer_list_out import LayerListOut
from utility_service.use_cases.schemas.layer.layer_out import LayerOut
from utility_service.web_api.api import auth as auth_api
from utility_service.web_api.api.auth import create_access_token
from utility_service.web_api.api.exception_handlers import install_exception_handlers
from utility_service.web_api.api.layers import layers_router
from utility_service.web_api.tests.auth_user_factory import auth_user


USER_ID = UUID("10000000-0000-0000-0000-000000000001")
LAYER_ID = UUID("20000000-0000-0000-0000-000000000001")
FEATURE_ID = UUID("30000000-0000-0000-0000-000000000001")


@dataclass(frozen=True)
class LegacyLayerRequest:
    method: str
    path: str
    params: dict[str, str] | None = None
    json: dict[str, object] | None = None


LEGACY_LAYER_REQUESTS = [
    LegacyLayerRequest("GET", "/api/v1/layers"),
    LegacyLayerRequest(
        "GET",
        f"/api/v1/layers/{LAYER_ID}/features",
        params={"bbox": "0,0,1,1"},
    ),
    LegacyLayerRequest(
        "GET",
        f"/api/v1/layers/{LAYER_ID}/features/{FEATURE_ID}",
    ),
    LegacyLayerRequest(
        "POST",
        f"/api/v1/layers/{LAYER_ID}/features",
        json={
            "geometry": {"type": "Point", "coordinates": [1.0, 2.0]},
            "properties": {"name": "Created"},
        },
    ),
    LegacyLayerRequest(
        "PATCH",
        f"/api/v1/layers/{LAYER_ID}/features/{FEATURE_ID}",
        json={
            "version": 1,
            "geometry": None,
            "properties": {"name": "Updated"},
        },
    ),
    LegacyLayerRequest(
        "DELETE",
        f"/api/v1/layers/{LAYER_ID}/features/{FEATURE_ID}",
        json={"version": 1},
    ),
]


class FakeLayerService:
    def __init__(self):
        self.get_layers_calls = 0

    async def get_layers(self) -> LayerListOut:
        self.get_layers_calls += 1
        return LayerListOut(
            layers=[
                LayerOut(
                    id=LAYER_ID,
                    name="points",
                    title="Points",
                    geometryType="Point",
                    srid=4326,
                )
            ]
        )


class FakeFeatureService:
    def __init__(self):
        self.calls: list[tuple[str, UUID]] = []

    async def get_features_from_bbox(self, layer_id, bbox, limit, after_id):
        self.calls.append(("get_features_from_bbox", layer_id))
        return FeatureCollectionOut(
            features=[],
            meta=FeatureCollectionMetaOut(
                bbox=(bbox.min_lon, bbox.min_lat, bbox.max_lon, bbox.max_lat),
                limit=limit or 500,
                returned=0,
                truncated=False,
            ),
        )

    async def create_feature(self, layer_id, request):
        self.calls.append(("create_feature", layer_id))
        return feature_out(version=1, properties=request.properties)

    async def update_feature(self, layer_id, feature_id, request):
        self.calls.append(("update_feature", layer_id))
        return feature_out(version=request.version + 1, properties=request.properties or {})

    async def delete_feature(self, layer_id, feature_id, request):
        self.calls.append(("delete_feature", layer_id))
        return DeleteFeatureResponse(featureId=feature_id)

    async def get_feature(self, layer_id, feature_id):
        self.calls.append(("get_feature", layer_id))
        return feature_out(version=1, properties={"name": "Existing"})


def feature_out(version: int, properties: dict[str, object]) -> FeatureOut:
    return FeatureOut(
        id=FEATURE_ID,
        version=version,
        geometry={"type": "Point", "coordinates": [1.0, 2.0]},
        properties=properties,
    )


def build_app(role: str, layer_service: FakeLayerService, feature_service: FakeFeatureService):
    user = auth_user(role, user_id=USER_ID)

    async def get_user_by_id(_user_id):
        return user

    app = FastAPI()
    install_exception_handlers(app)
    app.include_router(layers_router)
    app.dependency_overrides[get_auth_service] = lambda: SimpleNamespace(
        get_user_by_id=get_user_by_id
    )
    app.dependency_overrides[get_layer_service] = lambda: layer_service
    app.dependency_overrides[get_feature_service] = lambda: feature_service
    return app


def auth_headers(role: str) -> dict[str, str]:
    token = create_access_token(str(USER_ID), role)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize("role", ["editor", "reviewer"])
@pytest.mark.parametrize("request_spec", LEGACY_LAYER_REQUESTS)
def test_legacy_layers_disabled_blocks_authenticated_roles(
    monkeypatch,
    role: str,
    request_spec: LegacyLayerRequest,
) -> None:
    monkeypatch.setattr(auth_api.settings, "legacy_gis_api_enabled", False)
    layer_service = FakeLayerService()
    feature_service = FakeFeatureService()
    client = TestClient(build_app(role, layer_service, feature_service))

    response = client.request(
        request_spec.method,
        request_spec.path,
        headers=auth_headers(role),
        params=request_spec.params,
        json=request_spec.json,
    )

    assert response.status_code == 403
    body = response.json()
    assert body["code"] == "LEGACY_GIS_API_DISABLED"
    assert body["message"] == "Legacy GIS API отключен."
    assert layer_service.get_layers_calls == 0
    assert feature_service.calls == []


@pytest.mark.parametrize("request_spec", LEGACY_LAYER_REQUESTS)
def test_legacy_layers_enabled_blocks_reviewer_before_services(
    monkeypatch,
    request_spec: LegacyLayerRequest,
) -> None:
    monkeypatch.setattr(auth_api.settings, "legacy_gis_api_enabled", True)
    layer_service = FakeLayerService()
    feature_service = FakeFeatureService()
    client = TestClient(build_app("reviewer", layer_service, feature_service))

    response = client.request(
        request_spec.method,
        request_spec.path,
        headers=auth_headers("reviewer"),
        params=request_spec.params,
        json=request_spec.json,
    )

    assert response.status_code == 403
    assert response.json()["code"] == "ROLE_NOT_ALLOWED"
    assert layer_service.get_layers_calls == 0
    assert feature_service.calls == []


def test_legacy_layers_enabled_allows_editor_to_list_layers(monkeypatch) -> None:
    monkeypatch.setattr(auth_api.settings, "legacy_gis_api_enabled", True)
    layer_service = FakeLayerService()
    feature_service = FakeFeatureService()
    client = TestClient(build_app("editor", layer_service, feature_service))

    response = client.get("/api/v1/layers", headers=auth_headers("editor"))

    assert response.status_code == 200
    assert response.json() == {
        "layers": [
            {
                "id": str(LAYER_ID),
                "name": "points",
                "title": "Points",
                "geometryType": "Point",
                "srid": 4326,
            }
        ]
    }
    assert layer_service.get_layers_calls == 1
