# Auth Session Cookie Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Убрать persistent `access_token` из `localStorage`, оставить access JWT только in-memory и восстанавливать вход через 12-часовую `HttpOnly` server-side session cookie.

**Architecture:** Backend добавляет DB-backed `auth_sessions`: raw session token живет только в cookie, а в БД хранится SHA-256 hash. REST API остается Bearer-based: login/refresh возвращают короткий `access_token`, frontend хранит его только в Pinia memory и после reload вызывает refresh endpoint с cookie.

**Tech Stack:** FastAPI, SQLAlchemy async, Alembic, Pydantic settings, jose JWT, Vue 3, Pinia, Axios, Vitest, Pytest.

---

## Scope Check

Один план покрывает один связный security slice: backend session cookie + frontend in-memory token restore. WebSocket ticket flow не меняется, но должен остаться regression gate.

## File Structure

Create:

- `apps/backend/utility_service/infrastructure/postgresql/models/auth_session.py` - SQLAlchemy model для `user.auth_sessions`.
- `apps/backend/utility_service/infrastructure/postgresql/repositories/auth_session_repository.py` - DB operations для create/get/revoke/rotate session.
- `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/f8a7b6c5d4e3_auth_sessions.py` - migration after `a6f4c9b8d2e1`.
- `apps/backend/utility_service/use_cases/services/auth_session_service.py` - opaque token generation, SHA-256 hash, cookie/session semantics.
- `apps/backend/utility_service/use_cases/schemas/auth/auth_session_out.py` - Pydantic use-case return schemas for issued/refreshed auth sessions.
- `apps/backend/utility_service/use_cases/tests/test_auth_session_service.py` - service-level TDD.
- `apps/backend/utility_service/infrastructure/tests/test_auth_session_repository.py` - repository SQL contract tests.
- `apps/frontend/src/api/auth.test.ts` - auth API credential options tests.

Modify:

- `apps/backend/utility_service/utils/settings.py` - session TTL and cookie settings.
- `apps/backend/utility_service/utils/tests/test_settings.py` - settings regression tests.
- `apps/backend/utility_service/web_api/main.py` - CORS credentials.
- `apps/backend/utility_service/web_api/tests/test_auth_api.py` - login/refresh/logout API tests.
- `apps/backend/utility_service/web_api/api/auth.py` - set/clear cookie and new routes.
- `apps/backend/utility_service/use_cases/deps.py` - dependency factory for `AuthSessionService`.
- `apps/backend/utility_service/infrastructure/postgresql/alembic/env.py` - import `AuthSession` for autogenerate consistency.
- `apps/frontend/src/api/auth.ts` - refresh/logout session endpoints.
- `apps/frontend/src/stores/auth.ts` - remove `localStorage` access token/user, make restore cookie-based.
- `apps/frontend/src/stores/auth.test.ts` - update storage and restore expectations.
- `apps/frontend/src/api/http.ts` - keep Bearer from memory; do not enable global credentials in the shared axios instance.
- `Code_wiki/архитектура/api_and_realtime.md` and `Code_wiki/архитектура/frontend.md` - update only through `/ingest repository-change` after implementation if the change qualifies as durable technical knowledge.

---

### Task 1: Backend Settings And CORS Contract

**Files:**

- Modify: `apps/backend/utility_service/utils/settings.py`
- Modify: `apps/backend/utility_service/utils/tests/test_settings.py`
- Modify: `apps/backend/utility_service/web_api/main.py`
- Test: `apps/backend/utility_service/utils/tests/test_settings.py`

- [ ] **Step 1: Write failing settings tests**

Add these tests to `apps/backend/utility_service/utils/tests/test_settings.py`:

```python
def test_settings_defaults_auth_session_cookie_values() -> None:
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
        DEV_MODE=True,
        JWT_SECRET="CHANGE_ME_IN_ENV",
    )

    assert settings.auth_session_ttl_hours == 12
    assert settings.auth_session_cookie_name == "geoservice_session"
    assert settings.auth_session_cookie_secure is False
    assert settings.auth_session_cookie_samesite == "lax"


def test_settings_reads_auth_session_values_from_env_aliases() -> None:
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
        DEV_MODE=True,
        JWT_SECRET="CHANGE_ME_IN_ENV",
        AUTH_SESSION_TTL_HOURS=8,
        AUTH_SESSION_COOKIE_NAME="custom_session",
        AUTH_SESSION_COOKIE_SECURE=True,
        AUTH_SESSION_COOKIE_SAMESITE="strict",
    )

    assert settings.auth_session_ttl_hours == 8
    assert settings.auth_session_cookie_name == "custom_session"
    assert settings.auth_session_cookie_secure is True
    assert settings.auth_session_cookie_samesite == "strict"
```

- [ ] **Step 2: Run settings tests and verify failure**

Run:

```powershell
cd apps/backend
pytest utility_service/utils/tests/test_settings.py -q
```

Expected: FAIL because `Settings` has no `auth_session_ttl_hours`, `auth_session_cookie_name`, `auth_session_cookie_secure`, or `auth_session_cookie_samesite`.

- [ ] **Step 3: Add settings fields**

In `apps/backend/utility_service/utils/settings.py`, add these fields after `websocket_ticket_ttl_seconds`:

```python
    auth_session_ttl_hours: int = Field(12, alias="AUTH_SESSION_TTL_HOURS")
    auth_session_cookie_name: str = Field(
        "geoservice_session",
        alias="AUTH_SESSION_COOKIE_NAME",
    )
    auth_session_cookie_secure: bool = Field(
        False,
        alias="AUTH_SESSION_COOKIE_SECURE",
    )
    auth_session_cookie_samesite: str = Field(
        "lax",
        alias="AUTH_SESSION_COOKIE_SAMESITE",
    )
```

