import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from domain.bbox import Bbox
from domain.exceptions.feature_not_found_exception import FeatureNotFoundException
from schemas.create_feature_in import CreateFeatureIn
from schemas.patch_feature_request import PatchFeatureRequest
from services.feature_service import FeatureService


class DummyTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class DummySession:
    def begin(self):
        return DummyTransaction()


POLYGON_GEOMETRY = {
    "type": "Polygon",
    "coordinates": [[(10.0, 10.0), (20.0, 10.0), (20.0, 20.0), (10.0, 10.0)]],
}
UPDATED_POLYGON_GEOMETRY = {
    "type": "Polygon",
    "coordinates": [[(10.0, 10.0), (25.0, 10.0), (25.0, 25.0), (10.0, 10.0)]],
}


def test_get_feature_raises_feature_not_found_when_repository_returns_none() -> None:
    layer_id = uuid4()
    feature_id = uuid4()
    layer = SimpleNamespace(
        id=layer_id,
        geometry_type="Polygon",
        storage_table="polygon_features",
    )
    repository = AsyncMock()
    repository.get_layer_by_id.return_value = layer
    repository.get_feature.return_value = None
    service = FeatureService(session=None, layer_repository=repository)

    with pytest.raises(FeatureNotFoundException, match=str(feature_id)):
        asyncio.run(service.get_feature(layer_id, feature_id))


def test_get_features_from_bbox_returns_meta_with_truncation_flag() -> None:
    layer_id = uuid4()
    layer = SimpleNamespace(
        id=layer_id,
        geometry_type="Polygon",
        storage_table="polygon_features",
    )
    bbox = Bbox(min_lon=10.0, min_lat=20.0, max_lon=30.0, max_lat=40.0)
    row = SimpleNamespace(
        id=uuid4(),
        version=2,
        properties={"name": "A"},
        geometry_data=POLYGON_GEOMETRY,
    )
    repository = AsyncMock()
    repository.get_layer_by_id.return_value = layer
    repository.list_features_bbox.return_value = ([row], True, str(row.id))
    service = FeatureService(session=None, layer_repository=repository)

    result = asyncio.run(service.get_features_from_bbox(layer_id, bbox, 500))

    assert result.meta.bbox == (10.0, 20.0, 30.0, 40.0)
    assert result.meta.limit == 500
    assert result.meta.returned == 1
    assert result.meta.truncated is True
    assert result.meta.sort == "id:asc"
    assert result.meta.next_cursor == str(row.id)
    assert len(result.features) == 1


def test_get_features_from_bbox_passes_after_id_to_repository() -> None:
    layer_id = uuid4()
    after_id = uuid4()
    layer = SimpleNamespace(
        id=layer_id,
        geometry_type="Polygon",
        storage_table="polygon_features",
    )
    bbox = Bbox(min_lon=10.0, min_lat=20.0, max_lon=30.0, max_lat=40.0)
    repository = AsyncMock()
    repository.get_layer_by_id.return_value = layer
    repository.list_features_bbox.return_value = ([], False, None)
    service = FeatureService(session=None, layer_repository=repository)

    asyncio.run(service.get_features_from_bbox(layer_id, bbox, 250, after_id))

    repository.list_features_bbox.assert_awaited_once_with(layer, bbox, 250, after_id)


def test_create_feature_returns_geometry_and_properties_from_request() -> None:
    layer_id = uuid4()
    created_id = uuid4()
    layer = SimpleNamespace(
        id=layer_id,
        geometry_type="Polygon",
        storage_table="polygon_features",
    )
    repository = AsyncMock()
    repository.get_layer_by_id.return_value = layer
    repository.create_feature.return_value = SimpleNamespace(id=created_id, version=1)
    service = FeatureService(session=DummySession(), layer_repository=repository)
    request = CreateFeatureIn(geometry=POLYGON_GEOMETRY, properties={"name": "Created"})

    result = asyncio.run(service.create_feature(layer_id, request))

    assert result.id == created_id
    assert result.version == 1
    assert result.properties == {"name": "Created"}
    assert result.geometry.model_dump(mode="python") == POLYGON_GEOMETRY


def test_update_feature_uses_current_feature_for_missing_geometry() -> None:
    layer_id = uuid4()
    feature_id = uuid4()
    layer = SimpleNamespace(
        id=layer_id,
        geometry_type="Polygon",
        storage_table="polygon_features",
    )
    repository = AsyncMock()
    repository.get_layer_by_id.return_value = layer
    repository.get_feature.return_value = SimpleNamespace(
        id=feature_id,
        version=2,
        properties={"name": "Before"},
        geometry_data=UPDATED_POLYGON_GEOMETRY,
    )
    repository.update_feature_if_version_matches.return_value = (
        SimpleNamespace(id=feature_id, version=3),
        object,
    )
    service = FeatureService(session=DummySession(), layer_repository=repository)
    request = PatchFeatureRequest(version=2, geometry=None, properties={"name": "After"})

    result = asyncio.run(service.update_feature(layer_id, feature_id, request))

    assert result.id == feature_id
    assert result.version == 3
    assert result.properties == {"name": "After"}
    assert result.geometry.model_dump(mode="python") == UPDATED_POLYGON_GEOMETRY
