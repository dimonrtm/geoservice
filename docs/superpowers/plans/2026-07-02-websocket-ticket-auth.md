# WebSocket Ticket Auth Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace WebSocket JWT query string auth with short-lived, DB-backed, single-use tickets while keeping existing HTTP Bearer auth unchanged.

**Architecture:** Backend issues layer-bound opaque tickets through an authenticated HTTP endpoint, stores only SHA-256 ticket hashes, and atomically consumes tickets during WebSocket handshake. Frontend requests a fresh ticket before every initial connect and reconnect, then opens `WS /api/v1/ws/layers/{layerId}?ticket=...` without passing JWT into realtime code.

**Tech Stack:** FastAPI, SQLAlchemy async, Alembic, PostgreSQL, Pydantic v2, Vue 3, Pinia, Axios, Vitest, pytest.

---

## Source Spec

- `docs/superpowers/specs/2026-07-02-websocket-ticket-auth-design.md`

## File Structure

Backend create:

- `apps/backend/utility_service/infrastructure/postgresql/models/websocket_ticket.py`: SQLAlchemy model for `"user".websocket_tickets`.
- `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/a6f4c9b8d2e1_websocket_tickets.py`: migration for the ticket table and indexes.
- `apps/backend/utility_service/infrastructure/postgresql/repositories/websocket_ticket_repository.py`: insert and atomic consume of hashed tickets.
- `apps/backend/utility_service/use_cases/services/websocket_ticket_service.py`: ticket generation, SHA-256 hashing, issue/consume rules, role/user validation.
- `apps/backend/utility_service/use_cases/domain/exceptions/websocket_ticket_error.py`: WebSocket ticket exception and shared invalid-ticket message.
- `apps/backend/utility_service/use_cases/schemas/realtime/__init__.py`: realtime schema package marker.
- `apps/backend/utility_service/use_cases/schemas/realtime/websocket_ticket_out.py`: HTTP response schema `{ticket, expiresAt}`.
- `apps/backend/utility_service/utils/websocket_ticket_auth.py`: WebSocket-specific ticket-to-`WebSocketUserContext` helper.
- `apps/backend/utility_service/use_cases/tests/test_websocket_ticket_service.py`: service-level ticket tests.

Backend modify:

- `apps/backend/utility_service/utils/settings.py`: add `WEBSOCKET_TICKET_TTL_SECONDS`.
- `apps/backend/utility_service/utils/tests/test_settings.py`: cover default and env override.
- `apps/backend/utility_service/infrastructure/postgresql/alembic/env.py`: import the new model for autogenerate metadata.
- `apps/backend/utility_service/use_cases/deps.py`: dependency factory for `WebSocketTicketService`.
- `apps/backend/utility_service/web_api/api/ws_layers.py`: add ticket issue endpoint and use ticket auth in the WebSocket route.
- `apps/backend/utility_service/web_api/tests/test_ws_layers.py`: update WebSocket tests from `token` to `ticket`; add issue/reuse/wrong auth tests.
- `apps/backend/utility_service/web_api/tests/test_websocket_auth.py`: delete after production code stops using `authenticate_websocket_token`.
- `apps/backend/utility_service/web_api/tests/test_websocket_auth_roles.py`: delete after production code stops using `authenticate_websocket_token`.

Frontend create:

- `apps/frontend/src/api/realtime.ts`: issue ticket through existing Axios `http` client.

Frontend modify:

- `apps/frontend/src/composables/map/useLayerRealtime.ts`: remove JWT parameter, request tickets before opening sockets, request new tickets on reconnect.
- `apps/frontend/src/composables/map/useLayerRealtime.test.ts`: mock ticket API and assert URLs use `ticket`, never `token`.
- `apps/frontend/src/components/MapView.vue`: pass auth-ready state, not JWT, into realtime.
- `apps/frontend/src/components/MapView.test.ts`: keep auth mock aligned with the new `syncRealtimeLayer` behavior.

Docs modify after implementation:

- `Code_wiki/архитектура/api_and_realtime.md`
- `Code_wiki/архитектура/backend.md`
- `Code_wiki/архитектура/frontend.md`
- `Code_wiki/правила_и_стиль/testing_strategy.md`

---

### Task 1: Backend Settings, Model, And Migration

**Files:**

- Modify: `apps/backend/utility_service/utils/tests/test_settings.py`
- Modify: `apps/backend/utility_service/utils/settings.py`
- Create: `apps/backend/utility_service/infrastructure/postgresql/models/websocket_ticket.py`
- Modify: `apps/backend/utility_service/infrastructure/postgresql/alembic/env.py`
- Create: `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/a6f4c9b8d2e1_websocket_tickets.py`

- [ ] **Step 1: Write failing settings tests**

Append to `apps/backend/utility_service/utils/tests/test_settings.py`:

```python
def test_settings_defaults_websocket_ticket_ttl_seconds_to_60() -> None:
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
        DEV_MODE=True,
        JWT_SECRET="CHANGE_ME_IN_ENV",
    )

    assert settings.websocket_ticket_ttl_seconds == 60


def test_settings_reads_websocket_ticket_ttl_seconds_from_env_alias() -> None:
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
        DEV_MODE=True,
        JWT_SECRET="CHANGE_ME_IN_ENV",
        WEBSOCKET_TICKET_TTL_SECONDS=45,
    )

    assert settings.websocket_ticket_ttl_seconds == 45
```

- [ ] **Step 2: Run settings tests to verify failure**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/utils/tests/test_settings.py -q
```

Expected: FAIL with `AttributeError: 'Settings' object has no attribute 'websocket_ticket_ttl_seconds'`.

- [ ] **Step 3: Add the settings field**

In `apps/backend/utility_service/utils/settings.py`, add this field after `access_token_ttl_min`:

```python
    websocket_ticket_ttl_seconds: int = Field(60, alias="WEBSOCKET_TICKET_TTL_SECONDS")