- [ ] **Step 4: Enable CORS credentials**

In `apps/backend/utility_service/web_api/main.py`, change the CORS middleware argument:

```python
    allow_credentials=True,
```

Keep `allow_origins=settings.cors_origins`; do not switch to wildcard origins.

- [ ] **Step 5: Run settings tests and backend auth import smoke**

Run:

```powershell
cd apps/backend
pytest utility_service/utils/tests/test_settings.py utility_service/web_api/tests/test_auth_api.py -q
```

Expected: PASS for settings and existing auth API tests.

---

### Task 2: Auth Session Model, Migration, And Repository

**Files:**

- Create: `apps/backend/utility_service/infrastructure/postgresql/models/auth_session.py`
- Create: `apps/backend/utility_service/infrastructure/postgresql/repositories/auth_session_repository.py`
- Create: `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/f8a7b6c5d4e3_auth_sessions.py`
- Create: `apps/backend/utility_service/infrastructure/tests/test_auth_session_repository.py`
- Modify: `apps/backend/utility_service/infrastructure/postgresql/alembic/env.py`

- [ ] **Step 1: Write failing repository SQL tests**

Create `apps/backend/utility_service/infrastructure/tests/test_auth_session_repository.py`:

```python
import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.dialects import postgresql

from utility_service.infrastructure.postgresql.repositories.auth_session_repository import (
    AuthSessionRepository,
)


class _ScalarOneOrNoneResult:
    def scalar_one_or_none(self):
        return None


class _ScalarOneResult:
    def scalar_one(self):
        return None


class CapturingSession:
    def __init__(self) -> None:
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)
        if "RETURNING" in str(statement):
            return _ScalarOneResult()
        return _ScalarOneOrNoneResult()


def compile_sql(statement) -> tuple[str, dict]:
    compiled = statement.compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"literal_binds": False},
    )
    return str(compiled), compiled.params


def test_get_active_session_by_hash_filters_revoked_and_expired() -> None:
    session = CapturingSession()
    repository = AuthSessionRepository(session)
    now = datetime(2026, 7, 3, 10, 0, tzinfo=timezone.utc)

    result = asyncio.run(
        repository.get_active_session_by_hash(
            session_token_hash="session-hash",
            now=now,
        )
    )

    assert result is None
    sql, params = compile_sql(session.statements[0])
    assert 'FROM "user".auth_sessions' in sql
    assert '"user".auth_sessions.session_token_hash =' in sql
    assert '"user".auth_sessions.revoked_at IS NULL' in sql
    assert '"user".auth_sessions.expires_at >' in sql
    assert params["session_token_hash_1"] == "session-hash"
    assert params["expires_at_1"] == now


def test_revoke_session_hash_updates_only_matching_active_session() -> None:
    session = CapturingSession()
    repository = AuthSessionRepository(session)
    now = datetime(2026, 7, 3, 10, 0, tzinfo=timezone.utc)

    asyncio.run(
        repository.revoke_session_hash(
            session_token_hash="session-hash",
            now=now,
        )
    )

    sql, params = compile_sql(session.statements[0])
    assert 'UPDATE "user".auth_sessions SET revoked_at=' in sql
    assert '"user".auth_sessions.session_token_hash =' in sql
    assert '"user".auth_sessions.revoked_at IS NULL' in sql
    assert params["session_token_hash_1"] == "session-hash"
    assert params["revoked_at"] == now


def test_create_session_hash_inserts_user_and_expiry() -> None:
    session = CapturingSession()
    repository = AuthSessionRepository(session)
    user_id = uuid4()
    expires_at = datetime(2026, 7, 3, 22, 0, tzinfo=timezone.utc)

    asyncio.run(
        repository.create_session(
            session_token_hash="session-hash",
            user_id=user_id,
            expires_at=expires_at,
        )
    )

    sql, params = compile_sql(session.statements[0])
    assert 'INSERT INTO "user".auth_sessions' in sql
    assert "session_token_hash" in sql
    assert "user_id" in sql
    assert "expires_at" in sql
    assert params["session_token_hash"] == "session-hash"
    assert params["user_id"] == user_id
    assert params["expires_at"] == expires_at
```

- [ ] **Step 2: Run repository tests and verify failure**

Run:

```powershell
cd apps/backend
pytest utility_service/infrastructure/tests/test_auth_session_repository.py -q
```

Expected: FAIL with `ModuleNotFoundError` for `auth_session_repository`.

- [ ] **Step 3: Create SQLAlchemy model**

Create `apps/backend/utility_service/infrastructure/postgresql/models/auth_session.py`:

```python
from __future__ import annotations

import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    __table_args__ = (
        UniqueConstraint(
            "session_token_hash",
            name="uq_auth_sessions_session_token_hash",
        ),
        Index("ix_auth_sessions_expires_at", "expires_at"),
        Index("ix_auth_sessions_user_id", "user_id"),
        {"schema": "user"},
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    session_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
```

- [ ] **Step 4: Create repository**

Create `apps/backend/utility_service/infrastructure/postgresql/repositories/auth_session_repository.py`:

