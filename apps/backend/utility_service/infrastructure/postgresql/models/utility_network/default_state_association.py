from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    Enum as SAEnum,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from utility_service.infrastructure.postgresql.models.base import Base
from utility_service.infrastructure.postgresql.models.utility_network.default_state import (
    DefaultState,
)
from utility_service.infrastructure.postgresql.models.utility_network.network_association import (
    AssociationType,
)


class DefaultStateAssociation(Base):
    __tablename__ = "default_state_associations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["default_state_id", "from_feature_id"],
            [
                "utility_network.default_state_features.default_state_id",
                "utility_network.default_state_features.feature_id",
            ],
            name="fk_default_state_associations_from_feature",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["default_state_id", "to_feature_id"],
            [
                "utility_network.default_state_features.default_state_id",
                "utility_network.default_state_features.feature_id",
            ],
            name="fk_default_state_associations_to_feature",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "default_state_id",
            "association_id",
            name="uq_default_state_associations_default_state_id_association_id",
        ),
        UniqueConstraint(
            "default_state_id",
            "from_feature_id",
            "to_feature_id",
            "association_type",
            name="uq_default_state_associations_directed_edge",
        ),
        CheckConstraint(
            "from_feature_id <> to_feature_id",
            name="ck_default_state_associations_no_self_reference",
        ),
        CheckConstraint(
            "network_version >= 1",
            name="ck_default_state_associations_network_version_positive",
        ),
        {"schema": "utility_network"},
    )

    default_state_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "utility_network.default_states.id",
            name="fk_default_state_associations_default_state",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    association_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    association_type: Mapped[AssociationType] = mapped_column(
        SAEnum(
            AssociationType,
            name="default_state_association_type",
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda enum_class: [item.value for item in enum_class],
            length=16,
        ),
        nullable=False,
    )
    from_feature_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    to_feature_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
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
