from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from utility_service.infrastructure.postgresql.models.base import Base

if TYPE_CHECKING:
    from .feeder import Feeder
    from .network_feature import NetworkFeature


class AssociationType(str, enum.Enum):
    CONNECTIVITY = "connectivity"
    CONTAINMENT = "containment"
    ATTACHMENT = "attachment"


class NetworkAssociation(Base):
    __tablename__ = "network_associations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["feeder_id", "from_feature_id"],
            [
                "utility_network.network_features.feeder_id",
                "utility_network.network_features.id",
            ],
            name="fk_network_associations_from_feature",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["feeder_id", "to_feature_id"],
            [
                "utility_network.network_features.feeder_id",
                "utility_network.network_features.id",
            ],
            name="fk_network_associations_to_feature",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "feeder_id",
            "from_feature_id",
            "to_feature_id",
            "association_type",
            name="uq_network_associations_directed_edge",
        ),
        CheckConstraint(
            "from_feature_id <> to_feature_id",
            name="ck_network_associations_no_self_reference",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_network_associations_version_positive",
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
            name="fk_network_associations_feeder",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    association_type: Mapped[AssociationType] = mapped_column(
        SAEnum(
            AssociationType,
            name="network_association_type",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            values_callable=lambda enum_class: [item.value for item in enum_class],
            length=16,
        ),
        nullable=False,
    )
    from_feature_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    to_feature_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
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

    feeder: Mapped[Feeder] = relationship(back_populates="associations")
    from_feature: Mapped[NetworkFeature] = relationship(
        foreign_keys=[feeder_id, from_feature_id],
        viewonly=True,
    )
    to_feature: Mapped[NetworkFeature] = relationship(
        foreign_keys=[feeder_id, to_feature_id],
        viewonly=True,
    )