```

- [ ] **Step 4: Run settings tests to verify pass**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/utils/tests/test_settings.py -q
```

Expected: PASS.

- [ ] **Step 5: Create the ticket model**

Create `apps/backend/utility_service/infrastructure/postgresql/models/websocket_ticket.py`:

```python
from __future__ import annotations

import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class WebSocketTicket(Base):
    __tablename__ = "websocket_tickets"
    __table_args__ = (
        UniqueConstraint("ticket_hash", name="uq_websocket_tickets_ticket_hash"),
        Index("ix_websocket_tickets_expires_at", "expires_at"),
        {"schema": "user"},
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    ticket_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    layer_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
```

- [ ] **Step 6: Import the model into Alembic metadata**

In `apps/backend/utility_service/infrastructure/postgresql/alembic/env.py`, add this import next to the existing model imports:

```python
from utility_service.infrastructure.postgresql.models.websocket_ticket import (  # noqa: E402, F401
    WebSocketTicket,
)
```

- [ ] **Step 7: Add the migration**

Create `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/a6f4c9b8d2e1_websocket_tickets.py`:

```python
"""add websocket tickets

Revision ID: a6f4c9b8d2e1
Revises: c9d0e1f2a3b4
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a6f4c9b8d2e1"
down_revision: Union[str, Sequence[str], None] = "c9d0e1f2a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "websocket_tickets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("ticket_hash", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("layer_id", sa.UUID(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticket_hash", name="uq_websocket_tickets_ticket_hash"),
        schema="user",
    )
    op.create_index(
        "ix_websocket_tickets_expires_at",
        "websocket_tickets",
        ["expires_at"],
        schema="user",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_websocket_tickets_expires_at",
        table_name="websocket_tickets",
        schema="user",
    )
    op.drop_table("websocket_tickets", schema="user")
```

- [ ] **Step 8: Run backend tests touched by this task**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/utils/tests/test_settings.py -q
```

Expected: PASS.

---

### Task 2: Backend Ticket Repository And Service

**Files:**

- Create: `apps/backend/utility_service/use_cases/tests/test_websocket_ticket_service.py`
- Create: `apps/backend/utility_service/infrastructure/postgresql/repositories/websocket_ticket_repository.py`
- Create: `apps/backend/utility_service/use_cases/domain/exceptions/websocket_ticket_error.py`
- Create: `apps/backend/utility_service/use_cases/services/websocket_ticket_service.py`

- [ ] **Step 1: Write failing service tests**

Create `apps/backend/utility_service/use_cases/tests/test_websocket_ticket_service.py`:

```python
import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from utility_service.use_cases.domain.exceptions.auth_api_error import AuthApiError
from utility_service.use_cases.domain.exceptions.websocket_ticket_error import (
    WebSocketTicketError,
)
from utility_service.use_cases.services.websocket_ticket_service import (
    WebSocketTicketService,
    hash_websocket_ticket,
)


class DummyTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class DummySession:
    def begin(self):
        return DummyTransaction()


class FakeTicketRepository:
    def __init__(self):
        self.created = []
        self.consumed_hashes = set()

    async def create_ticket(self, *, ticket_hash, user_id, layer_id, expires_at):
        self.created.append(
            SimpleNamespace(
                ticket_hash=ticket_hash,
                user_id=user_id,
                layer_id=layer_id,
                expires_at=expires_at,
            )
        )
        return self.created[-1]

    async def consume_ticket_hash(self, *, ticket_hash, layer_id, now):
        if ticket_hash in self.consumed_hashes:
            return None
        matching = [
            row
            for row in self.created
            if row.ticket_hash == ticket_hash
            and row.layer_id == layer_id
            and row.expires_at > now
        ]
        if not matching:
            return None
        self.consumed_hashes.add(ticket_hash)
        return matching[0]


class FakeLayerRepository:
    def __init__(self, layer):
        self.layer = layer

    async def get_layer_by_id(self, layer_id):
        if self.layer and self.layer.id == layer_id:
            return self.layer
        return None


class FakeUserRepository:
    def __init__(self, user):
        self.user = user

    async def get_by_id(self, user_id):
        if self.user and self.user.id == user_id:
            return self.user
        return None


def make_user(role="editor", is_active=True):
    return SimpleNamespace(
        id=uuid4(),
        email="editor@example.local",
        role=SimpleNamespace(value=role),
        is_active=is_active,
    )


def build_service(user, layer, ticket_repository=None):
    repository = ticket_repository or FakeTicketRepository()
    service = WebSocketTicketService(
        DummySession(),
        repository,
        FakeLayerRepository(layer),
        FakeUserRepository(user),
        ticket_ttl_seconds=60,
    )
    return service, repository


def test_hash_websocket_ticket_uses_sha_256_hex() -> None:
    assert (
        hash_websocket_ticket("ticket-1")
        == "737ce60fccf9da889f4605c0a20479b502eb8ed97e7bf3b5db1295ccd350b1bb"
    )


def test_issue_ticket_stores_hash_and_returns_raw_ticket() -> None:
    user = make_user()
    layer = SimpleNamespace(id=uuid4())
    service, repository = build_service(user, layer)

    result = asyncio.run(service.issue_ticket(user, layer.id))

    assert result.ticket
    assert result.expires_at > datetime.now(timezone.utc)
    assert repository.created[0].ticket_hash == hash_websocket_ticket(result.ticket)
    assert repository.created[0].ticket_hash != result.ticket
    assert repository.created[0].user_id == user.id
    assert repository.created[0].layer_id == layer.id


def test_issue_ticket_rejects_role_not_allowed() -> None:
    user = make_user(role="viewer")
    layer = SimpleNamespace(id=uuid4())
    service, _repository = build_service(user, layer)

    with pytest.raises(AuthApiError) as exc_info:
        asyncio.run(service.issue_ticket(user, layer.id))

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "ROLE_NOT_ALLOWED"


