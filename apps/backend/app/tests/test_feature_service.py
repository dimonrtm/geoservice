import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from domain.exceptions.feature_not_found_exception import FeatureNotFoundException
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
