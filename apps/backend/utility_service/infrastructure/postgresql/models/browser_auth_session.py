from __future__ import annotations

import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Index, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class BrowserAuthSession(Base):
    __tablename__ = "browser_auth_sessions"
    __table_args__ = (
        UniqueConstraint(
            "id",
            "user_id",
            name="uq_browser_auth_sessions_id_user_id",
        ),
        Index(
            "ix_browser_auth_sessions_user_id",
            "user_id",
        ),
        Index(
            "ix_browser_auth_sessions_expires_at",
            "expires_at",
        ),
        {"schema": "user"},
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