```python
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.auth_session import AuthSession


class AuthSessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(
        self,
        *,
        session_token_hash: str,
        user_id: UUID,
        expires_at: datetime,
    ) -> AuthSession:
        stmt = (
            insert(AuthSession)
            .values(
                session_token_hash=session_token_hash,
                user_id=user_id,
                expires_at=expires_at,
            )
            .returning(AuthSession)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_active_session_by_hash(
        self,
        *,
        session_token_hash: str,
        now: datetime,
    ) -> AuthSession | None:
        stmt = (
            select(AuthSession)
            .where(AuthSession.session_token_hash == session_token_hash)
            .where(AuthSession.revoked_at.is_(None))
            .where(AuthSession.expires_at > now)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_session_hash(
        self,
        *,
        session_token_hash: str,
        now: datetime,
    ) -> None:
        stmt = (
            update(AuthSession)
            .where(AuthSession.session_token_hash == session_token_hash)
            .where(AuthSession.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await self.session.execute(stmt)

    async def mark_session_used(
        self,
        *,
        session_token_hash: str,
        now: datetime,
    ) -> None:
        stmt = (
            update(AuthSession)
            .where(AuthSession.session_token_hash == session_token_hash)
            .where(AuthSession.revoked_at.is_(None))
            .values(last_used_at=now)
        )
        await self.session.execute(stmt)

    async def mark_session_rotated(
        self,
        *,
        session_token_hash: str,
        now: datetime,
    ) -> None:
        stmt = (
            update(AuthSession)
            .where(AuthSession.session_token_hash == session_token_hash)
            .where(AuthSession.revoked_at.is_(None))
            .values(revoked_at=now, rotated_at=now, last_used_at=now)
        )
        await self.session.execute(stmt)
```

- [ ] **Step 5: Create Alembic migration**

Create `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/f8a7b6c5d4e3_auth_sessions.py`:

```python
"""add auth sessions

Revision ID: f8a7b6c5d4e3
Revises: a6f4c9b8d2e1
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f8a7b6c5d4e3"
down_revision: Union[str, Sequence[str], None] = "a6f4c9b8d2e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_token_hash", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rotated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "session_token_hash",
            name="uq_auth_sessions_session_token_hash",
        ),
        schema="user",
    )
    op.create_index(
        "ix_auth_sessions_expires_at",
        "auth_sessions",
        ["expires_at"],
        schema="user",
    )
    op.create_index(
        "ix_auth_sessions_user_id",
        "auth_sessions",
        ["user_id"],
        schema="user",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_auth_sessions_user_id",
        table_name="auth_sessions",
        schema="user",
    )
    op.drop_index(
        "ix_auth_sessions_expires_at",
        table_name="auth_sessions",
        schema="user",
    )
    op.drop_table("auth_sessions", schema="user")
```

- [ ] **Step 6: Import model in Alembic env**

Add this import to `apps/backend/utility_service/infrastructure/postgresql/alembic/env.py` near the other model imports:

```python
from utility_service.infrastructure.postgresql.models.auth_session import (  # noqa: E402, F401
    AuthSession,
)
```

- [ ] **Step 7: Run repository tests**

Run:

```powershell
cd apps/backend
pytest utility_service/infrastructure/tests/test_auth_session_repository.py -q
```

Expected: PASS.

---

### Task 3: Auth Session Service

**Files:**

- Create: `apps/backend/utility_service/use_cases/services/auth_session_service.py`
- Create: `apps/backend/utility_service/use_cases/schemas/auth/auth_session_out.py`
- Create: `apps/backend/utility_service/use_cases/tests/test_auth_session_service.py`
- Modify: `apps/backend/utility_service/use_cases/deps.py`

- [ ] **Step 1: Write failing service tests**

Create `apps/backend/utility_service/use_cases/tests/test_auth_session_service.py`:

