import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from utility_service.domain_services.bbox import Bbox
from utility_service.use_cases.domain.exceptions.feature_not_found_exception import (
    FeatureNotFoundException,
)
from utility_service.use_cases.domain.exceptions.version_mismatch_exception import (
    VersionMismatchException,
)
from utility_service.use_cases.schemas.feature.create_feature_in import CreateFeatureIn
from utility_service.use_cases.schemas.feature.delete_feature_request import (
    DeleteFeatureRequest,
)
from utility_service.use_cases.schemas.feature.patch_feature_request import (
    PatchFeatureRequest,
)
from utility_service.use_cases.services.feature_service import FeatureService


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


def test_create_feature_publishes_created_event_after_success() -> None:
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
    publisher = AsyncMock()
    service = FeatureService(
        session=DummySession(),
        layer_repository=repository,
        realtime_publisher=publisher,
    )
    request = CreateFeatureIn(geometry=POLYGON_GEOMETRY, properties={"name": "Created"})

    result = asyncio.run(service.create_feature(layer_id, request))

    assert result.id == created_id
    publisher.publish_feature_created.assert_awaited_once_with(layer_id, result)


def test_create_feature_does_not_fail_when_realtime_publish_raises() -> None:
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
    publisher = AsyncMock()
    publisher.publish_feature_created.side_effect = RuntimeError("socket down")
    service = FeatureService(
        session=DummySession(),
        layer_repository=repository,
        realtime_publisher=publisher,
    )
    request = CreateFeatureIn(geometry=POLYGON_GEOMETRY, properties={"name": "Created"})

    result = asyncio.run(service.create_feature(layer_id, request))

    assert result.id == created_id
    publisher.publish_feature_created.assert_awaited_once()


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
    request = PatchFeatureRequest(
        version=2, geometry=None, properties={"name": "After"}
    )

    result = asyncio.run(service.update_feature(layer_id, feature_id, request))

    assert result.id == feature_id
    assert result.version == 3
    assert result.properties == {"name": "After"}
    assert result.geometry.model_dump(mode="python") == UPDATED_POLYGON_GEOMETRY


def test_update_feature_publishes_updated_event_after_success() -> None:
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
    publisher = AsyncMock()
    service = FeatureService(
        session=DummySession(),
        layer_repository=repository,
        realtime_publisher=publisher,
    )
    request = PatchFeatureRequest(
        version=2, geometry=None, properties={"name": "After"}
    )

    result = asyncio.run(service.update_feature(layer_id, feature_id, request))

    assert result.id == feature_id
    publisher.publish_feature_updated.assert_awaited_once_with(layer_id, result)


def test_delete_feature_publishes_deleted_event_after_success() -> None:
    layer_id = uuid4()
    feature_id = uuid4()
    layer = SimpleNamespace(
        id=layer_id,
        geometry_type="Polygon",
        storage_table="polygon_features",
    )
    repository = AsyncMock()
    repository.get_layer_by_id.return_value = layer
    repository.delete_feature_if_version_matches.return_value = (True, object)
    publisher = AsyncMock()
    service = FeatureService(
        session=DummySession(),
        layer_repository=repository,
        realtime_publisher=publisher,
    )

    result = asyncio.run(
        service.delete_feature(layer_id, feature_id, DeleteFeatureRequest(version=3))
    )

    assert result.featureId == feature_id
    publisher.publish_feature_deleted.assert_awaited_once_with(layer_id, feature_id, 3)


@pytest.mark.parametrize("properties", [{"name": "After"}, {}])
def test_update_feature_does_not_publish_event_on_version_mismatch(properties) -> None:
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
    repository.update_feature_if_version_matches.return_value = (None, object)
    repository.get_current_version.return_value = SimpleNamespace(version=5)
    publisher = AsyncMock()
    service = FeatureService(
        session=DummySession(),
        layer_repository=repository,
        realtime_publisher=publisher,
    )
    request = PatchFeatureRequest(version=2, geometry=None, properties=properties)
    with pytest.raises(VersionMismatchException):
        asyncio.run(service.update_feature(layer_id, feature_id, request))

    publisher.publish_feature_updated.assert_not_awaited()


def make_update_service(initial_properties):
    layer_id, feature_id = uuid4(), uuid4()
    repository = AsyncMock()
    repository.get_layer_by_id.return_value = SimpleNamespace(
        id=layer_id, geometry_type="Polygon", storage_table="feature_polygons"
    )
    repository.get_feature.return_value = SimpleNamespace(
        id=feature_id,
        version=2,
        properties=initial_properties,
        geometry_data=POLYGON_GEOMETRY,
    )
    repository.update_feature_if_version_matches.return_value = (
        SimpleNamespace(id=feature_id, version=3),
        object,
    )
    publisher = AsyncMock()
    service = FeatureService(DummySession(), repository, publisher)
    return service, repository, publisher, layer_id, feature_id


@pytest.mark.parametrize("geometry", [None, UPDATED_POLYGON_GEOMETRY])
@pytest.mark.parametrize("initial_properties", [{"name": "Before"}, {}])
def test_update_feature_clears_properties(geometry, initial_properties) -> None:
    service, repository, publisher, layer_id, feature_id = make_update_service(
        initial_properties
    )
    request = PatchFeatureRequest(version=2, geometry=geometry, properties={})

    result = asyncio.run(service.update_feature(layer_id, feature_id, request))

    assert repository.update_feature_if_version_matches.await_args.args[3] == {}
    assert result.id == feature_id
    assert result.properties == {}
    assert result.version == 3
    expected_geometry = (
        POLYGON_GEOMETRY if geometry is None else UPDATED_POLYGON_GEOMETRY
    )
    assert result.geometry.model_dump(mode="python") == expected_geometry
    publisher.publish_feature_updated.assert_awaited_once_with(layer_id, result)
    if geometry is not None:
        repository.get_feature.assert_not_awaited()


@pytest.mark.parametrize("initial_properties", [{"name": "Before"}, {}])
def test_update_feature_preserves_properties_when_null(initial_properties) -> None:
    service, repository, publisher, layer_id, feature_id = make_update_service(
        initial_properties
    )
    request = PatchFeatureRequest(
        version=2, geometry=UPDATED_POLYGON_GEOMETRY, properties=None
    )

    result = asyncio.run(service.update_feature(layer_id, feature_id, request))

    assert repository.update_feature_if_version_matches.await_args.args[3] is None
    assert result.properties == initial_properties
    assert result.version == 3
    assert result.geometry.model_dump(mode="python") == UPDATED_POLYGON_GEOMETRY
    publisher.publish_feature_updated.assert_awaited_once_with(layer_id, result)


def test_update_feature_preserves_falsy_property_values() -> None:
    service, repository, publisher, layer_id, feature_id = make_update_service(
        {"name": "Before"}
    )
    request = PatchFeatureRequest(
        version=2,
        geometry=None,
        properties={"enabled": False, "count": 0, "note": None},
    )

    result = asyncio.run(service.update_feature(layer_id, feature_id, request))

    assert repository.update_feature_if_version_matches.await_args.args[3] == {
        "enabled": False,
        "count": 0,
        "note": None,
    }
    assert result.properties == {"enabled": False, "count": 0, "note": None}
    assert result.version == 3
    assert result.geometry.model_dump(mode="python") == POLYGON_GEOMETRY
    publisher.publish_feature_updated.assert_awaited_once_with(layer_id, result)
