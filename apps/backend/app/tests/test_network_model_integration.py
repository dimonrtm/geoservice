from uuid import uuid4

import pytest
from geoalchemy2.elements import WKTElement
from sqlalchemy import delete, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.utility_network import (
    AOI,
    AssociationType,
    Feeder,
    FeatureType,
    NetworkAssociation,
    NetworkFeature,
)
from tests.network_db_support import run_in_rollback_transaction


def point(x: float, y: float, srid: int = 4326) -> WKTElement:
    return WKTElement(f"POINT ({x} {y})", srid=srid)


def line(srid: int = 4326) -> WKTElement:
    return WKTElement("LINESTRING (0 0, 1 1)", srid=srid)


def polygon() -> WKTElement:
    return WKTElement(
        "POLYGON ((0 0, 0 2, 2 2, 2 0, 0 0))",
        srid=4326,
    )


def multipolygon() -> WKTElement:
    return WKTElement(
        "MULTIPOLYGON (((0 0, 0 2, 2 2, 2 0, 0 0)))",
        srid=4326,
    )


async def create_feeder(session: AsyncSession, code: str) -> Feeder:
    feeder = Feeder(code=code, name=f"Feeder {code}")
    session.add(feeder)
    await session.flush()
    return feeder


async def create_feature(
    session: AsyncSession,
    feeder: Feeder,
    asset_code: str,
    feature_type: FeatureType,
    geometry: WKTElement,
) -> NetworkFeature:
    feature = NetworkFeature(
        feeder_id=feeder.id,
        asset_code=asset_code,
        feature_type=feature_type,
        geometry=geometry,
        name=asset_code,
    )
    session.add(feature)
    await session.flush()
    return feature


def test_valid_network_graph_and_defaults_are_persisted() -> None:
    async def scenario(session: AsyncSession) -> None:
        aoi = AOI(name="Workspace", geometry=polygon())
        feeder = await create_feeder(session, "F-001")
        junction = await create_feature(
            session,
            feeder,
            "J-001",
            FeatureType.JUNCTION,
            point(0, 0),
        )
        line_feature = await create_feature(
            session,
            feeder,
            "L-001",
            FeatureType.LINE,
            line(),
        )
        association = NetworkAssociation(
            feeder_id=feeder.id,
            from_feature_id=junction.id,
            to_feature_id=line_feature.id,
            association_type=AssociationType.CONNECTIVITY,
        )
        session.add_all([aoi, association])
        await session.flush()
        await session.refresh(feeder)
        await session.refresh(junction)
        await session.refresh(association)

        assert feeder.is_active is True
        assert junction.properties == {}
        assert junction.version == 1
        assert association.version == 1

    run_in_rollback_transaction(scenario)


def test_utility_tables_are_isolated_from_public_schema() -> None:
    async def scenario(session: AsyncSession) -> None:
        result = await session.execute(
            text(
                """
                SELECT schemaname, tablename
                FROM pg_tables
                WHERE tablename IN (
                    'aois',
                    'feeders',
                    'network_features',
                    'network_associations'
                )
                ORDER BY schemaname, tablename
                """
            )
        )
        assert set(result) == {
            ("utility_network", "aois"),
            ("utility_network", "feeders"),
            ("utility_network", "network_associations"),
            ("utility_network", "network_features"),
        }

    run_in_rollback_transaction(scenario)


def test_search_path_is_not_changed_for_utility_schema() -> None:
    async def scenario(session: AsyncSession) -> None:
        search_path = await session.scalar(text("SHOW search_path"))
        assert "utility_network" not in search_path

    run_in_rollback_transaction(scenario)


@pytest.mark.parametrize("geometry", [polygon(), multipolygon()])
def test_aoi_accepts_polygon_and_multipolygon(geometry: WKTElement) -> None:
    async def scenario(session: AsyncSession) -> None:
        session.add(AOI(name="AOI", geometry=geometry))
        await session.flush()

    run_in_rollback_transaction(scenario)


@pytest.mark.parametrize(
    ("feature_type", "geometry"),
    [
        (FeatureType.JUNCTION, line()),
        (FeatureType.DEVICE, line()),
        (FeatureType.LINE, point(0, 0)),
    ],
)
def test_feature_type_rejects_incompatible_geometry(
    feature_type: FeatureType,
    geometry: WKTElement,
) -> None:
    async def scenario(session: AsyncSession) -> None:
        feeder = await create_feeder(session, f"F-{uuid4()}")
        session.add(
            NetworkFeature(
                feeder_id=feeder.id,
                asset_code="X-001",
                feature_type=feature_type,
                geometry=geometry,
                name="Invalid geometry",
            )
        )
        with pytest.raises(IntegrityError):
            await session.flush()

    run_in_rollback_transaction(scenario)