```python
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from utility_service.use_cases.domain.exceptions.auth_api_error import AuthApiError
from utility_service.use_cases.schemas.auth.auth_session_out import (
    IssuedAuthSessionOut,
    RefreshedAuthSessionOut,
)
from utility_service.use_cases.services.auth_session_service import (
    AuthSessionService,
    hash_auth_session_token,
)


class FakeSession:
    def __init__(self) -> None:
        self.begin_calls = 0

    @asynccontextmanager
    async def begin(self):
        self.begin_calls += 1
        yield self


def test_hash_auth_session_token_is_sha256_hex() -> None:
    value = hash_auth_session_token("session-token")

    assert value == "c101e911469c969171040b50d70543313cf968fdef5bacc780776f8fb399ab36"
    assert len(value) == 64


def test_issue_session_creates_hash_and_12_hour_expiry() -> None:
    session = FakeSession()
    repository = AsyncMock()
    user = SimpleNamespace(id=uuid4())
    service = AuthSessionService(
        session=session,
        session_repository=repository,
        user_repository=AsyncMock(),
        ttl_hours=12,
    )

    result = asyncio.run(service.issue_session(user))

    assert isinstance(result, IssuedAuthSessionOut)
    assert result.token
    assert result.expires_at > datetime.now(timezone.utc) + timedelta(hours=11)
    repository.create_session.assert_awaited_once()
    kwargs = repository.create_session.await_args.kwargs
    assert kwargs["session_token_hash"] == hash_auth_session_token(result.token)
    assert kwargs["user_id"] == user.id
    assert kwargs["expires_at"] == result.expires_at
    assert session.begin_calls == 1


def test_refresh_session_rotates_token_and_returns_user() -> None:
    session = FakeSession()
    old_token = "old-session-token"
    user_id = uuid4()
    user = SimpleNamespace(
        id=user_id,
        email="editor@example.local",
        role="editor",
        is_active=True,
    )
    repository = AsyncMock()
    repository.get_active_session_by_hash.return_value = SimpleNamespace(user_id=user_id)
    user_repository = AsyncMock()
    user_repository.get_by_id.return_value = user
    service = AuthSessionService(
        session=session,
        session_repository=repository,
        user_repository=user_repository,
        ttl_hours=12,
    )

    result = asyncio.run(service.refresh_session(old_token))

    assert isinstance(result, RefreshedAuthSessionOut)
    assert result.user is user
    assert result.token
    assert result.token != old_token
    repository.mark_session_rotated.assert_awaited_once()
    repository.create_session.assert_awaited_once()
    assert session.begin_calls == 1


def test_refresh_session_rejects_missing_or_inactive_session() -> None:
    service = AuthSessionService(
        session=FakeSession(),
        session_repository=AsyncMock(get_active_session_by_hash=AsyncMock(return_value=None)),
        user_repository=AsyncMock(),
        ttl_hours=12,
    )

    with pytest.raises(AuthApiError) as exc_info:
        asyncio.run(service.refresh_session("missing-token"))

    assert exc_info.value.status_code == 401
    assert exc_info.value.code == "AUTH_REQUIRED"


def test_refresh_session_rejects_inactive_user() -> None:
    user_id = uuid4()
    repository = AsyncMock()
    repository.get_active_session_by_hash.return_value = SimpleNamespace(user_id=user_id)
    user_repository = AsyncMock()
    user_repository.get_by_id.return_value = SimpleNamespace(
        id=user_id,
        role="editor",
        is_active=False,
    )
    service = AuthSessionService(
        session=FakeSession(),
        session_repository=repository,
        user_repository=user_repository,
        ttl_hours=12,
    )

    with pytest.raises(AuthApiError) as exc_info:
        asyncio.run(service.refresh_session("session-token"))

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "USER_INACTIVE"


def test_revoke_session_is_idempotent_for_empty_token() -> None:
    repository = AsyncMock()
    service = AuthSessionService(
        session=FakeSession(),
        session_repository=repository,
        user_repository=AsyncMock(),
        ttl_hours=12,
    )

    asyncio.run(service.revoke_session(None))

    repository.revoke_session_hash.assert_not_awaited()
```

- [ ] **Step 2: Run service tests and verify failure**

Run:

```powershell
cd apps/backend
pytest utility_service/use_cases/tests/test_auth_session_service.py -q
```

Expected: FAIL with `ModuleNotFoundError` for `auth_session_out`.

- [ ] **Step 3: Create service**

Create `apps/backend/utility_service/use_cases/schemas/auth/auth_session_out.py`:

```python
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class IssuedAuthSessionOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str
    expires_at: datetime


class RefreshedAuthSessionOut(IssuedAuthSessionOut):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    user: Any
```

Create `apps/backend/utility_service/use_cases/services/auth_session_service.py`:

```python
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from typing import Any

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.repositories.auth_session_repository import (
    AuthSessionRepository,
)
from utility_service.infrastructure.postgresql.repositories.user_repository import UserRepository
from utility_service.use_cases.domain.exceptions.auth_api_error import AuthApiError
from utility_service.use_cases.schemas.auth.auth_session_out import (
    IssuedAuthSessionOut,
    RefreshedAuthSessionOut,
)
from utility_service.utils.settings import settings


def hash_auth_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class AuthSessionService:
    def __init__(
        self,
        session: AsyncSession,
        session_repository: AuthSessionRepository,
        user_repository: UserRepository,
        ttl_hours: int | None = None,
    ):
        self.session = session
        self.session_repository = session_repository
        self.user_repository = user_repository
        self.ttl_hours = ttl_hours if ttl_hours is not None else settings.auth_session_ttl_hours

    async def issue_session(self, user: Any) -> IssuedAuthSessionOut:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=self.ttl_hours)
        async with self.session.begin():
            await self.session_repository.create_session(
                session_token_hash=hash_auth_session_token(token),
                user_id=user.id,
                expires_at=expires_at,
            )
        return IssuedAuthSessionOut(token=token, expires_at=expires_at)

    async def refresh_session(self, token: str | None) -> RefreshedAuthSessionOut:
        if not token:
            raise self._auth_required()

        old_hash = hash_auth_session_token(token)
        new_token = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        new_expires_at = now + timedelta(hours=self.ttl_hours)

        async with self.session.begin():
            session_row = await self.session_repository.get_active_session_by_hash(
                session_token_hash=old_hash,
                now=now,
            )
            if session_row is None:
                raise self._auth_required()

            user = await self.user_repository.get_by_id(session_row.user_id)
            if user is None:
                raise self._auth_required()
            if not user.is_active:
                raise AuthApiError(
                    status.HTTP_403_FORBIDDEN,
                    "USER_INACTIVE",
                    "Учетная запись отключена.",
                )

            await self.session_repository.mark_session_rotated(
                session_token_hash=old_hash,
                now=now,
            )
            await self.session_repository.create_session(
                session_token_hash=hash_auth_session_token(new_token),
                user_id=user.id,
                expires_at=new_expires_at,
            )

        return RefreshedAuthSessionOut(
            token=new_token,
            expires_at=new_expires_at,
            user=user,
        )

    async def revoke_session(self, token: str | None) -> None:
        if not token:
            return

        async with self.session.begin():
            await self.session_repository.revoke_session_hash(
                session_token_hash=hash_auth_session_token(token),
                now=datetime.now(timezone.utc),
            )

    def _auth_required(self) -> AuthApiError:
        return AuthApiError(401, "AUTH_REQUIRED", "Сессия недействительна.")
```

