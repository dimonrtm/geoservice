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
from utility_service.infrastructure.postgresql.models.utility_network.network_association import (
    AssociationType,
)
from utility_service.infrastructure.postgresql.models.work_order.edit_version import EditVersion
from utility_service.infrastructure.postgresql.models.work_order.edit_version_feature import (
    EditVersionOperationState,
)


class EditVersionAssociation(Base):
    __tablename__ = "edit_version_associations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["edit_version_id", "from_feature_id"],
            [
                "work_order.edit_version_features.edit_version_id",
                "work_order.edit_version_features.feature_id",
            ],
            name="fk_edit_version_associations_from_feature",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["edit_version_id", "to_feature_id"],
            [
                "work_order.edit_version_features.edit_version_id",
                "work_order.edit_version_features.feature_id",
            ],
            name="fk_edit_version_associations_to_feature",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "edit_version_id",
            "association_id",
            name="uq_edit_version_associations_edit_version_id_association_id",
        ),
        UniqueConstraint(
            "edit_version_id",
            "from_feature_id",
            "to_feature_id",
            "association_type",
            name="uq_edit_version_associations_directed_edge",
        ),
        CheckConstraint(
            "from_feature_id <> to_feature_id",
            name="ck_edit_version_associations_no_self_reference",
        ),
        CheckConstraint(
            "network_version >= 1",
            name="ck_edit_version_associations_network_version_positive",
        ),
        CheckConstraint(
            "operation IN ('unchanged', 'created', 'updated', 'deleted')",
            name="ck_edit_version_associations_operation",
        ),
        {"schema": "work_order"},
    )

    edit_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "work_order.edit_versions.id",
            name="fk_edit_version_associations_edit_version",
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
            name="edit_version_association_type",
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
