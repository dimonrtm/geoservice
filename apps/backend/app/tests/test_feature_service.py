import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from domain.exceptions.feature_not_found_exception import FeatureNotFoundException
from domain.bbox import Bbox
from services.feature_service import FeatureService


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
        geometry_json='{"type":"Polygon","coordinates":[[[10,10],[20,10],[20,20],[10,10]]]}',
    )
    repository = AsyncMock()
    repository.get_layer_by_id.return_value = layer
    repository.list_features_bbox.return_value = ([row], True)
    service = FeatureService(session=None, layer_repository=repository)

    result = asyncio.run(service.get_features_from_bbox(layer_id, bbox, 500))

    assert result.meta.bbox == (10.0, 20.0, 30.0, 40.0)
    assert result.meta.limit == 500
    assert result.meta.returned == 1
    assert result.meta.truncated is True
    assert result.meta.sort == "id:asc"
    assert len(result.features) == 1