def test_issue_ticket_rejects_missing_layer_with_structured_404() -> None:
    user = make_user()
    layer_id = uuid4()
    service, _repository = build_service(user, None)

    with pytest.raises(AuthApiError) as exc_info:
        asyncio.run(service.issue_ticket(user, layer_id))

    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "LAYER_NOT_FOUND"


def test_consume_ticket_returns_user_context_once() -> None:
    user = make_user(role="reviewer")
    layer = SimpleNamespace(id=uuid4())
    service, _repository = build_service(user, layer)
    issued = asyncio.run(service.issue_ticket(user, layer.id))

    context = asyncio.run(service.consume_ticket(issued.ticket, layer.id))

    assert context.user_id == user.id
    assert context.email == user.email
    assert context.role == "reviewer"

    with pytest.raises(WebSocketTicketError):
        asyncio.run(service.consume_ticket(issued.ticket, layer.id))


def test_consume_ticket_rejects_wrong_layer() -> None:
    user = make_user()
    layer = SimpleNamespace(id=uuid4())
    service, _repository = build_service(user, layer)
    issued = asyncio.run(service.issue_ticket(user, layer.id))

    with pytest.raises(WebSocketTicketError):
        asyncio.run(service.consume_ticket(issued.ticket, uuid4()))


def test_consume_ticket_rejects_inactive_user_after_issue() -> None:
    user = make_user(is_active=True)
    layer = SimpleNamespace(id=uuid4())
    service, _repository = build_service(user, layer)
    issued = asyncio.run(service.issue_ticket(user, layer.id))
    user.is_active = False

    with pytest.raises(WebSocketTicketError):
        asyncio.run(service.consume_ticket(issued.ticket, layer.id))


