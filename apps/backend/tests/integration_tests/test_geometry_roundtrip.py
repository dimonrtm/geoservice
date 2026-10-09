import json
from dataclasses import replace
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration_tests.first_save_schema_support import run_committed_scenario, seed_context
from utility_service.domain_services.edit_geometry.canonicalization import prepare_geometry
from utility_service.domain_services.edit_geometry.policy import GeometryPolicy
from utility_service.infrastructure.postgresql.geometry_codec import (
    decode_geometry,
    encode_geometry,
    geometry_to_geojson,
)
from utility_service.infrastructure.postgresql.repositories.work_order_repository import (
    WorkOrderRepository,
)
from utility_service.infrastructure.postgresql.models.user import UserRole
from utility_service.use_cases.services.workspace_service import WorkspaceService
from utility_service.web_api.tests.test_work_orders_api import build_app, auth_context
from utility_service.web_api.parsers.geometry_save_request import parse_geometry_save_request


def test_workspace_http_and_postgis_roundtrip_preserve_off_grid_baseline():
    async def scenario(engine):
        auth_service, token, actor_id = auth_context("editor")
        async with engine.begin() as connection:
            ids = await seed_context(
                connection,
                actor_user_id=actor_id,
            )
            params = {
                "id": ids["edit_version_id"],
                "feature": ids["feature_id"],
            }
            await connection.execute(
                text("UPDATE work_order.work_orders SET status='in_progress' WHERE id=:id"),
                {
                    "id": ids["work_order_id"],
                },
            )
            await connection.execute(
                text(
                    """
                    UPDATE work_order.edit_version_features
                    SET geometry = ST_GeomFromText(
                        'LINESTRING(65.5200000499 44.8200000501,65.5250000499 44.8205000501,65.5300000501 44.8200000499)',
                        4326
                    )
                    WHERE edit_version_id = :id
                        AND feature_id = :feature
                    """
                ),
                params,
            )
            baseline_bytes = await connection.scalar(
                text(
                    """
                    SELECT ST_AsEWKB(geometry)
                    FROM work_order.edit_version_features
                    WHERE edit_version_id = :id
                        AND feature_id = :feature
                    """
                ),
                params,
            )
            lossy = await connection.scalar(
                text(
                    """
                    SELECT ST_AsGeoJSON(geometry)::jsonb
                    FROM work_order.edit_version_features
                    WHERE edit_version_id = :id
                        AND feature_id = :feature
                    """
                ),
                params,
            )
        baseline = decode_geometry(baseline_bytes)
        assert Decimal(str(lossy["coordinates"][1][0])) != baseline.coordinates[1][0]
        actor_repository = SimpleNamespace(
            get_by_id=AsyncMock(
                return_value=SimpleNamespace(
                    id=actor_id,
                    role=UserRole.EDITOR,
                    is_active=True,
                )
            )
        )
        async with AsyncSession(engine) as session:
            workspace = WorkspaceService(
                session,
                actor_repository,
                WorkOrderRepository(session),
            )
            app = build_app(
                auth_service,
                AsyncMock(),
                workspace,
            )
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get(
                    f"/api/v1/work-orders/{ids['work_order_id']}/edit-versions/{ids['edit_version_id']}/workspace",
                    headers={
                        "Authorization": f"Bearer {token}",
                    },
                )
            assert response.status_code == 200, response.text
            payload = json.loads(
                response.content,
                parse_float=Decimal,
                parse_int=Decimal,
            )
            feature = next(
                f
                for f in payload["workOrder"]["editVersion"]["features"]["features"]
                if f["id"] == str(ids["feature_id"])
            )
            coordinates = tuple(tuple(p) for p in feature["geometry"]["coordinates"])
            assert coordinates == baseline.coordinates
        reverted = prepare_geometry(
            baseline,
            baseline,
            GeometryPolicy(Decimal("0.0000001")),
        ).geometry
        assert encode_geometry(reverted) == baseline_bytes
        async with engine.connect() as connection:
            stored = await connection.scalar(
                text("SELECT ST_AsEWKB(ST_GeomFromEWKB(:geometry))"),
                {
                    "geometry": encode_geometry(reverted),
                },
            )
            assert stored == baseline_bytes
            incoming = replace(
                baseline,
                coordinates=(
                    baseline.coordinates[0],
                    (Decimal("65.52600018"), Decimal("44.82150018")),
                    baseline.coordinates[-1],
                ),
            )
            policy = GeometryPolicy(Decimal("0.0000001"))
            candidate = prepare_geometry(
                incoming,
                baseline,
                policy,
            ).geometry
            assert candidate.coordinates[1] == (Decimal("65.5260002"), Decimal("44.8215002"))
            stored_candidate = await connection.scalar(
                text("SELECT ST_AsEWKB(ST_GeomFromEWKB(:geometry))"),
                {
                    "geometry": encode_geometry(candidate),
                },
            )
            decoded = decode_geometry(stored_candidate)
            assert decoded == candidate
            request = parse_geometry_save_request(
                json.dumps(
                    {
                        "commandId": str(ids["edit_version_id"]),
                        "draftVersionToken": "1",
                        "geometry": geometry_to_geojson(decoded),
                    }
                ).encode()
            )
            assert (
                prepare_geometry(
                    request.geometry,
                    baseline,
                    policy,
                ).geometry
                == candidate
            )

    run_committed_scenario(scenario)