@pytest.mark.parametrize(
    "geometry",
    [
        WKTElement("POINT EMPTY", srid=4326),
        WKTElement("POINT (0 0)", srid=3857),
    ],
)
def test_network_feature_rejects_empty_or_wrong_srid_geometry(
    geometry: WKTElement,
) -> None:
    async def scenario(session: AsyncSession) -> None:
        feeder = await create_feeder(session, f"F-{uuid4()}")
        session.add(
            NetworkFeature(
                feeder_id=feeder.id,
                asset_code="J-001",
                feature_type=FeatureType.JUNCTION,
                geometry=geometry,
                name="Invalid feature",
            )
        )
        with pytest.raises(DBAPIError):
            await session.flush()

    run_in_rollback_transaction(scenario)


def test_aoi_rejects_invalid_polygon() -> None:
    async def scenario(session: AsyncSession) -> None:
        invalid = WKTElement(
            "POLYGON ((0 0, 2 2, 0 2, 2 0, 0 0))",
            srid=4326,
        )
        session.add(AOI(name="Invalid AOI", geometry=invalid))
        with pytest.raises(IntegrityError):
            await session.flush()

    run_in_rollback_transaction(scenario)


@pytest.mark.parametrize(
    "geometry",
    [
        WKTElement("POLYGON EMPTY", srid=4326),
        WKTElement(
            "POLYGON ((0 0, 0 2, 2 2, 2 0, 0 0))",
            srid=3857,
        ),
    ],
)
def test_aoi_rejects_empty_or_wrong_srid_geometry(
    geometry: WKTElement,
) -> None:
    async def scenario(session: AsyncSession) -> None:
        session.add(AOI(name="Invalid AOI", geometry=geometry))
        with pytest.raises(DBAPIError):
            await session.flush()

    run_in_rollback_transaction(scenario)


def test_asset_code_is_unique_only_inside_feeder() -> None:
    async def scenario(session: AsyncSession) -> None:
        first = await create_feeder(session, "F-101")
        second = await create_feeder(session, "F-102")
        await create_feature(
            session,
            first,
            "J-001",
            FeatureType.JUNCTION,
            point(0, 0),
        )
        await create_feature(
            session,
            second,
            "J-001",
            FeatureType.JUNCTION,
            point(1, 1),
        )
        session.add(
            NetworkFeature(
                feeder_id=first.id,
                asset_code="J-001",
                feature_type=FeatureType.JUNCTION,
                geometry=point(2, 2),
                name="Duplicate",
            )
        )
        with pytest.raises(IntegrityError):
            await session.flush()

    run_in_rollback_transaction(scenario)


def test_association_rejects_self_reference() -> None:
    async def scenario(session: AsyncSession) -> None:
        feeder = await create_feeder(session, "F-201")
        feature = await create_feature(
            session,
            feeder,
            "J-001",
            FeatureType.JUNCTION,
            point(0, 0),
        )
        session.add(
            NetworkAssociation(
                feeder_id=feeder.id,
                from_feature_id=feature.id,
                to_feature_id=feature.id,
                association_type=AssociationType.CONNECTIVITY,
            )
        )
        with pytest.raises(IntegrityError):
            await session.flush()

    run_in_rollback_transaction(scenario)


def test_association_rejects_exact_directed_duplicate() -> None:
    async def scenario(session: AsyncSession) -> None:
        feeder = await create_feeder(session, "F-202")
        first = await create_feature(
            session,
            feeder,
            "J-001",
            FeatureType.JUNCTION,
            point(0, 0),
        )
        second = await create_feature(
            session,
            feeder,
            "J-002",
            FeatureType.JUNCTION,
            point(1, 1),
        )
        session.add(
            NetworkAssociation(
                feeder_id=feeder.id,
                from_feature_id=first.id,
                to_feature_id=second.id,
                association_type=AssociationType.CONNECTIVITY,
            )
        )
        await session.flush()
        session.add(
            NetworkAssociation(
                feeder_id=feeder.id,
                from_feature_id=first.id,
                to_feature_id=second.id,
                association_type=AssociationType.CONNECTIVITY,
            )
        )
        with pytest.raises(IntegrityError):
            await session.flush()

    run_in_rollback_transaction(scenario)


