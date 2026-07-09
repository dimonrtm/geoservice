from __future__ import annotations

import enum
import uuid
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import (
    CheckConstraint,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from utility_service.infrastructure.postgresql.models.base import Base
from utility_service.infrastructure.postgresql.models.utility_network.network_feature import (
    FeatureType,
)
from utility_service.infrastructure.postgresql.models.work_order.edit_version import EditVersion


class EditVersionOperationState(str, enum.Enum):
    UNCHANGED = "unchanged"
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"


class EditVersionFeature(Base):
    __tablename__ = "edit_version_features"
    __table_args__ = (
        Index("ix_edit_version_features_geometry", "geometry", postgresql_using="gist"),
        UniqueConstraint(
            "edit_version_id",
            "asset_code",
            name="uq_edit_version_features_edit_version_asset_code",
        ),
        UniqueConstraint(
            "edit_version_id",
            "feature_id",
            name="uq_edit_version_features_edit_version_id_feature_id",
        ),
        CheckConstraint(
            "NOT ST_IsEmpty(geometry)",
            name="ck_edit_version_features_geometry_not_empty",
        ),
        CheckConstraint(
            "ST_IsValid(geometry)",
            name="ck_edit_version_features_geometry_valid",
        ),
        CheckConstraint(
            "ST_SRID(geometry) = 4326",
            name="ck_edit_version_features_geometry_srid",
        ),
        CheckConstraint(
            "("
            "(feature_type IN ('junction', 'device') "
            "AND GeometryType(geometry) = 'POINT') "
            "OR "
            "(feature_type = 'line' "
            "AND GeometryType(geometry) = 'LINESTRING')"
            ")",
            name="ck_edit_version_features_geometry_matches_type",
        ),
        CheckConstraint(
            "network_version >= 1",
            name="ck_edit_version_features_network_version_positive",
        ),
        CheckConstraint(
            "operation IN ('unchanged', 'created', 'updated', 'deleted')",
            name="ck_edit_version_features_operation",
        ),
        {"schema": "work_order"},
    )

    edit_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "work_order.edit_versions.id",
            name="fk_edit_version_features_edit_version",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    feature_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    asset_code: Mapped[str] = mapped_column(String(100), nullable=False)
    feature_type: Mapped[FeatureType] = mapped_column(
        SAEnum(
            FeatureType,
            name="edit_version_feature_type",
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda enum_class: [item.value for item in enum_class],
            length=16,
        ),
        nullable=False,
    )
    geometry: Mapped[object] = mapped_column(
        Geometry(
            geometry_type="GEOMETRY",
            srid=4326,
            spatial_index=False,
        ),
        nullable=False,
    )
    properties: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    network_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    operation: Mapped[EditVersionOperationState] = mapped_column(
        SAEnum(
            EditVersionOperationState,
            name="edit_version_operation_state",
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda enum_class: [item.value for item in enum_class],
            length=16,
        ),
        nullable=False,
        default=EditVersionOperationState.UNCHANGED,
        server_default=EditVersionOperationState.UNCHANGED.value,
    )

    edit_version: Mapped[EditVersion] = relationship()
