from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from utility_service.infrastructure.postgresql.models.base import Base


class WorkOrderStatus(str, enum.Enum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"


class WorkOrder(Base):
    __tablename__ = "work_orders"
    __table_args__ = (
        UniqueConstraint("code", name="uq_work_orders_code"),
        CheckConstraint(
            "status IN ('assigned', 'in_progress')",
            name="ck_work_orders_status",
        ),
        Index("ix_work_orders_assignee_id", "assignee_id"),
        Index("ix_work_orders_status", "status"),
        Index("ix_work_orders_aoi_id", "aoi_id"),
        Index("ix_work_orders_feeder_id", "feeder_id"),
        {"schema": "utility_network"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[WorkOrderStatus] = mapped_column(
        SAEnum(
            WorkOrderStatus,
            name="work_order_status",
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda enum_class: [item.value for item in enum_class],
            length=16,
        ),
        nullable=False,
        default=WorkOrderStatus.ASSIGNED,
        server_default=WorkOrderStatus.ASSIGNED.value,
    )
    assignee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            name="fk_work_orders_assignee",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    aoi_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "utility_network.aois.id",
            name="fk_work_orders_aoi",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    feeder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "utility_network.feeders.id",
            name="fk_work_orders_feeder",
            ondelete="RESTRICT",
        ),
        nullable=False,
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

    aoi = relationship("AOI")
    feeder = relationship("Feeder")