- [ ] **Step 4: Add dependency factory**

In `apps/backend/utility_service/use_cases/deps.py`, add imports:

```python
from utility_service.infrastructure.postgresql.repositories.auth_session_repository import (
    AuthSessionRepository,
)
from utility_service.use_cases.services.auth_session_service import AuthSessionService
```

Add factory after `get_auth_service`:

```python
def get_auth_session_service(
    session: AsyncSession = Depends(get_session),
) -> AuthSessionService:
    return AuthSessionService(
        session,
        AuthSessionRepository(session),
        UserRepository(session),
    )
```

- [ ] **Step 5: Run service tests**

Run:

```powershell
cd apps/backend
pytest utility_service/use_cases/tests/test_auth_session_service.py -q
```

Expected: PASS.

---

### Task 4: Auth API Cookie Login, Refresh, And Logout

**Files:**

- Modify: `apps/backend/utility_service/web_api/api/auth.py`
- Modify: `apps/backend/utility_service/web_api/tests/test_auth_api.py`

- [ ] **Step 1: Write failing API tests**

Append these helpers and tests to `apps/backend/utility_service/web_api/tests/test_auth_api.py`:

```python
from types import SimpleNamespace
from uuid import uuid4

from utility_service.use_cases.deps import get_auth_session_service
```

Add this app builder for routes that need both auth services:

```python
def build_auth_session_app(auth_service: object, auth_session_service: object) -> FastAPI:
    app = FastAPI()
    install_exception_handlers(app)
    app.include_router(auth_router)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_auth_session_service] = lambda: auth_session_service
    return app
```

Add tests:

```python
def test_login_sets_http_only_session_cookie_and_returns_access_token() -> None:
    user = SimpleNamespace(
        id=uuid4(),
        email="editor@example.local",
        role=SimpleNamespace(value="editor"),
        is_active=True,
    )
    auth_service = AsyncMock()
    auth_service.authenticate_user.return_value = user
    auth_session_service = AsyncMock()
    auth_session_service.issue_session.return_value = SimpleNamespace(token="raw-session-token")

    response = TestClient(build_auth_session_app(auth_service, auth_session_service)).post(
        "/api/v1/auth/login",
        json={"email": "editor@example.local", "password": "editor-password"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["user"] == {
        "id": str(user.id),
        "email": "editor@example.local",
        "role": "editor",
    }
    assert "refresh_token" not in body
    set_cookie = response.headers["set-cookie"]
    assert "geoservice_session=raw-session-token" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie
    assert "Path=/api/v1/auth" in set_cookie
    assert "Max-Age=43200" in set_cookie


def test_refresh_session_rotates_cookie_and_returns_access_token() -> None:
    user = SimpleNamespace(
        id=uuid4(),
        email="reviewer@example.local",
        role=SimpleNamespace(value="reviewer"),
        is_active=True,
    )
    auth_service = AsyncMock()
    auth_session_service = AsyncMock()
    auth_session_service.refresh_session.return_value = SimpleNamespace(
        token="new-session-token",
        user=user,
    )
    client = TestClient(build_auth_session_app(auth_service, auth_session_service))

    response = client.post(
        "/api/v1/auth/session/refresh",
        cookies={"geoservice_session": "old-session-token"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"]
    set_cookie = response.headers["set-cookie"]
    assert "geoservice_session=new-session-token" in set_cookie
    assert "HttpOnly" in set_cookie
    auth_session_service.refresh_session.assert_awaited_once_with("old-session-token")


def test_refresh_without_cookie_returns_structured_401() -> None:
    auth_service = AsyncMock()
    auth_session_service = AsyncMock()
    auth_session_service.refresh_session.side_effect = AuthApiError(
        401,
        "AUTH_REQUIRED",
        "Сессия недействительна.",
    )

    response = TestClient(build_auth_session_app(auth_service, auth_session_service)).post(
        "/api/v1/auth/session/refresh",
        headers={"X-Correlation-ID": "refresh-correlation-id"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "code": "AUTH_REQUIRED",
        "message": "Сессия недействительна.",
        "correlationId": "refresh-correlation-id",
    }


def test_logout_revokes_session_and_clears_cookie() -> None:
    auth_service = AsyncMock()
    auth_session_service = AsyncMock()
    client = TestClient(build_auth_session_app(auth_service, auth_session_service))

    response = client.post(
        "/api/v1/auth/logout",
        cookies={"geoservice_session": "raw-session-token"},
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    auth_session_service.revoke_session.assert_awaited_once_with("raw-session-token")
    set_cookie = response.headers["set-cookie"]
    assert "geoservice_session=" in set_cookie
    assert "Max-Age=0" in set_cookie
    assert "Path=/api/v1/auth" in set_cookie
```

- [ ] **Step 2: Run auth API tests and verify failure**

Run:

```powershell
cd apps/backend
pytest utility_service/web_api/tests/test_auth_api.py -q
```

Expected: FAIL because `get_auth_session_service`, cookie helpers, refresh route, and logout route are not wired.

- [ ] **Step 3: Add imports and cookie helpers**

In `apps/backend/utility_service/web_api/api/auth.py`, extend imports:

```python
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from utility_service.use_cases.deps import get_auth_service, get_auth_session_service
from utility_service.use_cases.services.auth_session_service import AuthSessionService
```

Add helper functions near `SUPPORTED_AUTH_ROLES`:

