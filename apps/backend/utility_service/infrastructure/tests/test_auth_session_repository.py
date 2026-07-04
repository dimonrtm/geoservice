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
    def __init__(self, row):
        self.row = row

    def scalar_one(self):
        return self.row

    def scalar_one_or_none(self):
        return self.row


class CapturingSession:
    def __init__(self) -> None:
        self.statements = []
        self.created_row = object()

    async def execute(self, statement):
        self.statements.append(statement)
        if "RETURNING" in str(statement):
            return _ScalarOneResult(self.created_row)
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

    result = asyncio.run(
        repository.create_session(
            session_token_hash="session-hash",
            user_id=user_id,
            expires_at=expires_at,
        )
    )

    assert result is session.created_row
    sql, params = compile_sql(session.statements[0])
    assert 'INSERT INTO "user".auth_sessions' in sql
    assert "session_token_hash" in sql
    assert "user_id" in sql
    assert "expires_at" in sql
    assert params["session_token_hash"] == "session-hash"
    assert params["user_id"] == user_id
    assert params["expires_at"] == expires_at


def test_mark_session_used_updates_only_matching_active_session() -> None:
    session = CapturingSession()
    repository = AuthSessionRepository(session)
    now = datetime(2026, 7, 3, 10, 0, tzinfo=timezone.utc)

    asyncio.run(
        repository.mark_session_used(
            session_token_hash="session-hash",
            now=now,
        )
    )

    sql, params = compile_sql(session.statements[0])
    assert 'UPDATE "user".auth_sessions SET last_used_at=' in sql
    assert '"user".auth_sessions.session_token_hash =' in sql
    assert '"user".auth_sessions.revoked_at IS NULL' in sql
    assert '"user".auth_sessions.expires_at >' in sql
    assert params["session_token_hash_1"] == "session-hash"
    assert params["expires_at_1"] == now
    assert params["last_used_at"] == now


def test_mark_session_rotated_updates_and_returns_only_matching_active_session() -> None:
    session = CapturingSession()
    repository = AuthSessionRepository(session)
    now = datetime(2026, 7, 3, 10, 0, tzinfo=timezone.utc)

    result = asyncio.run(
        repository.mark_session_rotated(
            session_token_hash="session-hash",
            now=now,
        )
    )

    assert result is session.created_row
    sql, params = compile_sql(session.statements[0])
    assert 'UPDATE "user".auth_sessions SET revoked_at=' in sql
    assert "rotated_at=" in sql
    assert "last_used_at=" in sql
    assert '"user".auth_sessions.session_token_hash =' in sql
    assert '"user".auth_sessions.revoked_at IS NULL' in sql
    assert '"user".auth_sessions.expires_at >' in sql
    assert 'RETURNING "user".auth_sessions.id' in sql
    assert params["session_token_hash_1"] == "session-hash"
    assert params["expires_at_1"] == now
    assert params["revoked_at"] == now
    assert params["rotated_at"] == now
    assert params["last_used_at"] == now
