from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.orm import configure_mappers

from utility_service.infrastructure.postgresql.models.user import User
from utility_service.infrastructure.postgresql.models.utility_network import (
    AssociationType,
    DefaultState,
    DefaultStateAssociation,
    DefaultStateFeature,
    DefaultStateStatus,
    Feeder,
    FeatureType,
    NetworkAssociation,
    NetworkFeature,
    NetworkState,
)
from utility_service.infrastructure.postgresql.models.work_order import (
    AOI,
    EditVersion,
    EditVersionAssociation,
    EditVersionFeature,
    EditVersionStatus,
    WorkOrder,
    WorkOrderStatus,
)


def constraint_names(model: type) -> set[str]:
    return {
        constraint.name for constraint in model.__table__.constraints if constraint.name is not None
    }


def foreign_key_targets(model: type) -> set[str]:
    return {
        element.target_fullname
        for constraint in model.__table__.constraints
        if isinstance(constraint, ForeignKeyConstraint)
        for element in constraint.elements
    }


def test_utility_network_package_exports_public_contract() -> None:
    from utility_service.infrastructure.postgresql.models import utility_network

    assert set(utility_network.__all__) == {
        "AssociationType",
        "DefaultState",
        "DefaultStateAssociation",
        "DefaultStateFeature",
        "DefaultStateStatus",
        "Feeder",
        "FeatureType",
        "NetworkAssociation",
        "NetworkFeature",
        "NetworkState",
    }


def test_work_order_package_exports_public_contract() -> None:
    from utility_service.infrastructure.postgresql.models import work_order

    assert set(work_order.__all__) == {
        "AOI",
        "EditVersion",
        "EditVersionAssociation",
        "EditVersionFeature",
        "EditVersionStatus",
        "WorkOrder",
        "WorkOrderStatus",
    }


def test_user_model_uses_user_schema() -> None:
    assert User.__tablename__ == "users"
    assert User.__table__.schema == "user"


def test_work_order_models_use_work_order_schema() -> None:
    assert AOI.__table__.schema == "work_order"
    assert WorkOrder.__table__.schema == "work_order"
    assert EditVersion.__table__.schema == "work_order"
    assert EditVersionFeature.__table__.schema == "work_order"
    assert EditVersionAssociation.__table__.schema == "work_order"


def test_new_utility_baseline_models_use_utility_network_schema() -> None:
    assert NetworkState.__table__.schema == "utility_network"
    assert DefaultState.__table__.schema == "utility_network"
    assert DefaultStateFeature.__table__.schema == "utility_network"
    assert DefaultStateAssociation.__table__.schema == "utility_network"


def test_work_order_has_no_cross_schema_foreign_keys() -> None:
    assert foreign_key_targets(WorkOrder) == {"work_order.aois.id"}
    assert foreign_key_targets(EditVersion) == {"work_order.work_orders.id"}
    assert foreign_key_targets(EditVersionFeature) == {"work_order.edit_versions.id"}
    assert foreign_key_targets(EditVersionAssociation) == {
        "work_order.edit_versions.id",
        "work_order.edit_version_features.edit_version_id",
        "work_order.edit_version_features.feature_id",
    }


def test_default_state_uses_plain_work_order_reference() -> None:
    assert "work_order_id" in DefaultState.__table__.c
    assert "work_order.work_orders.id" not in foreign_key_targets(DefaultState)


def test_work_order_aoi_metadata_contains_geometry_guards() -> None:
    assert AOI.__tablename__ == "aois"
    assert AOI.__table__.schema == "work_order"
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
        for model in (
            AOI,
            NetworkFeature,
            NetworkAssociation,
            NetworkState,
            DefaultState,
            DefaultStateFeature,
            DefaultStateAssociation,
            WorkOrder,
            EditVersion,
            EditVersionFeature,
            EditVersionAssociation,
        )
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


def test_work_order_metadata_contains_aggregate_guards() -> None:
    assert WorkOrder.__tablename__ == "work_orders"
    assert WorkOrder.__table__.schema == "work_order"
    assert {column.name for column in WorkOrder.__table__.columns} == {
        "id",
        "code",
        "title",
        "description",
        "status",
        "aoi_id",
        "assignee_user_id",
        "created_by_user_id",
        "created_at",
        "updated_at",
    }
    assert WorkOrder.__table__.c.aoi_id.nullable is False
    assert {
        "uq_work_orders_code",
        "fk_work_orders_aoi",
        "ck_work_orders_status",
    }.issubset(constraint_names(WorkOrder))
    assert any(
        isinstance(constraint, UniqueConstraint)
        and tuple(column.name for column in constraint.columns) == ("code",)
        for constraint in WorkOrder.__table__.constraints
    )