```python
SESSION_COOKIE_PATH = "/api/v1/auth"


def _cookie_max_age_seconds() -> int:
    return settings.auth_session_ttl_hours * 60 * 60


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.auth_session_cookie_name,
        value=token,
        max_age=_cookie_max_age_seconds(),
        httponly=True,
        secure=settings.auth_session_cookie_secure,
        samesite=settings.auth_session_cookie_samesite,
        path=SESSION_COOKIE_PATH,
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.auth_session_cookie_name,
        path=SESSION_COOKIE_PATH,
        httponly=True,
        secure=settings.auth_session_cookie_secure,
        samesite=settings.auth_session_cookie_samesite,
    )
```

- [ ] **Step 4: Update login route to set cookie**

Change the login signature and body in `auth.py`:

```python
@auth_router.post("/login", response_model=AuthSuccessOut)
async def login(
    body: AuthLoginIn,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    auth_session_service: AuthSessionService = Depends(get_auth_session_service),
) -> AuthSuccessOut:
    user = await auth_service.authenticate_user(body.email, body.password)
    session = await auth_session_service.issue_session(user)
    set_session_cookie(response, session.token)
    token = create_access_token(str(user.id), _role_value(user))
    return AuthSuccessOut(
        access_token=token,
        token_type="bearer",
        user=AuthUserOut(
            id=str(user.id),
            email=user.email,
            role=_role_value(user),
        ),
    )
```

- [ ] **Step 5: Add refresh and logout routes**

Add below `login` and before `me`:

```python
@auth_router.post("/session/refresh", response_model=AuthSuccessOut)
async def refresh_session(
    response: Response,
    session_token: str | None = Cookie(
        default=None,
        alias=settings.auth_session_cookie_name,
    ),
    auth_session_service: AuthSessionService = Depends(get_auth_session_service),
) -> AuthSuccessOut:
    refreshed = await auth_session_service.refresh_session(session_token)
    set_session_cookie(response, refreshed.token)
    user = refreshed.user
    token = create_access_token(str(user.id), _role_value(user))
    return AuthSuccessOut(
        access_token=token,
        token_type="bearer",
        user=AuthUserOut(
            id=str(user.id),
            email=user.email,
            role=_role_value(user),
        ),
    )


@auth_router.post("/logout")
async def logout(
    response: Response,
    session_token: str | None = Cookie(
        default=None,
        alias=settings.auth_session_cookie_name,
    ),
    auth_session_service: AuthSessionService = Depends(get_auth_session_service),
) -> dict[str, bool]:
    await auth_session_service.revoke_session(session_token)
    clear_session_cookie(response)
    return {"ok": True}
```

- [ ] **Step 6: Run auth API tests**

Run:

```powershell
cd apps/backend
pytest utility_service/web_api/tests/test_auth_api.py utility_service/web_api/tests/test_auth_access.py -q
```

Expected: PASS.

---

### Task 5: Frontend Auth API Session Endpoints

**Files:**

- Modify: `apps/frontend/src/api/auth.ts`
- Create: `apps/frontend/src/api/auth.test.ts`

- [ ] **Step 1: Write failing frontend API tests**

Create `apps/frontend/src/api/auth.test.ts`:

```ts
import { beforeEach, describe, expect, it, vi } from "vitest";

const postMock = vi.hoisted(() => vi.fn());

vi.mock("@/api/http", () => ({
  http: {
    post: postMock,
    get: vi.fn(),
  },
}));

describe("auth API", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
  });

  it("refreshSession sends browser credentials", async () => {
    postMock.mockResolvedValue({
      data: {
        access_token: "token-1",
        token_type: "bearer",
        user: {
          id: "user-1",
          email: "editor@example.local",
          role: "editor",
        },
      },
    });

    const { refreshSession } = await import("@/api/auth");

    const result = await refreshSession();

    expect(result.access_token).toBe("token-1");
    expect(postMock).toHaveBeenCalledWith(
      "/api/v1/auth/session/refresh",
      undefined,
      { withCredentials: true },
    );
  });

  it("logoutSession sends browser credentials", async () => {
    postMock.mockResolvedValue({ data: { ok: true } });

    const { logoutSession } = await import("@/api/auth");

    await logoutSession();

    expect(postMock).toHaveBeenCalledWith(
      "/api/v1/auth/logout",
      undefined,
      { withCredentials: true },
    );
  });
});
```

- [ ] **Step 2: Run frontend API tests and verify failure**

Run:

```powershell
cd apps/frontend
npm test -- src/api/auth.test.ts
```

Expected: FAIL because `refreshSession` and `logoutSession` are not exported.

- [ ] **Step 3: Add session API functions**

In `apps/frontend/src/api/auth.ts`, append:

```ts
export async function refreshSession() {
  const response = await http.post<AuthLoginResponse>(
    "/api/v1/auth/session/refresh",
    undefined,
    { withCredentials: true },
  );
  return response.data;
}

export async function logoutSession() {
  await http.post("/api/v1/auth/logout", undefined, {
    withCredentials: true,
  });
}
```

Update `login()` so the browser accepts the session cookie from the cross-origin API response:

```ts
  const response = await http.post<AuthLoginResponse>(
    "/api/v1/auth/login",
    {
      email,
      password,
    },
    { withCredentials: true },
  );
```

Add this assertion to `auth.test.ts`:

