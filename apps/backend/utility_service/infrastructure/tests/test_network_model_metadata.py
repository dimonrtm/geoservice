from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.orm import configure_mappers

from utility_service.infrastructure.postgresql.models.utility_network import (
    AOI,
    AssociationType,
    Feeder,
    FeatureType,
    NetworkAssociation,
    NetworkFeature,
)


def constraint_names(model: type) -> set[str]:
    return {
        constraint.name for constraint in model.__table__.constraints if constraint.name is not None
    }


def test_utility_network_package_exports_public_contract() -> None:
    from utility_service.infrastructure.postgresql.models import utility_network

    assert set(utility_network.__all__) == {
        "AOI",
        "AssociationType",
        "Feeder",
        "FeatureType",
        "NetworkAssociation",
        "NetworkFeature",
    }


def test_aoi_metadata_contains_geometry_guards() -> None:
    assert AOI.__tablename__ == "aois"
    assert AOI.__table__.schema == "utility_network"
    assert {column.name for column in AOI.__table__.columns} == {
        "id",
        "name",
        "description",
        "geometry",
        "created_at",
        "updated_at",
    }
    assert {
        "ck_aois_geometry_not_empty",
        "ck_aois_geometry_valid",
        "ck_aois_geometry_srid",
        "ck_aois_geometry_type",
    }.issubset(constraint_names(AOI))


def test_aoi_declares_exactly_one_spatial_index() -> None:
    indexes = [
        index
        for index in AOI.__table__.indexes
        if tuple(column.name for column in index.columns) == ("geometry",)
    ]

    assert len(indexes) == 1
    assert indexes[0].name == "ix_aois_geometry"
    assert indexes[0].dialect_options["postgresql"]["using"] == "gist"
    assert AOI.__table__.c.geometry.type.spatial_index is False


def test_feeder_metadata_contains_defaults_and_unique_code() -> None:
    assert Feeder.__tablename__ == "feeders"
    assert Feeder.__table__.schema == "utility_network"
    assert Feeder.__table__.c.is_active.default.arg is True
    assert str(Feeder.__table__.c.is_active.server_default.arg) == "true"
    assert any(
        isinstance(constraint, UniqueConstraint)
        and tuple(column.name for column in constraint.columns) == ("code",)
        for constraint in Feeder.__table__.constraints
    )


def test_feature_type_values_are_stable_strings() -> None:
    assert {item.value for item in FeatureType} == {
        "junction",
        "line",
        "device",
    }


def test_network_feature_metadata_contains_aggregate_guards() -> None:
    assert NetworkFeature.__tablename__ == "network_features"
    assert NetworkFeature.__table__.schema == "utility_network"
    assert NetworkFeature.__table__.c.properties.default.is_callable is True
    assert NetworkFeature.__table__.c.version.default.arg == 1
    assert str(NetworkFeature.__table__.c.version.server_default.arg) == "1"
    assert {
        "fk_network_features_feeder",
        "uq_network_features_feeder_asset_code",
        "uq_network_features_feeder_id_id",
        "ck_network_features_geometry_not_empty",
        "ck_network_features_geometry_valid",
        "ck_network_features_geometry_srid",
        "ck_network_features_geometry_matches_type",
        "ck_network_features_version_positive",
    }.issubset(constraint_names(NetworkFeature))


def test_network_feature_has_schema_qualified_restrict_foreign_key() -> None:
    foreign_keys = [
        constraint
        for constraint in NetworkFeature.__table__.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]

    assert len(foreign_keys) == 1
    assert {element.ondelete for constraint in foreign_keys for element in constraint.elements} == {
        "RESTRICT"
    }
    assert {
        element.target_fullname for constraint in foreign_keys for element in constraint.elements
    } == {"utility_network.feeders.id"}


def test_network_feature_declares_exactly_one_spatial_index() -> None:
    indexes = [
        index
        for index in NetworkFeature.__table__.indexes
        if tuple(column.name for column in index.columns) == ("geometry",)
    ]

    assert len(indexes) == 1
    assert indexes[0].name == "ix_network_features_geometry"
    assert indexes[0].dialect_options["postgresql"]["using"] == "gist"
    assert NetworkFeature.__table__.c.geometry.type.spatial_index is False


def test_association_type_values_are_stable_strings() -> None:
    assert {item.value for item in AssociationType} == {
        "connectivity",
        "containment",
        "attachment",
    }


def test_network_association_metadata_contains_all_guards() -> None:
    assert NetworkAssociation.__table__.schema == "utility_network"
    assert {
        "fk_network_associations_feeder",
        "fk_network_associations_from_feature",
        "fk_network_associations_to_feature",
        "uq_network_associations_directed_edge",
        "ck_network_associations_no_self_reference",
        "ck_network_associations_version_positive",
    }.issubset(constraint_names(NetworkAssociation))


def test_network_association_foreign_keys_are_schema_qualified_and_restrict() -> None:
    foreign_keys = [
        constraint
        for constraint in NetworkAssociation.__table__.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]

    assert len(foreign_keys) == 3
    assert {element.ondelete for constraint in foreign_keys for element in constraint.elements} == {
        "RESTRICT"
    }
    assert {
        element.target_fullname for constraint in foreign_keys for element in constraint.elements
    } == {
        "utility_network.feeders.id",
        "utility_network.network_features.feeder_id",
        "utility_network.network_features.id",
    }


def test_network_relationships_do_not_delete_children_in_orm() -> None:
    configure_mappers()

    assert "delete" not in Feeder.features.property.cascade
    assert "delete" not in Feeder.associations.property.cascade
    assert NetworkFeature.outgoing_associations.property.viewonly is True
    assert NetworkFeature.incoming_associations.property.viewonly is True


def test_check_constraints_are_named() -> None:
    checks = [
        constraint
        for model in (AOI, NetworkFeature, NetworkAssociation)
        for constraint in model.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    ]

    assert checks
    assert all(constraint.name for constraint in checks)
