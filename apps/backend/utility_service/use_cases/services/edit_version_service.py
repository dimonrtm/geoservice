from __future__ import annotations

from dataclasses import dataclass
from copy import deepcopy
from uuid import UUID

from utility_service.infrastructure.postgresql.repositories.edit_version_repository import (
    EditVersionRepository,
)

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from utility_service.domain_services.edit_geometry.policy import GeometryPolicy
from utility_service.domain_services.edit_geometry.types import (
    GeometryRuleError,
    InvalidGeometryContext,
)
from utility_service.infrastructure.postgresql.geometry_codec import (
    decode_geometry,
    geometry_to_geojson,
)
from utility_service.infrastructure.postgresql.repository_rows.edit_geometry import (
    RepositoryProtocolError,
    RepositoryRejection,
)
from utility_service.infrastructure.postgresql.repository_rows.edit_version_command import (
    EditVersionCommandRow,
)
from utility_service.use_cases.schemas.edit_version.geometry_save_in import GeometrySaveRequest
from utility_service.use_cases.schemas.edit_version.geometry_save_out import (
    SaveGeometryResult,
    SaveGeometryRejection,
    build_geometry_save_payload,
)
from utility_service.use_cases.services.edit_version_save_identity import (
    build_save_geometry_identity,
)

from utility_service.infrastructure.postgresql.models.user import User, UserRole
from utility_service.infrastructure.postgresql.models.work_order import (
    EditVersion,
    WorkOrder,
    WorkOrderStatus,
    EditVersionCommandState,
)
from utility_service.infrastructure.postgresql.repositories.default_state_repository import (
    DefaultStateRepository,
)
from utility_service.infrastructure.postgresql.repositories.user_repository import UserRepository
from utility_service.infrastructure.postgresql.repositories.work_order_repository import (
    WorkOrderRepository,
)
from utility_service.use_cases.domain.exceptions.work_order_api_error import WorkOrderApiError


@dataclass(frozen=True)
class OpenEditVersionResult:
    created: bool
    edit_version: EditVersion


OPEN_EDIT_VERSION_UNIQUE_CONSTRAINT = "uq_edit_versions_open_work_order"
POSTGRES_UNIQUE_VIOLATION = "23505"


