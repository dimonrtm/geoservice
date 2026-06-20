from __future__ import annotations

import uuid
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import (
    CheckConstraint,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from utility_service.infrastructure.postgresql.models.base import Base
from utility_service.infrastructure.postgresql.models.utility_network.default_state import (
    DefaultState,
)
from utility_service.infrastructure.postgresql.models.utility_network.network_feature import (
    FeatureType,
)


class DefaultStateFeature(Base):
    __tablename__ = "default_state_features"
    __table_args__ = (
        UniqueConstraint(
            "default_state_id",
            "asset_code",
            name="uq_default_state_features_default_state_asset_code",
        ),
        UniqueConstraint(
            "default_state_id",
            "feature_id",
            name="uq_default_state_features_default_state_id_feature_id",
        ),
        CheckConstraint(
            "NOT ST_IsEmpty(geometry)",
            name="ck_default_state_features_geometry_not_empty",
        ),
        CheckConstraint(
            "ST_IsValid(geometry)",
            name="ck_default_state_features_geometry_valid",
        ),
        CheckConstraint(
            "ST_SRID(geometry) = 4326",
            name="ck_default_state_features_geometry_srid",
        ),
        CheckConstraint(
            "("
            "(feature_type IN ('junction', 'device') "
            "AND GeometryType(geometry) = 'POINT') "
            "OR "
            "(feature_type = 'line' "
            "AND GeometryType(geometry) = 'LINESTRING')"
            ")",
            name="ck_default_state_features_geometry_matches_type",
        ),
        CheckConstraint(
            "network_version >= 1",
            name="ck_default_state_features_network_version_positive",
        ),
        {"schema": "utility_network"},
    )

    default_state_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "utility_network.default_states.id",
            name="fk_default_state_features_default_state",
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
            name="default_state_feature_type",
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

    default_state: Mapped[DefaultState] = relationship()
