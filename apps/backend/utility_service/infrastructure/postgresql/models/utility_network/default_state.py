from __future__ import annotations

import uuid
import enum
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from utility_service.infrastructure.postgresql.models.base import Base
from utility_service.infrastructure.postgresql.models.utility_network.network_state import (
    NetworkState,
)


class DefaultStateStatus(str, enum.Enum):
    ACTIVE = "active"


class DefaultState(Base):
    __tablename__ = "default_states"
    __table_args__ = (
        UniqueConstraint("work_order_id", name="uq_default_states_work_order"),
        CheckConstraint(
            "base_network_revision >= 1",
            name="ck_default_states_base_network_revision_positive",
        ),
        CheckConstraint(
            "status IN ('active')",
            name="ck_default_states_status",
        ),
        {"schema": "utility_network"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    work_order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    network_state_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "utility_network.network_states.id",
            name="fk_default_states_network_state",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    base_network_revision: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    status: Mapped[DefaultStateStatus] = mapped_column(
        SAEnum(
            DefaultStateStatus,
            name="default_state_status",
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda enum_class: [item.value for item in enum_class],
            length=16,
        ),
        nullable=False,
        default=DefaultStateStatus.ACTIVE,
        server_default=DefaultStateStatus.ACTIVE.value,
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

    network_state: Mapped[NetworkState] = relationship()