class EditVersionService:
    def __init__(
        self,
        session: AsyncSession,
        user_repository: UserRepository,
        work_order_repository: WorkOrderRepository,
        default_state_repository: DefaultStateRepository,
        *,
        geometry_policy: GeometryPolicy,
        edit_version_repository: EditVersionRepository,
    ):
        self.session = session
        self.user_repository = user_repository
        self.work_order_repository = work_order_repository
        self.default_state_repository = default_state_repository
        self.geometry_policy = geometry_policy
        self.edit_version_repository = edit_version_repository

    async def save_geometry(
        self,
        *,
        work_order_id: UUID,
        edit_version_id: UUID,
        feature_id: UUID,
        actor_id: UUID,
        request: GeometrySaveRequest,
    ) -> SaveGeometryResult:
        async with self.session.begin():
            result = await self._save_geometry_locked(
                work_order_id=work_order_id,
                edit_version_id=edit_version_id,
                feature_id=feature_id,
                actor_id=actor_id,
                request=request,
            )
        # Domain failures are raised only AFTER their terminal row commits.
        if isinstance(
            result,
            SaveGeometryRejection,
        ):
            raise WorkOrderApiError(
                result.status_code,
                result.code,
                result.message,
            )
        return result

    async def _save_geometry_locked(
        self,
        *,
        work_order_id: UUID,
        edit_version_id: UUID,
        feature_id: UUID,
        actor_id: UUID,
        request: GeometrySaveRequest,
    ) -> SaveGeometryResult | SaveGeometryRejection:
        rejection = SaveGeometryRejection.from_code
        actor = await self.user_repository.get_by_id(actor_id)
        gate = None
        if actor is None or actor.role is not UserRole.EDITOR or not actor.is_active:
            gate = rejection(
                "ROLE_NOT_ALLOWED",
                "Роль пользователя не допускает операцию.",
            )
        repository = self.edit_version_repository
        root = await repository.lock_version(
            work_order_id=work_order_id,
            edit_version_id=edit_version_id,
        )
        if root is None:
            return gate or rejection(
                "EDIT_VERSION_NOT_FOUND",
                "Рабочая версия не найдена.",
            )
        context = await repository.read_context(
            root,
            feature_id=feature_id,
        )
        if isinstance(
            context,
            RepositoryRejection,
        ):
            return gate or rejection(
                context.code,
                context.reason,
            )
        if gate is None and context.assignee_user_id != actor_id:
            gate = rejection(
                "EDIT_VERSION_NOT_FOUND",
                "Рабочая версия не найдена.",
                retry_on_access_change=True,
            )
        if gate is None and (root.status != "open" or context.work_order_status != "in_progress"):
            gate = rejection(
                "SAVE_CONTEXT_CLOSED",
                "Контекст сохранения закрыт.",
            )

        command = await repository.get_command(
            root,
            command_id=request.command_id,
        )
        # Current guards mask any stored result, without rewriting its identity/outcome.
        if command is not None and gate is not None:
            return gate
        if command is not None:
            self._check_save_command_target(
                command,
                edit_version_id,
                feature_id,
                actor_id,
            )
        try:
            identity = build_save_geometry_identity(
                context,
                actor_id=actor_id,
                request=request,
                stored_fingerprint=command.request_fingerprint if command is not None else None,
            )
        except InvalidGeometryContext as error:
            # A stored geom-v1 cannot be compared without its immutable baseline.
            return gate or rejection(
                "WORK_ORDER_CONTEXT_INVALID",
                str(error),
            )
        if command is None:
            if await repository.command_has_history(
                root,
                command_id=request.command_id,
            ):
                return gate or rejection(
                    "COMMAND_ID_REUSED",
                    "Идентификатор занят другой командой.",
                )
            reserved = await repository.reserve_command(
                root,
                command_id=request.command_id,
                feature_id=feature_id,
                actor_id=actor_id,
                fingerprint=identity.fingerprint,
            )
            if not reserved:
                command = await repository.get_command(
                    root,
                    command_id=request.command_id,
                )
                if command is None:
                    if await repository.command_has_history(
                        root,
                        command_id=request.command_id,
                    ):
                        return gate or rejection(
                            "COMMAND_ID_REUSED",
                            "Идентификатор занят другой командой.",
                        )
                    raise RepositoryProtocolError(
                        "Результат конкурирующей команды больше недоступен."
                    )
                if gate is not None:
                    return gate
                self._check_save_command_target(
                    command,
                    edit_version_id,
                    feature_id,
                    actor_id,
                )
                try:
                    identity = build_save_geometry_identity(
                        context,
                        actor_id=actor_id,
                        request=request,
                        stored_fingerprint=command.request_fingerprint,
                    )
                except InvalidGeometryContext as error:
                    return rejection(
                        "WORK_ORDER_CONTEXT_INVALID",
                        str(error),
                    )
        if command is not None:
            if command.request_fingerprint != identity.fingerprint:
                self._reject_command_reuse()
            if command.state == EditVersionCommandState.REJECTED and command.retry_on_access_change:
                await repository.resume_access_command(
                    root,
                    command_id=request.command_id,
                )
            else:
                return self._replay_save(
                    command,
                    identity.fingerprint,
                )

        outcome = gate or identity.preparation_rejection
        # On contextless access resume the fingerprint skips baseline; domain preparation still runs.
        prepared = None
        if outcome is None:
            try:
                prepared = repository.prepare_candidate(
                    context,
                    request.geometry,
                )
                if isinstance(
                    prepared,
                    RepositoryRejection,
                ):
                    outcome = rejection(
                        prepared.code,
                        prepared.reason,
                    )
            except (GeometryRuleError, InvalidGeometryContext) as error:
                outcome = rejection(
                    (
                        error.code
                        if isinstance(
                            error,
                            GeometryRuleError,
                        )
                        else "WORK_ORDER_CONTEXT_INVALID"
                    ),
                    str(error),
                )
        if outcome is None and request.draft_version_token != str(root.draft_revision):
            outcome = rejection(
                "DRAFT_VERSION_STALE",
                "Рабочая версия изменилась. Обновите данные.",
            )
        if outcome is None:
            try:
                change = await repository.validate_candidate(
                    context,
                    prepared,
                )
                if isinstance(
                    change,
                    RepositoryRejection,
                ):
                    outcome = rejection(
                        change.code,
                        change.reason,
                    )
            except (GeometryRuleError, InvalidGeometryContext) as error:
                outcome = rejection(
                    (
                        error.code
                        if isinstance(
                            error,
                            GeometryRuleError,
                        )
                        else "WORK_ORDER_CONTEXT_INVALID"
                    ),
                    str(error),
                )
        if outcome is not None:
            await repository.reject_command(
                root,
                command_id=request.command_id,
                status_code=outcome.status_code,
                code=outcome.code,
                message=outcome.message,
                retry_on_access_change=outcome.retry_on_access_change,
            )
            return outcome

        # No domain-error conversion beyond this point: failures must roll back all writes.
        written = await repository.write_current(change)
        revision = (
            await repository.increment_revision(root) if written.changed else root.draft_revision
        )
        payload = build_geometry_save_payload(
            command_id=request.command_id,
            feature_id=feature_id,
            draft_revision=revision,
            operation=written.operation,
            geometry=geometry_to_geojson(decode_geometry(written.after_ewkb)),
        )
        await repository.complete_command(
            root,
            command_id=request.command_id,
            payload=payload,
        )
        if written.changed:
            await repository.append_change_event(
                root,
                command_id=request.command_id,
                feature_id=feature_id,
                actor_id=actor_id,
                change=written,
                draft_revision_after=revision,
            )
        return SaveGeometryResult(
            200,
            deepcopy(payload),
        )

    @staticmethod
    def _check_save_command_target(
        command: EditVersionCommandRow,
        edit_version_id: UUID,
        feature_id: UUID,
        actor_id: UUID,
    ) -> None:
        if (command.edit_version_id, command.feature_id, command.actor_user_id) != (
            edit_version_id,
            feature_id,
            actor_id,
        ):
            EditVersionService._reject_command_reuse()

    @staticmethod
    def _replay_save(
        command: EditVersionCommandRow,
        fingerprint: str,
    ) -> SaveGeometryResult | SaveGeometryRejection:
        if command.request_fingerprint != fingerprint:
            EditVersionService._reject_command_reuse()
        if command.state == EditVersionCommandState.SUCCEEDED:
            if command.response_status is None or command.response_payload is None:
                raise RepositoryProtocolError("Успешная команда не содержит результата.")
            return SaveGeometryResult(
                command.response_status,
                deepcopy(command.response_payload),
            )
        if command.state == EditVersionCommandState.REJECTED:
            if (
                command.response_status is None
                or command.rejection_code is None
                or command.rejection_message is None
            ):
                raise RepositoryProtocolError("Отклонённая команда не содержит результата.")
            return SaveGeometryRejection(
                command.response_status,
                command.rejection_code,
                command.rejection_message,
            )
        raise RepositoryProtocolError("Нельзя воспроизвести незавершённую команду.")

    @staticmethod
    def _reject_command_reuse() -> None:
        raise WorkOrderApiError(
            409,
            "COMMAND_ID_REUSED",
            "Идентификатор занят другой командой.",
        )

    async def open_for_work_order(
        self,
        work_order_id: UUID,
        actor_id: UUID,
    ) -> OpenEditVersionResult:
        try:
            return await self.open_for_work_order_locked(
                work_order_id,
                actor_id,
            )
        except IntegrityError as exc:
            if not self.is_open_edit_version_unique_violation(exc):
                raise
            return await self.recover_existing_open_edit_version(
                work_order_id,
                actor_id,
            )

    async def open_for_work_order_locked(
        self,
        work_order_id: UUID,
        actor_id: UUID,
    ) -> OpenEditVersionResult:
        async with self.session.begin():
            actor = await self.get_actor(actor_id)
            work_order = await self.get_visible_work_order(
                work_order_id,
                actor,
            )
            return await self.open_visible_work_order(
                work_order,
                actor,
            )

    async def open_visible_work_order(
        self,
        work_order: WorkOrder,
        actor: User,
    ) -> OpenEditVersionResult:
        existing = await self.edit_version_repository.get_open_edit_version(work_order.id)

        if work_order.status is WorkOrderStatus.IN_PROGRESS:
            if existing is None:
                self.raise_context_invalid()
            return await self.reopen_edit_version(existing)

        if work_order.status is not WorkOrderStatus.ASSIGNED:
            raise WorkOrderApiError(
                409,
                "WORK_ORDER_STATE_CONFLICT",
                "Состояние рабочей задачи не допускает операцию.",
            )

        if existing is not None:
            self.raise_context_invalid()

        default_state_aggregate = (
            await self.default_state_repository.get_active_aggregate_by_work_order_id(work_order.id)
        )
        if default_state_aggregate is None:
            self.raise_context_invalid()

        default_state = default_state_aggregate.state
        created = await self.edit_version_repository.create_open_edit_version(
            geometry_policy=self.geometry_policy,
            work_order_id=work_order.id,
            default_state_id=default_state.id,
            base_network_revision=default_state.base_network_revision,
            default_features=default_state_aggregate.features,
            default_associations=default_state_aggregate.associations,
            owner_user_id=actor.id,
        )
        work_order.status = WorkOrderStatus.IN_PROGRESS
        await self.work_order_repository.save(work_order)
        return OpenEditVersionResult(
            created=True,
            edit_version=created,
        )

    async def recover_existing_open_edit_version(
        self,
        work_order_id: UUID,
        actor_id: UUID,
    ) -> OpenEditVersionResult:
        async with self.session.begin():
            actor = await self.get_actor(actor_id)
            work_order = await self.get_visible_work_order(
                work_order_id,
                actor,
            )
            existing = await self.edit_version_repository.get_open_edit_version(work_order.id)
            if existing is None:
                self.raise_context_invalid()
            return await self.reopen_edit_version(existing)

    async def reopen_edit_version(
        self,
        edit_version: EditVersion,
    ) -> OpenEditVersionResult:
        await self.edit_version_repository.touch_edit_version(edit_version)
        return OpenEditVersionResult(
            created=False,
            edit_version=edit_version,
        )

    async def get_actor(
        self,
        actor_id: UUID,
    ) -> User:
        actor = await self.user_repository.get_by_id(actor_id)
        if actor is None:
            raise WorkOrderApiError(
                404,
                "WORK_ORDER_ACTOR_NOT_FOUND",
                "Пользователь не найден.",
            )
        self.require_active_editor(actor)
        return actor

    async def get_visible_work_order(
        self,
        work_order_id: UUID,
        actor: User,
    ) -> WorkOrder:
        work_order = await self.work_order_repository.get_by_id_for_update(work_order_id)
        if work_order is None or work_order.assignee_user_id != actor.id:
            raise WorkOrderApiError(
                404,
                "WORK_ORDER_NOT_FOUND",
                "Рабочая задача не найдена.",
            )
        return work_order

    def require_active_editor(
        self,
        actor: User,
    ) -> None:
        if actor.role is not UserRole.EDITOR or not actor.is_active:
            raise WorkOrderApiError(
                403,
                "ROLE_NOT_ALLOWED",
                "Роль пользователя не допускает операцию.",
            )

    @staticmethod
    def is_open_edit_version_unique_violation(error: IntegrityError) -> bool:
        original = getattr(
            error,
            "orig",
            None,
        )
        sqlstate = getattr(
            original,
            "sqlstate",
            None,
        ) or getattr(
            original,
            "pgcode",
            None,
        )
        diag = getattr(
            original,
            "diag",
            None,
        )
        constraint_name = getattr(
            diag,
            "constraint_name",
            None,
        ) or getattr(
            original,
            "constraint_name",
            None,
        )
        return sqlstate == POSTGRES_UNIQUE_VIOLATION and (
            constraint_name == OPEN_EDIT_VERSION_UNIQUE_CONSTRAINT
            or OPEN_EDIT_VERSION_UNIQUE_CONSTRAINT in str(error)
        )

    def raise_context_invalid(self) -> None:
        raise WorkOrderApiError(
            422,
            "WORK_ORDER_CONTEXT_INVALID",
            "Контекст рабочей задачи поврежден или неполон.",
        )
