from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKeyConstraint,
    Index,
    PrimaryKeyConstraint,
    SmallInteger,
    Text,
    false,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from utility_service.infrastructure.postgresql.models.base import Base


class EditVersionCommandState(str, enum.Enum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    REJECTED = "rejected"


class EditVersionCommand(Base):
    __tablename__ = "edit_version_commands"
    __table_args__ = (
        PrimaryKeyConstraint(
            "command_id",
            name="pk_edit_version_commands",
        ),
        ForeignKeyConstraint(
            ["edit_version_id"],
            ["work_order.edit_versions.id"],
            name="fk_ev_commands_edit_version",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["edit_version_id", "feature_id"],
            [
                "work_order.edit_version_features.edit_version_id",
                "work_order.edit_version_features.feature_id",
            ],
            name="fk_ev_commands_feature",
            ondelete="NO ACTION",
        ),
        CheckConstraint(
            "btrim(request_fingerprint) <> ''",
            name="ck_ev_commands_fingerprint",
        ),
        CheckConstraint(
            "state IN ('running','succeeded','rejected')",
            name="ck_ev_commands_state",
        ),
        CheckConstraint(
            """
            (state = 'running'
             AND response_status IS NULL AND response_payload IS NULL
             AND rejection_code IS NULL AND rejection_message IS NULL
             AND completed_at IS NULL AND NOT retry_on_access_change)
            OR
            (state = 'succeeded'
             AND response_status IS NOT NULL AND response_status BETWEEN 200 AND 299
             AND response_payload IS NOT NULL AND jsonb_typeof(response_payload) = 'object'
             AND rejection_code IS NULL AND rejection_message IS NULL
             AND completed_at IS NOT NULL AND NOT retry_on_access_change)
            OR
            (state = 'rejected'
             AND response_status IS NOT NULL AND response_status BETWEEN 400 AND 499
             AND response_payload IS NULL
             AND rejection_code IS NOT NULL AND btrim(rejection_code) <> ''
             AND rejection_message IS NOT NULL AND btrim(rejection_message) <> ''
             AND completed_at IS NOT NULL)
            """,
            name="ck_ev_commands_result",
        ),
        CheckConstraint(
            """
            NOT retry_on_access_change OR
            (state = 'rejected' AND response_status IS NOT NULL AND response_status = 404
             AND rejection_code IS NOT NULL AND rejection_code = 'EDIT_VERSION_NOT_FOUND')
            """,
            name="ck_ev_commands_access_retry",
        ),
        Index(
            "ix_ev_commands_version_feature",
            "edit_version_id",
            "feature_id",
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
    feature_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    actor_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    request_fingerprint: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    state: Mapped[EditVersionCommandState] = mapped_column(
        SAEnum(
            EditVersionCommandState,
            name="edit_version_command_state",
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda enum_class: [item.value for item in enum_class],
            length=16,
        ),
        nullable=False,
    )
    retry_on_access_change: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=false(),
    )
    response_status: Mapped[int | None] = mapped_column(
        SmallInteger,
        nullable=True,
    )
    response_payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB(none_as_null=True),
        nullable=True,
    )
    rejection_code: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    rejection_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
