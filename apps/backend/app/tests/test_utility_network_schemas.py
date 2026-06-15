from uuid import UUID

from models.utility_network import AssociationType
from schemas.utility_network import (
    UtilityAssociationOut,
    UtilityFeatureCollectionOut,
    UtilityFeederOut,
)


def test_utility_schema_package_exports_and_serializes_wire_aliases() -> None:
    feeder_id = UUID("6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0101")
    from_id = UUID("6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0221")
    to_id = UUID("6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0211")
    association = UtilityAssociationOut(
        id=UUID("6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0301"),
        from_feature_id=from_id,
        to_feature_id=to_id,
        association_type=AssociationType.CONNECTIVITY,
        version=1,
    )
    response = UtilityFeederOut(
        id=feeder_id,
        code="synthetic_utility_feeder_01",
        name="Демонстрационный фидер 10 кВ",
        is_active=True,
        aois=UtilityFeatureCollectionOut(features=[]),
        network=UtilityFeatureCollectionOut(features=[]),
        associations=[association],
    )

    payload = response.model_dump(mode="json", by_alias=True)

    assert payload["isActive"] is True
    assert payload["associations"][0]["fromFeatureId"] == str(from_id)
    assert payload["associations"][0]["toFeatureId"] == str(to_id)
    assert payload["associations"][0]["associationType"] == "connectivity"
