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
from utility_service.domain_services.edit_geometry.fingerprint import command_fingerprint
from utility_service.domain_services.edit_geometry.types import (
    FingerprintContext,
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
    build_geometry_save_payload,
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
        try:
            async with self.session.begin():
                result = await self._save_geometry_locked(
                    work_order_id=work_order_id,
                    edit_version_id=edit_version_id,
                    feature_id=feature_id,
                    actor_id=actor_id,
                    request=request,
                )
        except GeometryRuleError as error:
            self._reject_save(
                error.code,
                str(error),
            )
        except InvalidGeometryContext as error:
            self._reject_save(
                "WORK_ORDER_CONTEXT_INVALID",
                str(error),
            )
        # Deferred constraints and commit must succeed before returning success.
        return result

    async def _save_geometry_locked(
        self,
        *,
        work_order_id: UUID,
        edit_version_id: UUID,
        feature_id: UUID,
        actor_id: UUID,
        request: GeometrySaveRequest,
    ) -> SaveGeometryResult:
        actor = await self.user_repository.get_by_id(actor_id)
        if actor is None:
            self._reject_save(
                "ROLE_NOT_ALLOWED",
                "Роль пользователя не допускает операцию.",
            )
        self.require_active_editor(actor)
        repository = self.edit_version_repository
        root = await repository.lock_version(
            work_order_id=work_order_id,
            edit_version_id=edit_version_id,
        )
        if root is None:
            self._reject_save(
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
            self._reject_save(
                context.code,
                context.reason,
            )
        if context.assignee_user_id != actor.id:
            self._reject_save(
                "EDIT_VERSION_NOT_FOUND",
                "Рабочая версия не найдена.",
            )
        if root.status != "open" or context.work_order_status != "in_progress":
            self._reject_save(
                "SAVE_CONTEXT_CLOSED",
                "Контекст сохранения закрыт.",
            )

        command = await repository.get_command(
            root,
            command_id=request.command_id,
        )
        if command is not None:
            self._check_save_command_target(
                command,
                edit_version_id,
                feature_id,
                actor_id,
            )
        prepared = repository.prepare_candidate(
            context,
            request.geometry,
        )
        if isinstance(
            prepared,
            RepositoryRejection,
        ):
            self._reject_save(
                prepared.code,
                prepared.reason,
            )
        fingerprint = command_fingerprint(
            FingerprintContext(
                work_order_id=work_order_id,
                edit_version_id=edit_version_id,
                feature_id=feature_id,
                actor_user_id=actor_id,
                default_state_id=root.default_state_id,
                base_network_revision=root.base_network_revision,
                draft_version_token=request.draft_version_token,
            ),
            decode_geometry(context.baseline.geometry_ewkb),
            root.policy,
            prepared.prepared,
        )
        if command is not None:
            return self._replay_save(
                command,
                fingerprint,
            )
        if await repository.command_has_history(
            root,
            command_id=request.command_id,
        ):
            self._reject_command_reuse()
        reserved = await repository.reserve_command(
            root,
            command_id=request.command_id,
            feature_id=feature_id,
            actor_id=actor_id,
            fingerprint=fingerprint,
        )
        if not reserved:
            # READ COMMITTED: a new statement sees the winner of the INSERT conflict.
            command = await repository.get_command(
                root,
                command_id=request.command_id,
            )
            if command is None:
                if await repository.command_has_history(
                    root,
                    command_id=request.command_id,
                ):
                    self._reject_command_reuse()
                raise RepositoryProtocolError("Результат конкурирующей команды больше недоступен.")
            self._check_save_command_target(
                command,
                edit_version_id,
                feature_id,
                actor_id,
            )
            return self._replay_save(
                command,
                fingerprint,
            )

        if request.draft_version_token != str(root.draft_revision):
            self._reject_save(
                "DRAFT_VERSION_STALE",
                "Рабочая версия изменилась. Обновите данные.",
            )
        change = await repository.validate_candidate(
            context,
            prepared,
        )
        if isinstance(
            change,
            RepositoryRejection,
        ):
            self._reject_save(
                change.code,
                change.reason,
            )
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
    ) -> SaveGeometryResult:
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
            raise WorkOrderApiError(
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

    @staticmethod
    def _reject_save(
        code: str,
        message: str,
    ) -> None:
        statuses = {
            "ROLE_NOT_ALLOWED": 403,
            "EDIT_VERSION_NOT_FOUND": 404,
            "SAVE_CONTEXT_CLOSED": 409,
            "DRAFT_VERSION_STALE": 409,
            "MULTIPLE_FEATURE_CHANGE_NOT_ALLOWED": 409,
            "FEATURE_NOT_EDITABLE": 422,
            "WORK_ORDER_CONTEXT_INVALID": 422,
            "GEOMETRY_STRUCTURE_CHANGED": 422,
            "GEOMETRY_INVALID": 422,
            "GEOMETRY_OUTSIDE_AOI": 422,
        }
        if code not in statuses:
            raise RepositoryProtocolError("Неизвестный результат проверки сохранения.")
        raise WorkOrderApiError(
            statuses[code],
            code,
            message,
        )

    async def open_for_work_order(
        self,
        work_order_id: UUID,
        actor_id: UUID,
    ) -> OpenEditVersionResult:
        try:
            return await self.open_for_work_order_locked(work_order_id, actor_id)
        except IntegrityError as exc:
            if not self.is_open_edit_version_unique_violation(exc):
                raise
            return await self.recover_existing_open_edit_version(work_order_id, actor_id)

    async def open_for_work_order_locked(
        self,
        work_order_id: UUID,
        actor_id: UUID,
    ) -> OpenEditVersionResult:
        async with self.session.begin():
            actor = await self.get_actor(actor_id)
            work_order = await self.get_visible_work_order(work_order_id, actor)
            return await self.open_visible_work_order(work_order, actor)

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
        return OpenEditVersionResult(created=True, edit_version=created)

    async def recover_existing_open_edit_version(
        self,
        work_order_id: UUID,
        actor_id: UUID,
    ) -> OpenEditVersionResult:
        async with self.session.begin():
            actor = await self.get_actor(actor_id)
            work_order = await self.get_visible_work_order(work_order_id, actor)
            existing = await self.edit_version_repository.get_open_edit_version(work_order.id)
            if existing is None:
                self.raise_context_invalid()
            return await self.reopen_edit_version(existing)

    async def reopen_edit_version(self, edit_version: EditVersion) -> OpenEditVersionResult:
        await self.edit_version_repository.touch_edit_version(edit_version)
        return OpenEditVersionResult(created=False, edit_version=edit_version)

    async def get_actor(self, actor_id: UUID) -> User:
        actor = await self.user_repository.get_by_id(actor_id)
        if actor is None:
            raise WorkOrderApiError(
                404,
                "WORK_ORDER_ACTOR_NOT_FOUND",
                "Пользователь не найден.",
            )
        self.require_active_editor(actor)
        return actor

    async def get_visible_work_order(self, work_order_id: UUID, actor: User) -> WorkOrder:
        work_order = await self.work_order_repository.get_by_id_for_update(work_order_id)
        if work_order is None or work_order.assignee_user_id != actor.id:
            raise WorkOrderApiError(
                404,
                "WORK_ORDER_NOT_FOUND",
                "Рабочая задача не найдена.",
            )
        return work_order

    def require_active_editor(self, actor: User) -> None:
        if actor.role is not UserRole.EDITOR or not actor.is_active:
            raise WorkOrderApiError(
                403,
                "ROLE_NOT_ALLOWED",
                "Роль пользователя не допускает операцию.",
            )

    @staticmethod
    def is_open_edit_version_unique_violation(error: IntegrityError) -> bool:
        original = getattr(error, "orig", None)
        sqlstate = getattr(original, "sqlstate", None) or getattr(original, "pgcode", None)
        diag = getattr(original, "diag", None)
        constraint_name = getattr(diag, "constraint_name", None) or getattr(
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
