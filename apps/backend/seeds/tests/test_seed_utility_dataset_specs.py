from decimal import Decimal
from uuid import UUID

from shapely.geometry import Point
from shapely.wkt import loads

from seeds.specs import seed_utility_dataset_specs as seed_specs
from utility_service.infrastructure.postgresql.models.utility_network import (
    AssociationType,
    FeatureType,
)
from seeds.specs.seed_utility_dataset_specs import (
    UTILITY_DATASET_SPEC,
    UTILITY_FEEDER_CODE,
    UTILITY_FEEDER_ID,
)
from seeds.specs.seed_work_order_specs import SEED_WORK_ORDER_AOI_SPEC


def test_utility_dataset_has_stable_identity_and_expected_counts() -> None:
    spec = UTILITY_DATASET_SPEC

    assert UTILITY_FEEDER_ID == UUID("6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0101")
    assert UTILITY_FEEDER_CODE == "synthetic_utility_feeder_01"
    assert spec.feeder.id == UTILITY_FEEDER_ID
    assert spec.feeder.code == UTILITY_FEEDER_CODE
    assert len(spec.features) == 19
    assert len(spec.associations) == 9


def test_utility_dataset_has_expected_feature_breakdown() -> None:
    counts = {
        feature_type: sum(
            feature.feature_type is feature_type for feature in UTILITY_DATASET_SPEC.features
        )
        for feature_type in FeatureType
    }

    assert counts == {
        FeatureType.JUNCTION: 7,
        FeatureType.LINE: 6,
        FeatureType.DEVICE: 6,
    }


def test_asset_codes_ids_and_association_edges_are_unique_and_valid() -> None:
    spec = UTILITY_DATASET_SPEC
    asset_codes = [feature.asset_code for feature in spec.features]
    feature_ids = [feature.id for feature in spec.features]
    feature_ids_set = set(feature_ids)
    edges = [
        (
            association.from_feature_id,
            association.to_feature_id,
            association.association_type,
        )
        for association in spec.associations
    ]

    assert len(asset_codes) == len(set(asset_codes))
    assert len(feature_ids) == len(feature_ids_set)
    assert len(edges) == len(set(edges))
    assert all(
        association.association_type is AssociationType.CONNECTIVITY
        for association in spec.associations
    )
    assert all(
        association.from_feature_id in feature_ids_set
        and association.to_feature_id in feature_ids_set
        and association.from_feature_id != association.to_feature_id
        for association in spec.associations
    )


def test_l003_is_the_only_structurally_eligible_demo_line() -> None:
    lines = [
        feature
        for feature in UTILITY_DATASET_SPEC.features
        if feature.feature_type is FeatureType.LINE
    ]
    eligible = [feature for feature in lines if len(loads(feature.geometry_wkt).coords) == 3]

    assert [feature.asset_code for feature in eligible] == ["L-003"]
    assert sum(len(loads(feature.geometry_wkt).coords) == 2 for feature in lines) == 5


def test_l003_has_exact_safe_internal_vertex_and_unchanged_endpoints() -> None:
    by_code = {feature.asset_code: feature for feature in UTILITY_DATASET_SPEC.features}
    line = loads(by_code["L-003"].geometry_wkt)
    aoi = loads(SEED_WORK_ORDER_AOI_SPEC.geometry_wkt)
    point_coordinates = {
        tuple(loads(feature.geometry_wkt).coords[0])
        for feature in UTILITY_DATASET_SPEC.features
        if feature.feature_type in {FeatureType.JUNCTION, FeatureType.DEVICE}
    }

    assert list(line.coords) == [
        (65.520, 44.820),
        (65.525, 44.8205),
        (65.530, 44.820),
    ]
    assert tuple(line.coords[0]) == tuple(loads(by_code["J-003"].geometry_wkt).coords[0])
    assert tuple(line.coords[-1]) == tuple(loads(by_code["J-004"].geometry_wkt).coords[0])
    assert tuple(line.coords[1]) not in point_coordinates
    assert aoi.covers(line)
    assert line.is_valid and line.is_simple and not line.is_empty
    assert Point(line.coords[1]).within(aoi)
    for coordinate in line.coords:
        for ordinate in coordinate:
            assert Decimal(str(ordinate)) % Decimal("0.0000001") == 0


def test_l003_keeps_expected_association_edges() -> None:
    by_id = {feature.id: feature.asset_code for feature in UTILITY_DATASET_SPEC.features}
    edges = {
        (by_id[item.from_feature_id], by_id[item.to_feature_id])
        for item in UTILITY_DATASET_SPEC.associations
        if "L-003" in {by_id[item.from_feature_id], by_id[item.to_feature_id]}
    }

    assert edges == {("D-002", "L-003"), ("D-003", "L-003")}


def test_editable_line_constants_reference_l003_spec() -> None:
    assert seed_specs.UTILITY_EDITABLE_LINE_ASSET_CODE == "L-003"
    assert seed_specs.UTILITY_EDITABLE_LINE_SPEC.asset_code == "L-003"
    assert seed_specs.UTILITY_EDITABLE_LINE_SPEC in UTILITY_DATASET_SPEC.features