def test_work_order_declares_lookup_indexes() -> None:
    indexes = {
        index.name: tuple(column.name for column in index.columns)
        for index in WorkOrder.__table__.indexes
    }

    assert indexes == {
        "ix_work_orders_aoi_id": ("aoi_id",),
        "ix_work_orders_assignee_user_id": ("assignee_user_id",),
        "ix_work_orders_created_by_user_id": ("created_by_user_id",),
        "ix_work_orders_status": ("status",),
    }


def test_network_state_metadata_contains_current_revision_guards() -> None:
    assert NetworkState.__tablename__ == "network_states"
    assert NetworkState.__table__.schema == "utility_network"
    assert {column.name for column in NetworkState.__table__.columns} == {
        "id",
        "name",
        "current_revision",
        "created_at",
        "updated_at",
    }
    assert NetworkState.__table__.c.current_revision.default.arg == 1
    assert str(NetworkState.__table__.c.current_revision.server_default.arg) == "1"
    assert {
        "uq_network_states_name",
        "ck_network_states_current_revision_positive",
    }.issubset(constraint_names(NetworkState))


def test_default_state_status_values_are_stable_strings() -> None:
    assert {item.value for item in DefaultStateStatus} == {"active"}


def test_default_state_metadata_contains_work_order_baseline_guards() -> None:
    assert DefaultState.__tablename__ == "default_states"
    assert DefaultState.__table__.schema == "utility_network"
    assert {column.name for column in DefaultState.__table__.columns} == {
        "id",
        "work_order_id",
        "network_state_id",
        "base_network_revision",
        "status",
        "created_at",
        "updated_at",
    }
    assert DefaultState.__table__.c.base_network_revision.default.arg == 1
    assert str(DefaultState.__table__.c.base_network_revision.server_default.arg) == "1"
    assert {
        "uq_default_states_work_order",
        "ck_default_states_base_network_revision_positive",
        "ck_default_states_status",
    }.issubset(constraint_names(DefaultState))
    assert any(
        isinstance(constraint, UniqueConstraint)
        and tuple(column.name for column in constraint.columns) == ("work_order_id",)
        for constraint in DefaultState.__table__.constraints
    )


def test_default_state_foreign_keys_stay_inside_utility_network() -> None:
    assert foreign_key_targets(DefaultState) == {"utility_network.network_states.id"}


def test_default_state_feature_metadata_preserves_future_network_ids() -> None:
    assert DefaultStateFeature.__tablename__ == "default_state_features"
    assert DefaultStateFeature.__table__.schema == "utility_network"
    assert {column.name for column in DefaultStateFeature.__table__.columns} == {
        "default_state_id",
        "feature_id",
        "asset_code",
        "feature_type",
        "geometry",
        "properties",
        "network_version",
    }
    assert {
        "fk_default_state_features_default_state",
        "uq_default_state_features_default_state_asset_code",
        "uq_default_state_features_default_state_id_feature_id",
        "ck_default_state_features_geometry_not_empty",
        "ck_default_state_features_geometry_valid",
        "ck_default_state_features_geometry_srid",
        "ck_default_state_features_geometry_matches_type",
        "ck_default_state_features_network_version_positive",
    }.issubset(constraint_names(DefaultStateFeature))


def test_default_state_association_metadata_preserves_future_network_ids() -> None:
    assert DefaultStateAssociation.__tablename__ == "default_state_associations"
    assert DefaultStateAssociation.__table__.schema == "utility_network"
    assert {column.name for column in DefaultStateAssociation.__table__.columns} == {
        "default_state_id",
        "association_id",
        "association_type",
        "from_feature_id",
        "to_feature_id",
        "properties",
        "network_version",
    }
    assert {
        "fk_default_state_associations_default_state",
        "fk_default_state_associations_from_feature",
        "fk_default_state_associations_to_feature",
        "uq_default_state_associations_default_state_id_association_id",
        "uq_default_state_associations_directed_edge",
        "ck_default_state_associations_no_self_reference",
        "ck_default_state_associations_network_version_positive",
    }.issubset(constraint_names(DefaultStateAssociation))


def test_edit_version_status_values_are_stable_strings() -> None:
    assert {item.value for item in EditVersionStatus} == {"open"}


