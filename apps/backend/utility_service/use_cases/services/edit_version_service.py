from __future__ import annotations

from copy import deepcopy
from uuid import UUID

from utility_service.infrastructure.postgresql.repositories.edit_version_repository import (
    EditVersionRepository,
)

from sqlalchemy.ext.asyncio import AsyncSession
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

from utility_service.infrastructure.postgresql.models.user import UserRole
from utility_service.infrastructure.postgresql.models.work_order import (
    EditVersionCommandState,
)
from utility_service.infrastructure.postgresql.repositories.default_state_repository import (
    DefaultStateRepository,
)
from utility_service.infrastructure.postgresql.repositories.user_repository import UserRepository
from utility_service.use_cases.domain.exceptions.work_order_api_error import WorkOrderApiError


class EditVersionService:
    def __init__(
        self,
        session: AsyncSession,
        user_repository: UserRepository,
        default_state_repository: DefaultStateRepository,
        *,
        edit_version_repository: EditVersionRepository,
    ):
        self.session = session
        self.user_repository = user_repository
        self.default_state_repository = default_state_repository
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
        baseline = await self.default_state_repository.read_geometry_baseline(
            default_state_id=root.default_state_id,
            feature_id=feature_id,
        )
        context = await repository.read_context(
            root,
            feature_id=feature_id,
            baseline=baseline,
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