def test_consume_ticket_rejects_expired_ticket() -> None:
    user = make_user()
    layer = SimpleNamespace(id=uuid4())
    repository = FakeTicketRepository()
    service = WebSocketTicketService(
        DummySession(),
        repository,
        FakeLayerRepository(layer),
        FakeUserRepository(user),
        ticket_ttl_seconds=60,
    )
    ticket = "expired-ticket"
    repository.created.append(
        SimpleNamespace(
            ticket_hash=hash_websocket_ticket(ticket),
            user_id=user.id,
            layer_id=layer.id,
            expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
    )

    with pytest.raises(WebSocketTicketError):
        asyncio.run(service.consume_ticket(ticket, layer.id))
```

- [ ] **Step 2: Run service tests to verify failure**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/use_cases/tests/test_websocket_ticket_service.py -q
```

Expected: FAIL with `ModuleNotFoundError` for `websocket_ticket_service`.

- [ ] **Step 3: Create the repository**

Create `apps/backend/utility_service/infrastructure/postgresql/repositories/websocket_ticket_repository.py`:

```python
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import insert, update
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.websocket_ticket import WebSocketTicket


class WebSocketTicketRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_ticket(
        self,
        *,
        ticket_hash: str,
        user_id: UUID,
        layer_id: UUID,
        expires_at: datetime,
    ) -> WebSocketTicket:
        stmt = (
            insert(WebSocketTicket)
            .values(
                ticket_hash=ticket_hash,
                user_id=user_id,
                layer_id=layer_id,
                expires_at=expires_at,
            )
            .returning(WebSocketTicket)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def consume_ticket_hash(
        self,
        *,
        ticket_hash: str,
        layer_id: UUID,
        now: datetime,
    ) -> WebSocketTicket | None:
        stmt = (
            update(WebSocketTicket)
            .where(WebSocketTicket.ticket_hash == ticket_hash)
            .where(WebSocketTicket.layer_id == layer_id)
            .where(WebSocketTicket.used_at.is_(None))
            .where(WebSocketTicket.expires_at > now)
            .values(used_at=now)
            .returning(WebSocketTicket)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
```

- [ ] **Step 4: Create the service**

Create `apps/backend/utility_service/use_cases/services/websocket_ticket_service.py`:

```python
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from typing import Any
from uuid import UUID

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.repositories.layer_repository import LayerRepository
from utility_service.infrastructure.postgresql.repositories.user_repository import UserRepository
from utility_service.infrastructure.postgresql.repositories.websocket_ticket_repository import (
    WebSocketTicketRepository,
)
from utility_service.use_cases.domain.exceptions.auth_api_error import AuthApiError
from utility_service.use_cases.domain.exceptions.websocket_ticket_error import (
    INVALID_WEBSOCKET_TICKET_MESSAGE,
    WebSocketTicketError,
)
from utility_service.use_cases.schemas.realtime import WebSocketTicketOut
from utility_service.use_cases.services.realtime_connection_manager import WebSocketUserContext
from utility_service.utils.settings import settings


ALLOWED_REALTIME_ROLES = {"editor", "reviewer"}
def hash_websocket_ticket(ticket: str) -> str:
    return hashlib.sha256(ticket.encode("utf-8")).hexdigest()


def _role_value(user: Any) -> str:
    role = getattr(user, "role", "")
    return str(getattr(role, "value", role))


class WebSocketTicketService:
    def __init__(
        self,
        session: AsyncSession,
        ticket_repository: WebSocketTicketRepository,
        layer_repository: LayerRepository,
        user_repository: UserRepository,
        ticket_ttl_seconds: int | None = None,
    ):
        self.session = session
        self.ticket_repository = ticket_repository
        self.layer_repository = layer_repository
        self.user_repository = user_repository
        self.ticket_ttl_seconds = (
            ticket_ttl_seconds
            if ticket_ttl_seconds is not None
            else settings.websocket_ticket_ttl_seconds
        )

    async def issue_ticket(self, user: Any, layer_id: UUID) -> WebSocketTicketOut:
        if _role_value(user) not in ALLOWED_REALTIME_ROLES:
            raise AuthApiError(
                status.HTTP_403_FORBIDDEN,
                "ROLE_NOT_ALLOWED",
                "Подписка на realtime недоступна для этой роли.",
            )

        async with self.session.begin():
            layer = await self.layer_repository.get_layer_by_id(layer_id)
            if layer is None:
                raise AuthApiError(
                    status.HTTP_404_NOT_FOUND,
                    "LAYER_NOT_FOUND",
                    "Слой не найден.",
                )

            ticket = secrets.token_urlsafe(32)
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(seconds=self.ticket_ttl_seconds)
            await self.ticket_repository.create_ticket(
                ticket_hash=hash_websocket_ticket(ticket),
                user_id=user.id,
                layer_id=layer_id,
                expires_at=expires_at,
            )

        return WebSocketTicketOut(ticket=ticket, expires_at=expires_at)

    async def consume_ticket(self, ticket: str, layer_id: UUID) -> WebSocketUserContext:
        async with self.session.begin():
            ticket_row = await self.ticket_repository.consume_ticket_hash(
                ticket_hash=hash_websocket_ticket(ticket),
                layer_id=layer_id,
                now=datetime.now(timezone.utc),
            )
            if ticket_row is None:
                raise WebSocketTicketError(INVALID_WEBSOCKET_TICKET_MESSAGE)

            user = await self.user_repository.get_by_id(ticket_row.user_id)
            if user is None or not user.is_active or _role_value(user) not in ALLOWED_REALTIME_ROLES:
                raise WebSocketTicketError(INVALID_WEBSOCKET_TICKET_MESSAGE)

            return WebSocketUserContext(
                user_id=user.id,
                email=user.email,
                role=_role_value(user),
            )
```

- [ ] **Step 5: Run service tests to verify pass**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/use_cases/tests/test_websocket_ticket_service.py -q
```

Expected: PASS.

---

### Task 3: Backend HTTP Ticket Issue Endpoint

**Files:**

- Create: `apps/backend/utility_service/use_cases/schemas/realtime/__init__.py`
- Create: `apps/backend/utility_service/use_cases/schemas/realtime/websocket_ticket_out.py`
- Modify: `apps/backend/utility_service/use_cases/deps.py`
- Modify: `apps/backend/utility_service/web_api/api/ws_layers.py`
- Modify: `apps/backend/utility_service/web_api/tests/test_ws_layers.py`

- [ ] **Step 1: Write failing HTTP endpoint tests**

Append to `apps/backend/utility_service/web_api/tests/test_ws_layers.py`:

```python
def test_ws_ticket_endpoint_issues_ticket_for_authorized_user() -> None:
    layer_id = uuid4()
    user_id = uuid4()

    async def get_user_by_id(_user_id):
        return SimpleNamespace(
            id=user_id,
            email="editor@example.local",
            role=SimpleNamespace(value="editor"),
            is_active=True,
        )

    async def get_layer_by_id(_layer_id):
        return SimpleNamespace(id=layer_id)

    app = create_test_app(
        SimpleNamespace(get_user_by_id=get_user_by_id),
        SimpleNamespace(get_layer_by_id=get_layer_by_id),
    )
    token = create_access_token(str(user_id), "editor")

    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/ws/layers/{layer_id}/ticket",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["ticket"]
    assert response.json()["expiresAt"]


def test_ws_ticket_endpoint_rejects_missing_http_auth() -> None:
    layer_id = uuid4()

    async def get_user_by_id(_user_id):
        return None

    async def get_layer_by_id(_layer_id):
        return SimpleNamespace(id=layer_id)

    app = create_test_app(
        SimpleNamespace(get_user_by_id=get_user_by_id),
        SimpleNamespace(get_layer_by_id=get_layer_by_id),
    )

    with TestClient(app) as client:
        response = client.post(f"/api/v1/ws/layers/{layer_id}/ticket")

    assert response.status_code == 401
```

Do not update `create_test_app` before running the failing test; the first failure should be the missing route.

- [ ] **Step 2: Run endpoint tests to verify failure**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/web_api/tests/test_ws_layers.py::test_ws_ticket_endpoint_issues_ticket_for_authorized_user -q
```

Expected: FAIL with status `404`.

- [ ] **Step 3: Create the response schema**

Create `apps/backend/utility_service/use_cases/schemas/realtime/__init__.py`:

```python
"""Realtime API schemas."""
```

Create `apps/backend/utility_service/use_cases/schemas/realtime/websocket_ticket_out.py`:

```python
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WebSocketTicketOut(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    ticket: str
    expires_at: datetime = Field(serialization_alias="expiresAt")
```

- [ ] **Step 4: Add the dependency factory**

In `apps/backend/utility_service/use_cases/deps.py`, add this import:

```python
from utility_service.infrastructure.postgresql.repositories.websocket_ticket_repository import (
    WebSocketTicketRepository,
)
from utility_service.use_cases.services.websocket_ticket_service import WebSocketTicketService
```

Add this function near the other service factories:

```python
def get_websocket_ticket_service(
    session: AsyncSession = Depends(get_session),
) -> WebSocketTicketService:
    return WebSocketTicketService(
        session,
        WebSocketTicketRepository(session),
        LayerRepository(session),
        UserRepository(session),
    )
```

- [ ] **Step 5: Add the ticket issue route**

In `apps/backend/utility_service/web_api/api/ws_layers.py`, import:

```python
from typing import Any

from utility_service.use_cases.deps import get_websocket_ticket_service
from utility_service.use_cases.schemas.realtime.websocket_ticket_out import WebSocketTicketOut
from utility_service.use_cases.services.websocket_ticket_service import WebSocketTicketService
from utility_service.web_api.api.auth import get_current_user
```

Add this route above `subscribe_to_layer_updates`:

```python
@ws_layers_router.post(
    "/api/v1/ws/layers/{layer_id}/ticket",
    response_model=WebSocketTicketOut,
)
async def issue_layer_websocket_ticket(
    layer_id: UUID,
    user: Any = Depends(get_current_user),
    ticket_service: WebSocketTicketService = Depends(get_websocket_ticket_service),
) -> WebSocketTicketOut:
    return await ticket_service.issue_ticket(user, layer_id)
```

- [ ] **Step 6: Update `create_test_app` dependency overrides**

In `apps/backend/utility_service/web_api/tests/test_ws_layers.py`, import `get_websocket_ticket_service` and `WebSocketTicketService`, then let `create_test_app` accept an optional ticket service. Use the real service with the fake in-memory repository from `test_websocket_ticket_service.py`; do not use real DB repositories in these TestClient unit tests.

Use this helper code in the test file:

```python
from utility_service.use_cases.deps import get_websocket_ticket_service
from utility_service.use_cases.services.websocket_ticket_service import WebSocketTicketService
from utility_service.use_cases.tests.test_websocket_ticket_service import (
    DummySession,
    FakeTicketRepository,
    FakeUserRepository,
)


def create_ticket_service(user: object, layer_service: object) -> WebSocketTicketService:
    class LayerRepositoryAdapter:
        async def get_layer_by_id(self, layer_id):
            return await layer_service.get_layer_by_id(layer_id)

    return WebSocketTicketService(
        DummySession(),
        FakeTicketRepository(),
        LayerRepositoryAdapter(),
        FakeUserRepository(user),
        ticket_ttl_seconds=60,
    )
```

Then update `create_test_app` so it can override `get_websocket_ticket_service`:

```python
def create_test_app(
    auth_service: object,
    layer_service: object,
    connection_manager: WebSocketConnectionManager | None = None,
    ticket_service: object | None = None,
) -> FastAPI:
    app = FastAPI()
    app.state.websocket_connection_manager = connection_manager or WebSocketConnectionManager()
    app.include_router(ws_layers_router)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_layer_service] = lambda: layer_service
    if ticket_service is not None:
        app.dependency_overrides[get_websocket_ticket_service] = lambda: ticket_service
    return app
```

For the endpoint success test, construct `ticket_service` after defining the user object and pass it into `create_test_app`.

- [ ] **Step 7: Run endpoint tests to verify pass**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/web_api/tests/test_ws_layers.py::test_ws_ticket_endpoint_issues_ticket_for_authorized_user utility_service/web_api/tests/test_ws_layers.py::test_ws_ticket_endpoint_rejects_missing_http_auth -q
```

Expected: PASS.

---

### Task 4: Backend WebSocket Ticket Handshake

**Files:**

- Create: `apps/backend/utility_service/utils/websocket_ticket_auth.py`
- Modify: `apps/backend/utility_service/web_api/api/ws_layers.py`
- Modify: `apps/backend/utility_service/web_api/tests/test_ws_layers.py`
- Modify or delete: `apps/backend/utility_service/web_api/tests/test_websocket_auth.py`
- Modify or delete: `apps/backend/utility_service/web_api/tests/test_websocket_auth_roles.py`

- [ ] **Step 1: Write failing WebSocket ticket tests**

Update `test_ws_layer_subscription_accepts_authorized_users` in `apps/backend/utility_service/web_api/tests/test_ws_layers.py` so it first issues a ticket and then connects with `?ticket=...`:

```python
@pytest.mark.parametrize("role", ["editor", "reviewer"])
def test_ws_layer_subscription_accepts_authorized_users(role: str) -> None:
    layer_id = uuid4()
    user_id = uuid4()
    token = create_access_token(str(user_id), role)
    user = SimpleNamespace(
        id=user_id,
        email=f"{role}@example.com",
        role=SimpleNamespace(value=role),
        is_active=True,
    )

    async def get_user_by_id(_user_id):
        return user

    async def get_layer_by_id(_layer_id):
        return SimpleNamespace(id=layer_id)

    auth_service = SimpleNamespace(get_user_by_id=get_user_by_id)
    layer_service = SimpleNamespace(get_layer_by_id=get_layer_by_id)
    ticket_service = create_ticket_service(user, layer_service)
    connection_manager = WebSocketConnectionManager()
    app = create_test_app(auth_service, layer_service, connection_manager, ticket_service)

    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/ws/layers/{layer_id}/ticket",
            headers={"Authorization": f"Bearer {token}"},
        )
        ticket = response.json()["ticket"]
        with client.websocket_connect(f"/api/v1/ws/layers/{layer_id}?ticket={ticket}") as websocket:
            assert websocket.receive_json() == {"type": "connected", "layerId": str(layer_id)}
            assert connection_manager.get_connection_count(layer_id) == 1

    assert connection_manager.get_connection_count(layer_id) == 0
