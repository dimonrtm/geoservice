from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from utility_service.infrastructure.postgresql.models.base import Base

if TYPE_CHECKING:
    from utility_service.infrastructure.postgresql.models.work_order.work_order import (
        WorkOrder,
    )


class EditVersionStatus(str, enum.Enum):
    OPEN = "open"


class EditVersion(Base):
    __tablename__ = "edit_versions"
    __table_args__ = (
        CheckConstraint(
            """
            geometry_xy_resolution NOT IN (
                'NaN'::numeric,
                'Infinity'::numeric,
                '-Infinity'::numeric
            )
            AND geometry_xy_resolution BETWEEN 0.0000001 AND 360
            AND geometry_xy_resolution * 1000000000
                = trunc(geometry_xy_resolution * 1000000000)
            """,
            name="ck_edit_versions_geometry_grid",
        ),
        CheckConstraint(
            "geometry_rounding_mode = 'ROUND_HALF_AWAY_FROM_ZERO'",
            name="ck_edit_versions_geometry_rounding",
        ),
        CheckConstraint(
            "geometry_policy_version = 1",
            name="ck_edit_versions_geometry_policy_version",
        ),
        CheckConstraint(
            "draft_revision >= 1",
            name="ck_edit_versions_draft_revision_positive",
        ),
        CheckConstraint(
            "base_network_revision >= 1",
            name="ck_edit_versions_base_network_revision_positive",
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
        {
            "schema": "work_order",
        },
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    work_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "work_order.work_orders.id",
            name="fk_edit_versions_work_order",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    default_state_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    draft_revision: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default="1",
    )
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    base_network_revision: Mapped[int] = mapped_column(
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

    geometry_xy_resolution: Mapped[Decimal] = mapped_column(
        Numeric(),
        nullable=False,
    )
    geometry_rounding_mode: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    geometry_policy_version: Mapped[int] = mapped_column(
        SmallInteger(),
        nullable=False,
    )

    work_order: Mapped[WorkOrder] = relationship()
