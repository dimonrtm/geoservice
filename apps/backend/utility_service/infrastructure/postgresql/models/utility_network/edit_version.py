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
    Index,
    Integer,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from utility_service.infrastructure.postgresql.models.base import Base

if TYPE_CHECKING:
    from utility_service.infrastructure.postgresql.models.utility_network.work_order import (
        WorkOrder,
    )


class EditVersionStatus(str, enum.Enum):
    OPEN = "open"


class EditVersion(Base):
    __tablename__ = "edit_versions"
    __table_args__ = (
        CheckConstraint(
            "base_revision >= 1",
            name="ck_edit_versions_base_revision_positive",
        ),
        CheckConstraint(
            "status IN ('open')",
            name="ck_edit_versions_status",
        ),
        Index(
            "uq_edit_versions_open_work_order",
            "work_order_id",
            unique=True,
            postgresql_where=text("status = 'open'"),
        ),
        {"schema": "utility_network"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    work_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "utility_network.work_orders.id",
            name="fk_edit_versions_work_order",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            name="fk_edit_versions_owner",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    base_revision: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    status: Mapped[EditVersionStatus] = mapped_column(
        SAEnum(
            EditVersionStatus,
            name="edit_version_status",
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda enum_class: [item.value for item in enum_class],
            length=16,
        ),
        nullable=False,
        default=EditVersionStatus.OPEN,
        server_default=EditVersionStatus.OPEN.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    last_opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    work_order: Mapped[WorkOrder] = relationship()