```

Add tests:

```python
def test_ws_layer_subscription_rejects_reused_ticket() -> None:
    layer_id = uuid4()
    user_id = uuid4()
    token = create_access_token(str(user_id), "editor")
    user = SimpleNamespace(
        id=user_id,
        email="editor@example.local",
        role=SimpleNamespace(value="editor"),
        is_active=True,
    )

    async def get_user_by_id(_user_id):
        return user

    async def get_layer_by_id(_layer_id):
        return SimpleNamespace(id=layer_id)

    auth_service = SimpleNamespace(get_user_by_id=get_user_by_id)
    layer_service = SimpleNamespace(get_layer_by_id=get_layer_by_id)
    ticket_service = create_ticket_service(user, layer_service)
    app = create_test_app(auth_service, layer_service, ticket_service=ticket_service)

    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/ws/layers/{layer_id}/ticket",
            headers={"Authorization": f"Bearer {token}"},
        )
        ticket = response.json()["ticket"]
        with client.websocket_connect(f"/api/v1/ws/layers/{layer_id}?ticket={ticket}") as websocket:
            assert websocket.receive_json()["type"] == "connected"

        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect(f"/api/v1/ws/layers/{layer_id}?ticket={ticket}"):
                pass

    assert exc_info.value.code == 1008


