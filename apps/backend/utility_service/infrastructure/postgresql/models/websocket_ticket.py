from __future__ import annotations

import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKeyConstraint, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class WebSocketTicket(Base):
    __tablename__ = "websocket_tickets"
    __table_args__ = (
        ForeignKeyConstraint(
            ["browser_session_id", "user_id"],
            ["user.browser_auth_sessions.id", "user.browser_auth_sessions.user_id"],
            name="fk_websocket_tickets_browser_session_owner",
        ),
        UniqueConstraint("ticket_hash", name="uq_websocket_tickets_ticket_hash"),
        Index("ix_websocket_tickets_expires_at", "expires_at"),
        Index(
            "ix_websocket_tickets_browser_session_id",
            "browser_session_id",
        ),
        {"schema": "user"},
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    ticket_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    browser_session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    layer_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
