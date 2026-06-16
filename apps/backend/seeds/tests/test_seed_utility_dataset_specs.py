from uuid import UUID

from utility_service.infrastructure.postgresql.models.utility_network import (
    AssociationType,
    FeatureType,
)
from seeds.specs.seed_utility_dataset_specs import (
    UTILITY_DATASET_SPEC,
    UTILITY_FEEDER_CODE,
    UTILITY_FEEDER_ID,
)


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
