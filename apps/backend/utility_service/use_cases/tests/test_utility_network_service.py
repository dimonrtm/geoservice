import asyncio
from copy import deepcopy
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from utility_service.use_cases.domain.exceptions.utility_network_api_error import (
    UtilityNetworkApiError,
)
from utility_service.infrastructure.postgresql.repositories.utility_network_repository import (
    FeederAggregateRow,
)
from utility_service.use_cases.services.utility_network_service import UtilityNetworkService


FEEDER_ID = UUID("6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0101")
FEATURE_ID = UUID("6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0221")
ASSOCIATION_ID = UUID("6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0301")


def feature_data() -> dict:
    return {
        "id": FEATURE_ID,
        "asset_code": "D-001",
        "feature_type": "device",
        "name": "Breaker",
        "description": "Start breaker",
        "properties": {
            "assetCode": "spoofed",
            "featureType": "line",
            "name": "spoofed",
            "description": "spoofed",
            "version": 999,
            "status": "closed",
        },
        "version": 1,
        "geometry_data": {
            "type": "Point",
            "coordinates": [65.52, 44.82],
        },
    }


def association_data() -> dict:
    return {
        "id": ASSOCIATION_ID,
        "from_feature_id": FEATURE_ID,
        "to_feature_id": FEATURE_ID,
        "association_type": "connectivity",
        "version": 1,
    }


def aggregate_row() -> FeederAggregateRow:
    return FeederAggregateRow(
        id=FEEDER_ID,
        code="synthetic_utility_feeder_01",
        name="Демонстрационный фидер 10 кВ",
        is_active=True,
        features_data=[feature_data()],
        associations_data=[association_data()],
    )


def test_get_feeder_maps_geojson_and_system_properties_take_precedence() -> None:
    repository = AsyncMock()
    repository.get_feeder_aggregate.return_value = aggregate_row()
    service = UtilityNetworkService(session=None, repository=repository)

    response = asyncio.run(service.get_feeder(FEEDER_ID))
    payload = response.model_dump(by_alias=True, mode="json")

    assert payload["id"] == str(FEEDER_ID)
    assert "aois" not in payload
    assert payload["network"]["features"][0]["properties"] == {
        "assetCode": "D-001",
        "featureType": "device",
        "name": "Breaker",
        "description": "Start breaker",
        "version": 1,
        "status": "closed",
    }
    repository.get_feeder_aggregate.assert_awaited_once_with(FEEDER_ID)


def test_get_feeder_raises_structured_404_when_missing() -> None:
    repository = AsyncMock()
    repository.get_feeder_aggregate.return_value = None
    service = UtilityNetworkService(session=None, repository=repository)

    with pytest.raises(UtilityNetworkApiError) as exc_info:
        asyncio.run(service.get_feeder(FEEDER_ID))

    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "FEEDER_NOT_FOUND"


def test_get_feeder_rejects_association_to_missing_feature() -> None:
    aggregate = aggregate_row()
    invalid_association = deepcopy(aggregate.associations_data[0])
    invalid_association["to_feature_id"] = uuid4()
    repository = AsyncMock()
    repository.get_feeder_aggregate.return_value = FeederAggregateRow(
        **{
            **aggregate.__dict__,
            "associations_data": [invalid_association],
        }
    )
    service = UtilityNetworkService(session=None, repository=repository)

    with pytest.raises(UtilityNetworkApiError) as exc_info:
        asyncio.run(service.get_feeder(FEEDER_ID))

    assert exc_info.value.status_code == 500
    assert exc_info.value.code == "UTILITY_DATASET_INVALID"


def test_get_feeder_rejects_invalid_geometry() -> None:
    aggregate = aggregate_row()
    invalid_feature = deepcopy(aggregate.features_data[0])
    invalid_feature["geometry_data"] = {
        "type": "Point",
        "coordinates": [999, 44.82],
    }
    repository = AsyncMock()
    repository.get_feeder_aggregate.return_value = FeederAggregateRow(
        **{
            **aggregate.__dict__,
            "features_data": [invalid_feature],
        }
    )
    service = UtilityNetworkService(session=None, repository=repository)

    with pytest.raises(UtilityNetworkApiError) as exc_info:
        asyncio.run(service.get_feeder(FEEDER_ID))

    assert exc_info.value.status_code == 500
    assert exc_info.value.code == "UTILITY_DATASET_INVALID"