def test_ws_layer_subscription_rejects_legacy_jwt_query_token() -> None:
    layer_id = uuid4()
    user_id = uuid4()
    token = create_access_token(str(user_id), "editor")

    async def get_user_by_id(_user_id):
        return SimpleNamespace(
            id=user_id,
            email="editor@example.local",
            role=SimpleNamespace(value="editor"),
            is_active=True,
        )

    async def get_layer_by_id(_layer_id):
        return SimpleNamespace(id=layer_id)

    app = create_test_app(
        SimpleNamespace(get_user_by_id=get_user_by_id),
        SimpleNamespace(get_layer_by_id=get_layer_by_id),
    )

    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect(f"/api/v1/ws/layers/{layer_id}?token={token}"):
                pass

    assert exc_info.value.code == 1008
```

- [ ] **Step 2: Run the updated WebSocket tests to verify failure**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/web_api/tests/test_ws_layers.py -q
```

Expected: FAIL because the WebSocket route still reads `token`.

- [ ] **Step 3: Create the ticket auth helper**

Create `apps/backend/utility_service/utils/websocket_ticket_auth.py`:

```python
from __future__ import annotations

from uuid import UUID

from fastapi import WebSocketException, status

from utility_service.use_cases.domain.exceptions.websocket_ticket_error import (
    INVALID_WEBSOCKET_TICKET_MESSAGE,
    WebSocketTicketError,
)
from utility_service.use_cases.services.realtime_connection_manager import WebSocketUserContext
from utility_service.use_cases.services.websocket_ticket_service import WebSocketTicketService


def _websocket_auth_error(reason: str) -> WebSocketException:
    return WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason=reason)


async def authenticate_websocket_ticket(
    ticket: str | None,
    layer_id: UUID,
    ticket_service: WebSocketTicketService,
) -> WebSocketUserContext:
    if ticket is None or not ticket.strip():
        raise _websocket_auth_error("Realtime ticket отсутствует")

    try:
        return await ticket_service.consume_ticket(ticket, layer_id)
    except WebSocketTicketError as exc:
        raise _websocket_auth_error(INVALID_WEBSOCKET_TICKET_MESSAGE) from exc
```

- [ ] **Step 4: Switch the WebSocket route from token to ticket**

In `apps/backend/utility_service/web_api/api/ws_layers.py`:

Remove:

```python
from utility_service.web_api.api.websocket_auth import authenticate_websocket_token
```

Import:

```python
from utility_service.utils.websocket_ticket_auth import authenticate_websocket_ticket
```

Add `ticket_service` to `subscribe_to_layer_updates` dependencies:

```python
    ticket_service: WebSocketTicketService = Depends(get_websocket_ticket_service),
```

Replace:

```python
    token = websocket.query_params.get("token")
    user_context = await authenticate_websocket_token(token, auth_service)
```

with:

```python
    ticket = websocket.query_params.get("ticket")
    user_context = await authenticate_websocket_ticket(ticket, layer_id, ticket_service)
```

Keep the existing layer existence check after ticket auth:

```python
    layer = await layer_service.get_layer_by_id(layer_id)
    if layer is None:
        raise _websocket_route_error("Слой не найден")
```

- [ ] **Step 5: Remove stale token-auth tests**

Delete `apps/backend/utility_service/web_api/tests/test_websocket_auth.py` and `apps/backend/utility_service/web_api/tests/test_websocket_auth_roles.py` after the route has switched to `authenticate_websocket_ticket`.

Run this search before deleting:

```powershell
rg -n "authenticate_websocket_token|websocket_auth" apps/backend/utility_service
```

Expected before deletion: only stale tests reference `authenticate_websocket_token`.

- [ ] **Step 6: Run backend WebSocket tests to verify pass**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/web_api/tests/test_ws_layers.py utility_service/use_cases/tests/test_websocket_ticket_service.py -q
```

Expected: PASS.

---

### Task 5: Frontend Ticket API And Realtime Composable

**Files:**

- Create: `apps/frontend/src/api/realtime.ts`
- Modify: `apps/frontend/src/composables/map/useLayerRealtime.ts`
- Modify: `apps/frontend/src/composables/map/useLayerRealtime.test.ts`
- Modify: `apps/frontend/src/components/MapView.vue`
- Modify: `apps/frontend/src/components/MapView.test.ts`

- [ ] **Step 1: Write failing frontend tests for ticket URLs**

In `apps/frontend/src/composables/map/useLayerRealtime.test.ts`, add this hoisted mock:

```ts
const apiMocks = vi.hoisted(() => ({
  issueLayerWebSocketTicket: vi.fn(),
}));

vi.mock("@/api/realtime", () => ({
  issueLayerWebSocketTicket: apiMocks.issueLayerWebSocketTicket,
}));
```

In `beforeEach`, add:

```ts
    apiMocks.issueLayerWebSocketTicket.mockResolvedValue({
      ticket: "ticket-1",
      expiresAt: "2026-07-02T10:00:00Z",
    });
```

Update the first test call and URL assertions:

```ts
    await realtime.connectToLayer("layer-1");

    expect(apiMocks.issueLayerWebSocketTicket).toHaveBeenCalledWith("layer-1");

    const socket = getSocketAt(0);
    expect(socket.url).toContain("/api/v1/ws/layers/layer-1");
    expect(socket.url).toContain("ticket=ticket-1");
    expect(socket.url).not.toContain("token=");
```

Add a reconnect test assertion:

```ts
    apiMocks.issueLayerWebSocketTicket
      .mockResolvedValueOnce({
        ticket: "ticket-1",
        expiresAt: "2026-07-02T10:00:00Z",
      })
      .mockResolvedValueOnce({
        ticket: "ticket-2",
        expiresAt: "2026-07-02T10:00:30Z",
      });
```

After advancing reconnect timer, assert:

```ts
    expect(apiMocks.issueLayerWebSocketTicket).toHaveBeenNthCalledWith(2, "layer-1");
    expect(secondSocket.url).toContain("ticket=ticket-2");
    expect(secondSocket.url).not.toContain("token=");
