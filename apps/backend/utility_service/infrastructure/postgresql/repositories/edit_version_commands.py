"""Внутренние SQL-операции EditVersionRepository, без управления transaction."""

from copy import deepcopy
from dataclasses import fields
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.work_order import (
    EditVersionCommand,
    EditVersionCommandState,
)
from utility_service.infrastructure.postgresql.repository_rows.edit_version_command import (
    EditVersionCommandRow,
)


async def read_command(
    session: AsyncSession,
    command_id: UUID,
) -> EditVersionCommandRow | None:
    columns = [
        getattr(
            EditVersionCommand,
            field.name,
        )
        for field in fields(EditVersionCommandRow)
    ]
    row = (
        (await session.execute(select(*columns).where(EditVersionCommand.command_id == command_id)))
        .mappings()
        .one_or_none()
    )
    return EditVersionCommandRow(**deepcopy(dict(row))) if row is not None else None


async def insert_command(
    session: AsyncSession,
    *,
    version_id: UUID,
    command_id: UUID,
    feature_id: UUID,
    actor_id: UUID,
    fingerprint: str,
) -> bool:
    statement = (
        insert(EditVersionCommand)
        .values(
            command_id=command_id,
            edit_version_id=version_id,
            feature_id=feature_id,
            actor_user_id=actor_id,
            request_fingerprint=fingerprint,
            state=EditVersionCommandState.RUNNING,
        )
        .on_conflict_do_nothing(index_elements=[EditVersionCommand.command_id])
        .returning(EditVersionCommand.command_id)
    )
    return (await session.execute(statement)).scalar_one_or_none() is not None


async def finish_command(
    session: AsyncSession,
    *,
    version_id: UUID,
    command_id: UUID,
    payload: dict[str, Any],
) -> bool:
    statement = (
        update(EditVersionCommand)
        .where(
            EditVersionCommand.command_id == command_id,
            EditVersionCommand.edit_version_id == version_id,
            EditVersionCommand.state == EditVersionCommandState.RUNNING,
        )
        .values(
            state=EditVersionCommandState.SUCCEEDED,
            response_status=200,
            response_payload=deepcopy(payload),
            completed_at=func.now(),
        )
        .returning(EditVersionCommand.command_id)
        .execution_options(synchronize_session=False)
    )
    return (await session.execute(statement)).scalar_one_or_none() is not None