```ts
  it("login sends browser credentials so Set-Cookie is accepted", async () => {
    postMock.mockResolvedValue({
      data: {
        access_token: "token-1",
        token_type: "bearer",
        user: {
          id: "user-1",
          email: "editor@example.local",
          role: "editor",
        },
      },
    });

    const { login } = await import("@/api/auth");

    await login("editor@example.local", "editor-password");

    expect(postMock).toHaveBeenCalledWith(
      "/api/v1/auth/login",
      {
        email: "editor@example.local",
        password: "editor-password",
      },
      { withCredentials: true },
    );
  });
```

- [ ] **Step 4: Run frontend API tests**

Run:

```powershell
cd apps/frontend
npm test -- src/api/auth.test.ts
```

Expected: PASS.

---

### Task 6: Frontend Auth Store In-Memory Token

**Files:**

- Modify: `apps/frontend/src/stores/auth.ts`
- Modify: `apps/frontend/src/stores/auth.test.ts`

- [ ] **Step 1: Update auth store mocks and write failing tests**

In `apps/frontend/src/stores/auth.test.ts`, change the auth API mocks:

```ts
const loginMock = vi.fn();
const fetchMeMock = vi.fn();
const refreshSessionMock = vi.fn();
const logoutSessionMock = vi.fn();
const resetWorkOrdersMock = vi.hoisted(() => vi.fn());

vi.mock("@/api/auth", () => ({
  login: loginMock,
  fetchMe: fetchMeMock,
  refreshSession: refreshSessionMock,
  logoutSession: logoutSessionMock,
}));
```

Replace the old "stores token and full user object after successful login" test with:

```ts
  it("stores access token only in memory after successful login", async () => {
    loginMock.mockResolvedValue({
      access_token: "token-1",
      token_type: "bearer",
      user: {
        id: "user-1",
        email: "editor@example.com",
        role: "editor",
      },
    });

    const { useAuthStore } = await import("@/stores/auth");
    const store = useAuthStore();

    await store.loginWithPassword("editor@example.com", "editor-password");

    expect(store.token).toBe("token-1");
    expect(store.user).toEqual({
      id: "user-1",
      email: "editor@example.com",
      role: "editor",
    });
    expect(store.isAuthenticated).toBe(true);
    expect(localStorage.setItem).not.toHaveBeenCalledWith("access_token", "token-1");
    expect(localStorage.setItem).not.toHaveBeenCalledWith(
      "auth_user",
      expect.any(String),
    );
  });
```

Replace restore tests that pre-seed `localStorage` with cookie refresh tests:

```ts
  it("restores session through refresh endpoint without reading localStorage token", async () => {
    refreshSessionMock.mockResolvedValue({
      access_token: "token-2",
      token_type: "bearer",
      user: {
        id: "user-2",
        email: "marina.reviewer@example.local",
        role: "reviewer",
      },
    });

    const { useAuthStore } = await import("@/stores/auth");
    const store = useAuthStore();

    await store.restoreSession();

    expect(localStorage.getItem).not.toHaveBeenCalledWith("access_token");
    expect(refreshSessionMock).toHaveBeenCalledTimes(1);
    expect(store.token).toBe("token-2");
    expect(store.user).toEqual({
      id: "user-2",
      email: "marina.reviewer@example.local",
      role: "reviewer",
    });
    expect(store.sessionError).toBeNull();
    expect(store.isReady).toBe(true);
  });

  it("treats refresh 401 as logged out without session error", async () => {
    refreshSessionMock.mockRejectedValue({
      isAxiosError: true,
      response: { status: 401 },
    });

    const { useAuthStore } = await import("@/stores/auth");
    const store = useAuthStore();

    await store.restoreSession();

    expect(store.token).toBeNull();
    expect(store.user).toBeNull();
    expect(store.sessionError).toBeNull();
    expect(store.isReady).toBe(true);
  });

  it("keeps retry UX when refresh fails without 401", async () => {
    refreshSessionMock.mockRejectedValue({
      isAxiosError: true,
      response: { status: 503 },
    });

    const { useAuthStore } = await import("@/stores/auth");
    const store = useAuthStore();

    await store.restoreSession();

    expect(store.token).toBeNull();
    expect(store.sessionError).toBe(
      "Сейчас не удалось восстановить сессию. Попробуйте ещё раз.",
    );
    expect(store.isReady).toBe(true);
  });

  it("calls backend logout and clears memory state", async () => {
    const { useAuthStore } = await import("@/stores/auth");
    const store = useAuthStore();
    store.token = "token-1";
    store.user = {
      id: "user-1",
      email: "editor@example.com",
      role: "editor",
    };

    await store.logout();

    expect(logoutSessionMock).toHaveBeenCalledTimes(1);
    expect(store.token).toBeNull();
    expect(store.user).toBeNull();
    expect(resetWorkOrdersMock).toHaveBeenCalledTimes(1);
  });
```

- [ ] **Step 2: Run auth store tests and verify failure**

Run:

```powershell
cd apps/frontend
npm test -- src/stores/auth.test.ts
```

Expected: FAIL because `auth.ts` still reads/writes `localStorage` and `restoreSession()` calls `fetchMe()`.

- [ ] **Step 3: Modify auth store imports and state initialization**

In `apps/frontend/src/stores/auth.ts`, change imports:

```ts
import {
  fetchMe,
  login,
  logoutSession,
  refreshSession,
  type AuthUser,
} from "@/api/auth";
```

Remove these constants and functions from `apps/frontend/src/stores/auth.ts`:

