from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.orm import configure_mappers

from utility_service.infrastructure.postgresql.models.utility_network import (
    AOI,
    AssociationType,
    DefaultState,
    EditVersion,
    EditVersionStatus,
    Feeder,
    FeatureType,
    NetworkAssociation,
    NetworkFeature,
    WorkOrder,
    WorkOrderStatus,
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
        "DefaultState",
        "EditVersion",
        "EditVersionStatus",
        "Feeder",
        "FeatureType",
        "NetworkAssociation",
        "NetworkFeature",
        "WorkOrder",
        "WorkOrderStatus",
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
        for model in (AOI, NetworkFeature, NetworkAssociation, WorkOrder, DefaultState, EditVersion)
        for constraint in model.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    ]

    assert checks
    assert all(constraint.name for constraint in checks)


def test_work_order_status_values_are_stable_strings() -> None:
    assert {item.value for item in WorkOrderStatus} == {
        "assigned",
        "in_progress",
    }


def test_work_order_metadata_contains_assignment_guards() -> None:
    assert WorkOrder.__tablename__ == "work_orders"
    assert WorkOrder.__table__.schema == "utility_network"
    assert {column.name for column in WorkOrder.__table__.columns} == {
        "id",
        "code",
        "title",
        "description",
        "status",
        "assignee_id",
        "aoi_id",
        "feeder_id",
        "created_at",
        "updated_at",
    }
    assert {
        "uq_work_orders_code",
        "ck_work_orders_status",
    }.issubset(constraint_names(WorkOrder))
    assert any(
        isinstance(constraint, UniqueConstraint)
        and tuple(column.name for column in constraint.columns) == ("code",)
        for constraint in WorkOrder.__table__.constraints
    )


def test_work_order_foreign_keys_are_restrictive_and_schema_qualified() -> None:
    foreign_keys = [
        constraint
        for constraint in WorkOrder.__table__.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]

    assert len(foreign_keys) == 3
    assert {element.ondelete for constraint in foreign_keys for element in constraint.elements} == {
        "RESTRICT"
    }
    assert {
        element.target_fullname for constraint in foreign_keys for element in constraint.elements
    } == {
        "users.id",
        "utility_network.aois.id",
        "utility_network.feeders.id",
    }


def test_work_order_declares_lookup_indexes() -> None:
    indexes = {
        index.name: tuple(column.name for column in index.columns)
        for index in WorkOrder.__table__.indexes
    }

    assert indexes == {
        "ix_work_orders_assignee_id": ("assignee_id",),
        "ix_work_orders_status": ("status",),
        "ix_work_orders_aoi_id": ("aoi_id",),
        "ix_work_orders_feeder_id": ("feeder_id",),
    }


def test_default_state_metadata_contains_singleton_revision_guards() -> None:
    assert DefaultState.__tablename__ == "default_states"
    assert DefaultState.__table__.schema == "utility_network"
    assert {column.name for column in DefaultState.__table__.columns} == {
        "id",
        "name",
        "current_revision",
        "created_at",
        "updated_at",
    }
    assert DefaultState.__table__.c.current_revision.default.arg == 1
    assert str(DefaultState.__table__.c.current_revision.server_default.arg) == "1"
    assert {
        "uq_default_states_name",
        "ck_default_states_current_revision_positive",
    }.issubset(constraint_names(DefaultState))
    assert any(
        isinstance(constraint, UniqueConstraint)
        and tuple(column.name for column in constraint.columns) == ("name",)
        for constraint in DefaultState.__table__.constraints
    )


def test_edit_version_status_values_are_stable_strings() -> None:
    assert {item.value for item in EditVersionStatus} == {"open"}


def test_edit_version_metadata_contains_open_version_guards() -> None:
    assert EditVersion.__tablename__ == "edit_versions"
    assert EditVersion.__table__.schema == "utility_network"
    assert {column.name for column in EditVersion.__table__.columns} == {
        "id",
        "work_order_id",
        "owner_id",
        "base_revision",
        "status",
        "created_at",
        "last_opened_at",
    }
    assert EditVersion.__table__.c.base_revision.default.arg == 1
    assert str(EditVersion.__table__.c.base_revision.server_default.arg) == "1"
    assert {
        "ck_edit_versions_base_revision_positive",
        "ck_edit_versions_status",
    }.issubset(constraint_names(EditVersion))


def test_edit_version_foreign_keys_are_restrictive_and_schema_qualified() -> None:
    foreign_keys = [
        constraint
        for constraint in EditVersion.__table__.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]

    assert len(foreign_keys) == 2
    assert {element.ondelete for constraint in foreign_keys for element in constraint.elements} == {
        "RESTRICT"
    }
    assert {
        element.target_fullname for constraint in foreign_keys for element in constraint.elements
    } == {
        "users.id",
        "utility_network.work_orders.id",
    }


def test_edit_version_declares_partial_open_unique_index() -> None:
    indexes = {index.name: index for index in EditVersion.__table__.indexes}

    assert "uq_edit_versions_open_work_order" in indexes
    index = indexes["uq_edit_versions_open_work_order"]
    assert tuple(column.name for column in index.columns) == ("work_order_id",)
    assert index.unique is True
    assert str(index.dialect_options["postgresql"]["where"]) == "status = 'open'"