```

Add a failed-ticket test:

```ts
  it("does not open a websocket when ticket issue fails", async () => {
    apiMocks.issueLayerWebSocketTicket.mockRejectedValueOnce(new Error("401"));
    const { useLayerRealtime } =
      await import("@/composables/map/useLayerRealtime");
    const realtime = useLayerRealtime();

    await realtime.connectToLayer("layer-1");

    expect(FakeWebSocket.instances).toHaveLength(0);
    expect(realtime.isAuthError.value).toBe(true);
    expect(realtime.hasStoppedReconnect.value).toBe(true);
  });
```

- [ ] **Step 2: Run frontend realtime tests to verify failure**

Run:

```powershell
cd apps/frontend
npm test -- src/composables/map/useLayerRealtime.test.ts
```

Expected: FAIL because `@/api/realtime` does not exist and `connectToLayer` still requires a token.

- [ ] **Step 3: Create the frontend ticket API**

Create `apps/frontend/src/api/realtime.ts`:

```ts
import { http } from "@/api/http";

export type WebSocketTicketResponse = {
  ticket: string;
  expiresAt: string;
};

export async function issueLayerWebSocketTicket(
  layerId: string,
): Promise<WebSocketTicketResponse> {
  const response = await http.post<WebSocketTicketResponse>(
    `/api/v1/ws/layers/${layerId}/ticket`,
  );
  return response.data;
}
```

- [ ] **Step 4: Update `useLayerRealtime` signatures and state**

In `apps/frontend/src/composables/map/useLayerRealtime.ts`, import the API:

```ts
import { issueLayerWebSocketTicket } from "@/api/realtime";
```

Replace `currentToken` with:

```ts
  const currentAuthReady = ref(false);