def test_reverse_association_is_allowed() -> None:
    async def scenario(session: AsyncSession) -> None:
        feeder = await create_feeder(session, "F-203")
        first = await create_feature(
            session,
            feeder,
            "J-001",
            FeatureType.JUNCTION,
            point(0, 0),
        )
        second = await create_feature(
            session,
            feeder,
            "J-002",
            FeatureType.JUNCTION,
            point(1, 1),
        )
        session.add_all(
            [
                NetworkAssociation(
                    feeder_id=feeder.id,
                    from_feature_id=first.id,
                    to_feature_id=second.id,
                    association_type=AssociationType.CONNECTIVITY,
                ),
                NetworkAssociation(
                    feeder_id=feeder.id,
                    from_feature_id=second.id,
                    to_feature_id=first.id,
                    association_type=AssociationType.CONNECTIVITY,
                ),
            ]
        )
        await session.flush()

    run_in_rollback_transaction(scenario)


def test_cross_feeder_association_is_rejected() -> None:
    async def scenario(session: AsyncSession) -> None:
        first_feeder = await create_feeder(session, "F-204")
        second_feeder = await create_feeder(session, "F-205")
        first = await create_feature(
            session,
            first_feeder,
            "J-001",
            FeatureType.JUNCTION,
            point(0, 0),
        )
        second = await create_feature(
            session,
            second_feeder,
            "J-001",
            FeatureType.JUNCTION,
            point(1, 1),
        )
        session.add(
            NetworkAssociation(
                feeder_id=first_feeder.id,
                from_feature_id=first.id,
                to_feature_id=second.id,
                association_type=AssociationType.CONNECTIVITY,
            )
        )
        with pytest.raises(IntegrityError):
            await session.flush()

    run_in_rollback_transaction(scenario)


def test_association_with_missing_endpoint_is_rejected() -> None:
    async def scenario(session: AsyncSession) -> None:
        feeder = await create_feeder(session, "F-206")
        first = await create_feature(
            session,
            feeder,
            "J-001",
            FeatureType.JUNCTION,
            point(0, 0),
        )
        session.add(
            NetworkAssociation(
                feeder_id=feeder.id,
                from_feature_id=first.id,
                to_feature_id=uuid4(),
                association_type=AssociationType.CONNECTIVITY,
            )
        )
        with pytest.raises(IntegrityError):
            await session.flush()

    run_in_rollback_transaction(scenario)


@pytest.mark.parametrize("model_name", ["feature", "association"])
def test_version_must_be_positive(model_name: str) -> None:
    async def scenario(session: AsyncSession) -> None:
        feeder = await create_feeder(session, f"F-{uuid4()}")
        first = await create_feature(
            session,
            feeder,
            "J-001",
            FeatureType.JUNCTION,
            point(0, 0),
        )
        if model_name == "feature":
            session.add(
                NetworkFeature(
                    feeder_id=feeder.id,
                    asset_code="J-002",
                    feature_type=FeatureType.JUNCTION,
                    geometry=point(1, 1),
                    name="Version zero",
                    version=0,
                )
            )
        else:
            second = await create_feature(
                session,
                feeder,
                "J-002",
                FeatureType.JUNCTION,
                point(1, 1),
            )
            session.add(
                NetworkAssociation(
                    feeder_id=feeder.id,
                    from_feature_id=first.id,
                    to_feature_id=second.id,
                    association_type=AssociationType.CONNECTIVITY,
                    version=0,
                )
            )
        with pytest.raises(IntegrityError):
            await session.flush()

    run_in_rollback_transaction(scenario)


def test_delete_restricts_non_empty_feeder() -> None:
    async def scenario(session: AsyncSession) -> None:
        feeder = await create_feeder(session, "F-401")
        await create_feature(
            session,
            feeder,
            "J-001",
            FeatureType.JUNCTION,
            point(0, 0),
        )
        with pytest.raises(IntegrityError):
            await session.execute(delete(Feeder).where(Feeder.id == feeder.id))
            await session.flush()

    run_in_rollback_transaction(scenario)


def test_delete_restricts_feature_used_by_association() -> None:
    async def scenario(session: AsyncSession) -> None:
        feeder = await create_feeder(session, "F-402")
        first = await create_feature(
            session,
            feeder,
            "J-001",
            FeatureType.JUNCTION,
            point(0, 0),
        )
        second = await create_feature(
            session,
            feeder,
            "J-002",
            FeatureType.JUNCTION,
            point(1, 1),
        )
        session.add(
            NetworkAssociation(
                feeder_id=feeder.id,
                from_feature_id=first.id,
                to_feature_id=second.id,
                association_type=AssociationType.CONNECTIVITY,
            )
        )
        await session.flush()

        with pytest.raises(IntegrityError):
            await session.execute(delete(NetworkFeature).where(NetworkFeature.id == first.id))
            await session.flush()

    run_in_rollback_transaction(scenario)
