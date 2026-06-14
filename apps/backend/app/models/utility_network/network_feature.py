from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from geoalchemy2 import Geometry
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.utility_network.feeder import Feeder
    from models.utility_network.network_association import NetworkAssociation


class FeatureType(str, enum.Enum):
    JUNCTION = "junction"
    LINE = "line"
    DEVICE = "device"


class NetworkFeature(Base):
    __tablename__ = "network_features"
    __table_args__ = (
        UniqueConstraint(
            "feeder_id",
            "asset_code",
            name="uq_network_features_feeder_asset_code",
        ),
        UniqueConstraint(
            "feeder_id",
            "id",
            name="uq_network_features_feeder_id_id",
        ),
        CheckConstraint(
            "NOT ST_IsEmpty(geometry)",
            name="ck_network_features_geometry_not_empty",
        ),
        CheckConstraint(
            "ST_IsValid(geometry)",
            name="ck_network_features_geometry_valid",
        ),
        CheckConstraint(
            "ST_SRID(geometry) = 4326",
            name="ck_network_features_geometry_srid",
        ),
        CheckConstraint(
            "("
            "(feature_type IN ('junction', 'device') "
            "AND GeometryType(geometry) = 'POINT') "
            "OR "
            "(feature_type = 'line' "
            "AND GeometryType(geometry) = 'LINESTRING')"
            ")",
            name="ck_network_features_geometry_matches_type",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_network_features_version_positive",
        ),
        Index(
            "ix_network_features_geometry",
            "geometry",
            postgresql_using="gist",
        ),
        {"schema": "utility_network"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    feeder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "utility_network.feeders.id",
            name="fk_network_features_feeder",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    asset_code: Mapped[str] = mapped_column(String(100), nullable=False)
    feature_type: Mapped[FeatureType] = mapped_column(
        SAEnum(
            FeatureType,
            name="network_feature_type",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            values_callable=lambda enum_class: [item.value for item in enum_class],
            length=16,
        ),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    feeder: Mapped[Feeder] = relationship(back_populates="features")
    outgoing_associations: Mapped[list[NetworkAssociation]] = relationship(
        foreign_keys=("[NetworkAssociation.feeder_id, " "NetworkAssociation.from_feature_id]"),
        viewonly=True,
    )
    incoming_associations: Mapped[list[NetworkAssociation]] = relationship(
        foreign_keys=("[NetworkAssociation.feeder_id, " "NetworkAssociation.to_feature_id]"),
        viewonly=True,
    )