```

Change signatures:

```ts
  async function connectToLayer(layerId: string): Promise<void> {
```

```ts
  async function handleLayerChange(
    layer: LayerDto | null,
    authReady: boolean,
  ): Promise<void> {
    currentAuthReady.value = authReady;
    if (!layer || !authReady) {
      disconnect();
      return;
    }

    await connectToLayer(layer.id);
  }
```

In `connectToLayer`, remove token comparisons and compare only layer plus socket state:

```ts
    const sameConnectionRequested =
      currentLayerId.value === layerId &&
      socket.value !== null &&
      (socket.value.readyState === WebSocket.OPEN ||
        socket.value.readyState === WebSocket.CONNECTING);
```

Call:

```ts
    openSocket(layerId, false);
```

- [ ] **Step 5: Make socket opening issue tickets**

Change `openSocket` to async:

```ts
  async function openSocket(layerId: string, isReconnect: boolean) {
    clearReconnectTimer();
    closeActiveSocketIfNeeded();

    activeGeneration += 1;
    const generation = activeGeneration;
    isConnected.value = false;
    isReconnecting.value = isReconnect;
    isSyncingAfterReconnect.value = false;
    hasStoppedReconnect.value = false;
    isAuthError.value = false;
    connectionError.value = null;

    let ticket: string;
    try {
      const issued = await issueLayerWebSocketTicket(layerId);
      ticket = issued.ticket;
    } catch {
      if (generation === activeGeneration) {
        isReconnecting.value = false;
        hasStoppedReconnect.value = true;
        isAuthError.value = true;
        connectionError.value = "Ошибка авторизации realtime";
      }
      return;
    }

    if (generation !== activeGeneration || currentLayerId.value !== layerId) {
      return;
    }

    const nextSocket = new WebSocket(buildLayerWebSocketUrl(layerId, ticket));
    socket.value = nextSocket;
```

Keep the existing `message` and `close` listeners inside the new function body. Replace reconnect timer call:

```ts
      void openSocket(nextLayerId, true);
```

Update `scheduleReconnect` to require `currentAuthReady.value` instead of a token:

```ts
    if (!nextLayerId || !currentAuthReady.value) {
      isReconnecting.value = false;
      return;
    }
```

In `disconnect`, reset `currentAuthReady.value = false` and increment `activeGeneration` before closing the socket:

```ts
    activeGeneration += 1;
    currentAuthReady.value = false;
```

Update URL builder:

```ts
function buildLayerWebSocketUrl(layerId: string, ticket: string): string {
  const baseUrl = resolveWebSocketBaseUrl();
  const url = new URL(`/api/v1/ws/layers/${layerId}`, baseUrl);
  url.searchParams.set("ticket", ticket);
  return url.toString();
}
```

- [ ] **Step 6: Update MapView to stop passing JWT**

In `apps/frontend/src/components/MapView.vue`, replace `syncRealtimeLayer` with:

```ts
async function syncRealtimeLayer(layer: LayerDto | null): Promise<void> {
  if (!layer || !auth.isAuthenticated) {
    disconnectRealtime();
    return;
  }

  await handleRealtimeLayerChange(layer, auth.isAuthenticated);
}
```

In `apps/frontend/src/components/MapView.test.ts`, update the auth mock to remove `token`:

```ts
vi.mock("@/stores/auth", () => ({
  useAuthStore: () => ({
    isAuthenticated: true,
  }),
}));
```

- [ ] **Step 7: Run frontend tests to verify pass**

Run:

```powershell
cd apps/frontend
npm test -- src/composables/map/useLayerRealtime.test.ts src/components/MapView.test.ts
```

Expected: PASS.

- [ ] **Step 8: Run frontend typecheck**

Run:

```powershell
cd apps/frontend
npm run typecheck
```

Expected: PASS.

---

### Task 6: End-To-End Verification And Documentation

**Files:**

- Modify: `Code_wiki/архитектура/api_and_realtime.md`
- Modify: `Code_wiki/архитектура/backend.md`
- Modify: `Code_wiki/архитектура/frontend.md`
- Modify: `Code_wiki/правила_и_стиль/testing_strategy.md`
- Check: `docs/agent-memory/file-map.md`

- [ ] **Step 1: Run backend targeted tests**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/use_cases/tests/test_websocket_ticket_service.py utility_service/web_api/tests/test_ws_layers.py utility_service/utils/tests/test_settings.py -q
```

Expected: PASS.

- [ ] **Step 2: Run backend full tests**

Run:

```powershell
cd apps/backend
python -m pytest
```

Expected: PASS.

- [ ] **Step 3: Run frontend targeted tests**

Run:

```powershell
cd apps/frontend
npm test -- src/composables/map/useLayerRealtime.test.ts src/components/MapView.test.ts
```

Expected: PASS.

- [ ] **Step 4: Run frontend full checks**

Run:

```powershell
cd apps/frontend
npm test
npm run typecheck
npm run lint
```

Expected: PASS for all commands.

- [ ] **Step 5: Search for forbidden WebSocket JWT URL usage**

Run:

```powershell
rg -n "token=|query_params.get\\(\"token\"\\)|authenticate_websocket_token|connectToLayer\\([^\\)]*,\\s*\" apps/backend apps/frontend
```

Expected: no production matches for WebSocket JWT query auth. Test matches are allowed only when asserting legacy `?token=<jwt>` is rejected.

- [ ] **Step 6: Update Code_wiki API/realtime node**

In `Code_wiki/архитектура/api_and_realtime.md`, replace the WebSocket Realtime endpoint description with:

```markdown
Endpoint для выдачи ticket: `POST /api/v1/ws/layers/{layer_id}/ticket`.
Endpoint подписки: `GET /api/v1/ws/layers/{layer_id}?ticket=...`.

Server-side:

- ticket issue endpoint требует обычный HTTP `Authorization: Bearer ...`;
- ticket является opaque credential, хранится в БД только как SHA-256 hash;
- ticket короткоживущий, одноразовый и привязан к `layer_id`;
- WebSocket handshake атомарно consumes ticket и отклоняет missing/invalid/expired/reused/wrong-layer ticket с close code `1008`;
- старый `?token=<jwt>` больше не авторизует WebSocket;
- роли `editor` и `reviewer` допускаются к read-only подписке;
- feature create/update/delete публикуют события `feature_created`, `feature_updated`, `feature_deleted`.

Client-side:

- `useLayerRealtime` перед каждым initial connect и reconnect получает новый ticket через HTTP API;
- WebSocket URL содержит `ticket=...` и не содержит JWT `token=...`;
- при reconnect frontend вызывает forced reload активного слоя после получения `connected`.
```

- [ ] **Step 7: Update backend/frontend/testing wiki nodes**

Add concise Russian notes:

`Code_wiki/архитектура/backend.md`:

```markdown
WebSocket realtime auth использует `WebSocketTicketService` и таблицу
`"user".websocket_tickets`: raw ticket не хранится, lookup идет по SHA-256 hash,
а consume выполняется атомарным `UPDATE ... used_at IS NULL ... RETURNING`.
HTTP Bearer login flow не меняется.
```

`Code_wiki/архитектура/frontend.md`:

```markdown
`useLayerRealtime` больше не принимает JWT как WebSocket credential. Composable
сам запрашивает short-lived ticket через `src/api/realtime.ts` и использует новый
ticket для каждой попытки WebSocket connect/reconnect.
```

`Code_wiki/правила_и_стиль/testing_strategy.md`:

```markdown
Realtime auth tests должны покрывать ticket issue, single-use consume, expired,
reused и wrong-layer ticket, а frontend tests должны проверять, что WebSocket URL
не содержит `token=`.
```

- [ ] **Step 8: Update agent memory file map**

Run:

```powershell
rg -n "websocket layer realtime auth|frontend realtime websocket|auth login users jwt" docs/agent-memory/file-map.md docs/agent-memory
```

Expected: `docs/agent-memory/file-map.md` contains existing realtime/auth pointers.

Update the existing `websocket layer realtime auth` entry so it includes the new durable backend files:

```markdown
- websocket layer realtime auth: `apps/backend/utility_service/web_api/api/ws_layers.py`, `apps/backend/utility_service/utils/websocket_ticket_auth.py`, `apps/backend/utility_service/use_cases/services/websocket_ticket_service.py`, `apps/backend/utility_service/infrastructure/postgresql/repositories/websocket_ticket_repository.py`, `apps/backend/utility_service/infrastructure/postgresql/models/websocket_ticket.py`, `apps/backend/utility_service/use_cases/services/realtime_connection_manager.py`
```

Update the existing `frontend realtime websocket` entry so it includes the new ticket API:

```markdown
- frontend realtime websocket: `apps/frontend/src/api/realtime.ts`, `apps/frontend/src/composables/map/useLayerRealtime.ts`, `apps/frontend/src/contracts/realtime.ts`, `apps/frontend/src/contracts/map-cache.ts`
```

- [ ] **Step 9: Final verification**

Run:

```powershell
git status --short
```

Expected: working tree shows the implementation, documentation, spec, and plan files that the user will review and add manually. No unrelated user-owned changes should be modified by this task.

---

## Self-Review Notes

- Spec coverage: HTTP Bearer auth remains unchanged; WebSocket JWT query auth is removed; DB-backed single-use tickets are modeled, issued, consumed, tested, and documented; reconnect requests new tickets; docs update path is included.
- Scope check: this is one cohesive backend/frontend auth change for a single WebSocket flow. Cookie auth, Redis, refresh tokens, and realtime event changes remain out of scope.
- Type consistency: backend uses `WebSocketTicketService.issue_ticket(user, layer_id)` and `consume_ticket(ticket, layer_id)` throughout; frontend uses `issueLayerWebSocketTicket(layerId)` and `connectToLayer(layerId)` without JWT.
- Placeholder scan: plan uses concrete file names, commands, snippets, and expected outcomes.