```ts
const ACCESS_TOKEN_KEY = "access_token";
const AUTH_USER_KEY = "auth_user";

function readStoredToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

function readStoredUser(): AuthUser | null {
  const rawValue = localStorage.getItem(AUTH_USER_KEY);
  if (!rawValue) {
    return null;
  }

  try {
    return JSON.parse(rawValue) as AuthUser;
  } catch {
    localStorage.removeItem(AUTH_USER_KEY);
    return null;
  }
}
```

Change initial state:

```ts
    state: (): AuthState => ({
      token: null,
      user: null,
      isReady: false,
      isRestoring: false,
      sessionError: null,
    }),
```

- [ ] **Step 4: Remove storage writes from setters**

Change `setAuth`:

```ts
      setAuth(token: string, user: AuthUser) {
        const previousUserId = authUserId(this.user);

        this.token = token;
        this.user = user;
        this.sessionError = null;
        resetWorkOrdersIfUserIdChanged(previousUserId, user.id);
      },
```

Change `setUser`:

```ts
      setUser(user: AuthUser | null) {
        const previousUserId = authUserId(this.user);

        this.user = user;
        resetWorkOrdersIfUserIdChanged(previousUserId, authUserId(user));
      },
```

- [ ] **Step 5: Make restoreSession cookie-refresh based**

Replace `restoreSession()`:

```ts
      async restoreSession() {
        this.sessionError = null;
        this.isRestoring = true;

        try {
          const result = await refreshSession();
          this.setAuth(result.access_token, result.user);
        } catch (error: unknown) {
          if (axios.isAxiosError(error)) {
            const status = error.response?.status;
            if (status === 401) {
              this.token = null;
              this.setUser(null);
              return;
            }
          }

          this.token = null;
          this.setUser(null);
          this.sessionError =
            "Сейчас не удалось восстановить сессию. Попробуйте ещё раз.";
        } finally {
          this.isReady = true;
          this.isRestoring = false;
        }
      },
```

- [ ] **Step 6: Make logout async and best-effort**

Replace `logout()` with:

```ts
      async logout() {
        try {
          await logoutSession();
        } catch {
          // Local logout must still complete if the server is unavailable.
        } finally {
          const previousUserId = authUserId(this.user);

          this.token = null;
          this.user = null;
          this.sessionError = null;
          this.isReady = true;
          this.isRestoring = false;
          resetWorkOrdersIfUserIdChanged(previousUserId, null);
        }
      },
```

Because callers currently use `@click="auth.logout"` and response interceptor calls `auth.logout()`, returning a Promise is acceptable. Do not await it inside axios interceptor to avoid blocking rejection.

- [ ] **Step 7: Run frontend auth store tests**

Run:

```powershell
cd apps/frontend
npm test -- src/stores/auth.test.ts
```

Expected: PASS after replacing the old `localStorage` restore tests with the cookie refresh tests from Step 1 and deleting any remaining tests that pre-seed the `access_token` key in storage.

- [ ] **Step 8: Run App/Login tests for async logout compatibility**

Run:

```powershell
cd apps/frontend
npm test -- src/App.test.ts src/components/LoginScreen.test.ts
```

Expected: PASS.

---

### Task 7: Full Regression And Documentation Update

**Files:**

- Verify: backend and frontend tests.
- Review through `/ingest repository-change`: `Code_wiki/архитектура/api_and_realtime.md`, `Code_wiki/архитектура/frontend.md`, `Code_wiki/состояние_проекта/repository_change_ingest.md`.

- [ ] **Step 1: Run backend focused regression**

Run:

```powershell
cd apps/backend
pytest utility_service/utils/tests/test_settings.py utility_service/infrastructure/tests/test_auth_session_repository.py utility_service/use_cases/tests/test_auth_session_service.py utility_service/web_api/tests/test_auth_api.py utility_service/web_api/tests/test_auth_access.py utility_service/web_api/tests/test_ws_layers.py -q
```

Expected: PASS. This confirms settings, session persistence, auth routes, Bearer auth, and WebSocket ticket auth.

- [ ] **Step 2: Run frontend focused regression**

Run:

```powershell
cd apps/frontend
npm test -- src/api/auth.test.ts src/stores/auth.test.ts src/App.test.ts src/components/LoginScreen.test.ts src/composables/map/useLayerRealtime.test.ts
```

Expected: PASS. This confirms cookie refresh API, in-memory auth store, startup UX, login errors, and Bearer-based WebSocket ticket issue.

- [ ] **Step 3: Run broader static checks**

Run:

```powershell
cd apps/frontend
npm run typecheck
```

Expected: PASS.

Run:

```powershell
cd apps/backend
pytest utility_service -q
```

Expected: PASS. If this is too slow for the execution environment, record the focused regression output and the reason broader pytest was skipped.

- [ ] **Step 4: Decide whether repository-change ingest is required**

This implementation changes durable technical knowledge: auth persistence moves from `localStorage` token restore to `HttpOnly` session cookie restore while REST remains Bearer-based. Invoke `/ingest repository-change` only after code and tests are complete. The ingest must update Code_wiki knowledge documentation only, not code/config/tests.

Expected Code_wiki facts to preserve:

```markdown
- Auth login sets `HttpOnly` `geoservice_session` cookie and returns short access token.
- Frontend stores access token only in Pinia memory, not `localStorage`.
- Reload restore uses `POST /api/v1/auth/session/refresh` with cookie.
- REST and WebSocket ticket issue remain Bearer-based.
```

- [ ] **Step 5: Final status**

Run:

```powershell
git status --short
```

Expected: working tree contains only the intended implementation, test, spec, plan, and optional Code_wiki changes.
