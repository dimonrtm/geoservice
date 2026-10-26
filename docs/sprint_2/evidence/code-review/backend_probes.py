"""Read-only воспроизведения ревью; mock repositories, без доступа к БД."""

import asyncio
import json
from time import perf_counter
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from utility_service.use_cases.tests.test_feature_service import (
    DummySession,
    POLYGON_GEOMETRY,
)
from utility_service.use_cases.schemas.feature.patch_feature_request import (
    PatchFeatureRequest,
)
from utility_service.use_cases.services.feature_service import FeatureService
from utility_service.web_api.parsers.geometry_save_request import (
    parse_geometry_save_request,
)


async def probe_empty_properties():
    feature_id = uuid4()
    repository = AsyncMock()
    repository.get_layer_by_id.return_value = SimpleNamespace(geometry_type="Polygon")
    repository.get_feature.return_value = SimpleNamespace(
        id=feature_id,
        version=1,
        properties={"name": "old"},
        geometry_data=POLYGON_GEOMETRY,
    )
    repository.update_feature_if_version_matches.return_value = (
        SimpleNamespace(id=feature_id, version=2),
        object,
    )
    service = FeatureService(DummySession(), repository)
    result = await service.update_feature(
        uuid4(),
        feature_id,
        PatchFeatureRequest(version=1, geometry=None, properties={}),
    )
    persisted_argument = repository.update_feature_if_version_matches.await_args.args[3]
    assert persisted_argument == {}
    assert result.properties == {"name": "old"}
    print(
        json.dumps(
            {
                "probe": "empty_properties",
                "db_argument": persisted_argument,
                "response_properties": result.properties,
            }
        )
    )
    try:
        await service.update_feature(
            uuid4(),
            feature_id,
            PatchFeatureRequest(version=1, geometry=POLYGON_GEOMETRY, properties={}),
        )
    except Exception as exc:
        print(
            json.dumps(
                {
                    "probe": "geometry_and_empty_properties",
                    "exception": type(exc).__name__,
                }
            )
        )
    else:
        raise AssertionError(
            "Expected current implementation to reject empty properties"
        )


def probe_large_geometry():
    count = 100_000
    body = json.dumps(
        {
            "commandId": str(uuid4()),
            "draftVersionToken": "1",
            "geometry": {"type": "LineString", "coordinates": [[1, 2]] * count},
        }
    ).encode()
    started = perf_counter()
    request = parse_geometry_save_request(body)
    elapsed = perf_counter() - started
    assert len(request.geometry.coordinates) == count
    print(
        json.dumps(
            {
                "probe": "large_geometry",
                "accepted_vertices": count,
                "body_bytes": len(body),
                "synchronous_seconds": round(elapsed, 3),
            }
        )
    )


asyncio.run(probe_empty_properties())
probe_large_geometry()