def test_edit_version_metadata_contains_open_version_guards() -> None:
    assert EditVersion.__tablename__ == "edit_versions"
    assert EditVersion.__table__.schema == "work_order"
    assert {column.name for column in EditVersion.__table__.columns} == {
        "id",
        "work_order_id",
        "default_state_id",
        "owner_user_id",
        "base_network_revision",
        "status",
        "created_at",
        "last_opened_at",
    }
    assert EditVersion.__table__.c.base_network_revision.default.arg == 1
    assert str(EditVersion.__table__.c.base_network_revision.server_default.arg) == "1"
    assert {
        "ck_edit_versions_base_network_revision_positive",
        "ck_edit_versions_status",
    }.issubset(constraint_names(EditVersion))


def test_edit_version_foreign_keys_stay_inside_work_order_schema() -> None:
    foreign_keys = [
        constraint
        for constraint in EditVersion.__table__.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]

    assert len(foreign_keys) == 1
    assert {element.ondelete for constraint in foreign_keys for element in constraint.elements} == {
        "RESTRICT"
    }
    assert {
        element.target_fullname for constraint in foreign_keys for element in constraint.elements
    } == {"work_order.work_orders.id"}


def test_edit_version_declares_partial_open_unique_index() -> None:
    indexes = {index.name: index for index in EditVersion.__table__.indexes}

    assert "uq_edit_versions_open_work_order" in indexes
    index = indexes["uq_edit_versions_open_work_order"]
    assert tuple(column.name for column in index.columns) == ("work_order_id",)
    assert index.unique is True
    assert str(index.dialect_options["postgresql"]["where"]) == "status = 'open'"


def test_edit_version_feature_metadata_preserves_future_network_ids() -> None:
    assert EditVersionFeature.__tablename__ == "edit_version_features"
    assert EditVersionFeature.__table__.schema == "work_order"
    assert {column.name for column in EditVersionFeature.__table__.columns} == {
        "edit_version_id",
        "feature_id",
        "asset_code",
        "feature_type",
        "geometry",
        "properties",
        "network_version",
        "operation",
    }
    assert {
        "fk_edit_version_features_edit_version",
        "uq_edit_version_features_edit_version_asset_code",
        "uq_edit_version_features_edit_version_id_feature_id",
        "ck_edit_version_features_geometry_not_empty",
        "ck_edit_version_features_geometry_valid",
        "ck_edit_version_features_geometry_srid",
        "ck_edit_version_features_geometry_matches_type",
        "ck_edit_version_features_network_version_positive",
        "ck_edit_version_features_operation",
    }.issubset(constraint_names(EditVersionFeature))


def test_edit_version_feature_declares_exactly_one_spatial_index() -> None:
    indexes = [
        index
        for index in EditVersionFeature.__table__.indexes
        if tuple(column.name for column in index.columns) == ("geometry",)
    ]

    assert len(indexes) == 1
    assert indexes[0].name == "ix_edit_version_features_geometry"
    assert indexes[0].dialect_options["postgresql"]["using"] == "gist"
    assert EditVersionFeature.__table__.c.geometry.type.spatial_index is False


def test_edit_version_association_metadata_preserves_future_network_ids() -> None:
    assert EditVersionAssociation.__tablename__ == "edit_version_associations"
    assert EditVersionAssociation.__table__.schema == "work_order"
    assert {column.name for column in EditVersionAssociation.__table__.columns} == {
        "edit_version_id",
        "association_id",
        "association_type",
        "from_feature_id",
        "to_feature_id",
        "properties",
        "network_version",
        "operation",
    }
    assert {
        "fk_edit_version_associations_edit_version",
        "fk_edit_version_associations_from_feature",
        "fk_edit_version_associations_to_feature",
        "uq_edit_version_associations_edit_version_id_association_id",
        "uq_edit_version_associations_directed_edge",
        "ck_edit_version_associations_no_self_reference",
        "ck_edit_version_associations_network_version_positive",
        "ck_edit_version_associations_operation",
    }.issubset(constraint_names(EditVersionAssociation))


def test_edit_version_association_declares_to_feature_lookup_index() -> None:
    indexes = {
        index.name: tuple(column.name for column in index.columns)
        for index in EditVersionAssociation.__table__.indexes
    }

    assert indexes["ix_edit_version_associations_edit_version_to_feature_id"] == (
        "edit_version_id",
        "to_feature_id",
    )
