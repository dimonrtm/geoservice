from __future__ import annotations

import enum
import uuid
from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    Integer,
    PrimaryKeyConstraint,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from utility_service.infrastructure.postgresql.models.base import Base


class EditVersionChangeEventType(str, enum.Enum):
    CHANGE_SET_PERSISTED = "change_set_persisted"
    CHANGE_SET_CLEARED = "change_set_cleared"


class EditVersionChangeEvent(Base):
    __tablename__ = "edit_version_change_events"
    __table_args__ = (
        PrimaryKeyConstraint(
            "command_id",
            name="pk_edit_version_change_events",
        ),
        UniqueConstraint(
            "edit_version_id",
            "draft_revision_after",
            name="uq_ev_events_version_revision",
        ),
        CheckConstraint(
            "event_type IN ('change_set_persisted','change_set_cleared')",
            name="ck_ev_events_type",
        ),
        CheckConstraint(
            "base_network_revision >= 1",
            name="ck_ev_events_base_revision",
        ),
        CheckConstraint(
            """draft_revision_before >= 1 AND draft_revision_after > draft_revision_before
            AND draft_revision_after - draft_revision_before = 1""",
            name="ck_ev_events_draft_revisions",
        ),
        CheckConstraint(
            """NOT ST_IsEmpty(before_geometry) AND ST_IsValid(before_geometry)
            AND ST_IsSimple(before_geometry)""",
            name="ck_ev_events_before_geometry",
        ),
        CheckConstraint(
            """NOT ST_IsEmpty(after_geometry) AND ST_IsValid(after_geometry)
            AND ST_IsSimple(after_geometry)""",
            name="ck_ev_events_after_geometry",
        ),
        CheckConstraint(
            "ST_AsEWKB(before_geometry) <> ST_AsEWKB(after_geometry)",
            name="ck_ev_events_geometry_changed",
        ),
        {
            "schema": "work_order",
        },
    )

    command_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
    )
    edit_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    work_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    default_state_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    feature_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    actor_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    event_type: Mapped[EditVersionChangeEventType] = mapped_column(
        SAEnum(
            EditVersionChangeEventType,
            name="edit_version_change_event_type",
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda enum_class: [item.value for item in enum_class],
            length=32,
        ),
        nullable=False,
    )
    before_geometry: Mapped[object] = mapped_column(
        Geometry(
            "LINESTRING",
            srid=4326,
            spatial_index=False,
        ),
        nullable=False,
    )
    after_geometry: Mapped[object] = mapped_column(
        Geometry(
            "LINESTRING",
            srid=4326,
            spatial_index=False,
        ),
        nullable=False,
    )
    base_network_revision: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    draft_revision_before: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    draft_revision_after: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
