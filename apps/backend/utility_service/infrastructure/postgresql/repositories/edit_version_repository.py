from datetime import datetime, timezone
from typing import Any, Sequence
from dataclasses import replace
from pathlib import Path
from uuid import UUID

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.domain_services.edit_geometry.policy import GeometryPolicy
from utility_service.domain_services.edit_geometry.canonicalization import prepare_geometry
from utility_service.domain_services.edit_geometry.types import GeometryValue, GeometryRuleError
from utility_service.domain_services.edit_geometry.structure import validate_transition
from utility_service.infrastructure.postgresql.geometry_codec import (
    decode_geometry,
    encode_geometry,
)
from utility_service.infrastructure.postgresql.repositories.edit_geometry_validation import (
    check_baseline,
    check_context,
    inspect_spatial,
    reject_context,
)
from utility_service.infrastructure.postgresql.models.work_order import (
    EditVersion,
    EditVersionAssociation,
    EditVersionFeature,
    EditVersionStatus,
    EditVersionChangeEvent,
)
from utility_service.infrastructure.postgresql.repositories import edit_version_commands
from utility_service.infrastructure.postgresql.repository_rows.edit_version_command import (
    EditVersionCommandRow,
)
from utility_service.infrastructure.postgresql.repositories.edit_geometry_scope import (
    EditGeometryScope,
)
from utility_service.infrastructure.postgresql.repository_rows.edit_geometry import (
    EditGeometryContext,
    EditGeometryDefaultState,
    EditGeometryFeature,
    LockedEditVersion,
    PreparedGeometryHandle,
    RepositoryRejection,
    RepositoryProtocolError,
    ValidatedGeometryChange,
    GeometryWriteResult,
)


SQL_DIRECTORY = Path(__file__).resolve().parents[1] / "sql"
CONTEXT_SQL = text((SQL_DIRECTORY / "edit_geometry_context.sql").read_text(encoding="utf-8"))


class EditVersionRepository:
    """Persistence рабочей версии; transaction принадлежит вызывающему сервису."""

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session
        self.scope = EditGeometryScope.for_session(session)

    async def get_command(
        self,
        root: LockedEditVersion,
        *,
        command_id: UUID,
    ) -> EditVersionCommandRow | None:
        self.scope.require(root)
        with self.session.no_autoflush:
            return await edit_version_commands.read_command(
                self.session,
                command_id,
            )

    async def command_has_history(
        self,
        root: LockedEditVersion,
        *,
        command_id: UUID,
    ) -> bool:
        self.scope.require(root)
        with self.session.no_autoflush:
            return (
                await self.session.scalar(
                    select(EditVersionChangeEvent.command_id).where(
                        EditVersionChangeEvent.command_id == command_id
                    )
                )
            ) is not None

    async def reserve_command(
        self,
        root: LockedEditVersion,
        *,
        command_id: UUID,
        feature_id: UUID,
        actor_id: UUID,
        fingerprint: str,
    ) -> bool:
        self.scope.require(root)
        with self.session.no_autoflush:
            return await edit_version_commands.insert_command(
                self.session,
                version_id=root.id,
                command_id=command_id,
                feature_id=feature_id,
                actor_id=actor_id,
                fingerprint=fingerprint,
            )

    async def complete_command(
        self,
        root: LockedEditVersion,
        *,
        command_id: UUID,
        payload: dict[str, Any],
    ) -> None:
        self.scope.require(root)
        with self.session.no_autoflush:
            completed = await edit_version_commands.finish_command(
                self.session,
                version_id=root.id,
                command_id=command_id,
                payload=payload,
            )
        if not completed:
            raise RepositoryProtocolError("Команда не принадлежит версии или уже завершена.")

    async def increment_revision(
        self,
        root: LockedEditVersion,
    ) -> int:
        self.scope.require(root)
        with self.session.no_autoflush:
            revision = await self.session.scalar(
                update(EditVersion)
                .where(
                    EditVersion.id == root.id,
                    EditVersion.draft_revision == root.draft_revision,
                )
                .values(draft_revision=EditVersion.draft_revision + 1)
                .returning(EditVersion.draft_revision)
                .execution_options(synchronize_session=False)
            )
        if revision is None:
            raise RepositoryProtocolError("Ревизия версии изменилась после получения блокировки.")
        return revision

    async def reject_command(
        self,
        root: LockedEditVersion,
        *,
        command_id: UUID,
        status_code: int,
        code: str,
        message: str,
        retry_on_access_change: bool = False,
    ) -> None:
        self.scope.require(root)
        with self.session.no_autoflush:
            completed = await edit_version_commands.reject_running_command(
                self.session,
                version_id=root.id,
                command_id=command_id,
                status_code=status_code,
                code=code,
                message=message,
                retry_on_access_change=retry_on_access_change,
            )
        if not completed:
            raise RepositoryProtocolError("Команда не принадлежит версии или уже завершена.")

    async def append_change_event(
        self,
        root: LockedEditVersion,
        *,
        command_id: UUID,
        feature_id: UUID,
        actor_id: UUID,
        change: GeometryWriteResult,
        draft_revision_after: int,
    ) -> None:
        self.scope.require(root)
        if not change.changed or draft_revision_after != root.draft_revision + 1:
            raise RepositoryProtocolError(
                "Событие требует фактического изменения и следующей ревизии."
            )
        with self.session.no_autoflush:
            await self.session.execute(
                text(
                    """
                    INSERT INTO work_order.edit_version_change_events (
                        command_id,
                        edit_version_id,
                        work_order_id,
                        default_state_id,
                        feature_id,
                        actor_user_id,
                        event_type,
                        before_geometry,
                        after_geometry,
                        base_network_revision,
                        draft_revision_before,
                        draft_revision_after
                    )
                    VALUES (
                        :command_id,
                        :edit_version_id,
                        :work_order_id,
                        :default_state_id,
                        :feature_id,
                        :actor_id,
                        :event_type,
                        ST_GeomFromEWKB(:before),
                        ST_GeomFromEWKB(:after),
                        :base_revision,
                        :revision_before,
                        :revision_after
                    )
                    """
                ),
                {
                    "command_id": command_id,
                    "edit_version_id": root.id,
                    "work_order_id": root.work_order_id,
                    "default_state_id": root.default_state_id,
                    "feature_id": feature_id,
                    "actor_id": actor_id,
                    "event_type": (
                        "change_set_persisted"
                        if change.operation == "updated"
                        else "change_set_cleared"
                    ),
                    "before": change.before_ewkb,
                    "after": change.after_ewkb,
                    "base_revision": root.base_network_revision,
                    "revision_before": root.draft_revision,
                    "revision_after": draft_revision_after,
                },
            )

    async def resume_access_command(
        self,
        root: LockedEditVersion,
        *,
        command_id: UUID,
    ) -> None:
        self.scope.require(root)
        with self.session.no_autoflush:
            resumed = await edit_version_commands.resume_rejected_access_command(
                self.session,
                version_id=root.id,
                command_id=command_id,
            )
        if not resumed:
            raise RepositoryProtocolError("Команда не допускает повтор после изменения доступа.")

    async def get_open_edit_version(
        self,
        work_order_id: UUID,
    ) -> EditVersion | None:
        result = await self.session.execute(
            select(EditVersion).where(
                EditVersion.work_order_id == work_order_id,
                EditVersion.status == EditVersionStatus.OPEN,
            )
        )
        return result.scalars().one_or_none()

    async def create_open_edit_version(
        self,
        *,
        work_order_id: UUID,
        default_state_id: UUID,
        base_network_revision: int,
        default_features: Sequence[Any],
        default_associations: Sequence[Any],
        owner_user_id: UUID,
        geometry_policy: GeometryPolicy,
    ) -> EditVersion:
        edit_version = EditVersion(
            geometry_xy_resolution=geometry_policy.xy_resolution,
            geometry_rounding_mode=geometry_policy.rounding_mode,
            geometry_policy_version=geometry_policy.version,
            work_order_id=work_order_id,
            default_state_id=default_state_id,
            owner_user_id=owner_user_id,
            base_network_revision=base_network_revision,
            status=EditVersionStatus.OPEN,
        )
        self.session.add(edit_version)
        await self.session.flush()

        self.session.add_all(
            [
                EditVersionFeature(
                    edit_version_id=edit_version.id,
                    feature_id=feature.feature_id,
                    asset_code=feature.asset_code,
                    feature_type=feature.feature_type,
                    geometry=feature.geometry,
                    properties=dict(feature.properties),
                    network_version=feature.network_version,
                )
                for feature in default_features
            ]
        )
        # Associations have composite FKs to edit_version_features; insert parents first.
        await self.session.flush()

        self.session.add_all(
            [
                EditVersionAssociation(
                    edit_version_id=edit_version.id,
                    association_id=association.association_id,
                    association_type=association.association_type,
                    from_feature_id=association.from_feature_id,
                    to_feature_id=association.to_feature_id,
                    properties=dict(association.properties),
                    network_version=association.network_version,
                )
                for association in default_associations
            ]
        )
        await self.session.flush()
        return edit_version

    async def touch_edit_version(
        self,
        edit_version: EditVersion,
    ) -> None:
        edit_version.last_opened_at = datetime.now(timezone.utc)
        self.session.add(edit_version)
        await self.session.flush()

    async def lock_version(
        self,
        *,
        work_order_id: UUID,
        edit_version_id: UUID,
    ) -> LockedEditVersion | None:
        self.scope.require_transaction()
        # Column projection avoids stale ORM identity-map state after waiting.
        with self.session.no_autoflush:
            row = (
                (
                    await self.session.execute(
                        select(*EditVersion.__table__.columns)
                        .where(
                            EditVersion.id == edit_version_id,
                            EditVersion.work_order_id == work_order_id,
                        )
                        .with_for_update(of=EditVersion)
                    )
                )
                .mappings()
                .one_or_none()
            )
        if row is None:
            return None
        root = LockedEditVersion(
            id=row["id"],
            work_order_id=row["work_order_id"],
            default_state_id=row["default_state_id"],
            base_network_revision=row["base_network_revision"],
            draft_revision=row["draft_revision"],
            status=row["status"],
            policy=GeometryPolicy(
                row["geometry_xy_resolution"],
                row["geometry_rounding_mode"],
                row["geometry_policy_version"],
            ),
        )
        return self.scope.issue(
            root,
            root.id,
            root=True,
        )

    async def read_context(
        self,
        locked_version: LockedEditVersion,
        *,
        feature_id: UUID,
    ) -> EditGeometryContext | RepositoryRejection:
        self.scope.require(locked_version)
        with self.session.no_autoflush:
            row = (
                (
                    await self.session.execute(
                        CONTEXT_SQL,
                        {
                            "edit_version_id": locked_version.id,
                            "work_order_id": locked_version.work_order_id,
                            "feature_id": feature_id,
                        },
                    )
                )
                .mappings()
                .one_or_none()
            )
        if row is None or row["feature_id"] is None:
            return RepositoryRejection(
                "EDIT_VERSION_NOT_FOUND",
                "Рабочая версия или объект отсутствует.",
            )
        root = replace(
            locked_version,
            draft_revision=row["draft_revision"],
        )
        self.scope.issue(
            root,
            root.id,
            root=True,
        )
        baseline = None
        if row["baseline_feature_id"] is not None:
            baseline = EditGeometryFeature(
                row["baseline_feature_id"],
                row["baseline_feature_type"],
                None,
                row["baseline_network_version"],
                bytes(row["baseline_ewkb"]),
            )
        default_state = None
        if row["baseline_state_id"] is not None:
            default_state = EditGeometryDefaultState(
                row["baseline_state_id"],
                row["baseline_work_order_id"],
                row["baseline_revision"],
                row["baseline_status"],
            )
        context = EditGeometryContext(
            root=root,
            work_order_status=row["work_order_status"],
            assignee_user_id=row["assignee_user_id"],
            current=EditGeometryFeature(
                row["feature_id"],
                row["feature_type"],
                row["operation"],
                row["network_version"],
                bytes(row["current_ewkb"]),
            ),
            baseline=baseline,
            default_state=default_state,
            aoi_ewkb=bytes(row["aoi_ewkb"]) if row["aoi_ewkb"] is not None else None,
            other_changed_feature_ids=tuple(row["other_changed_feature_ids"]),
        )
        return self.scope.issue(
            context,
            root.id,
        )

    def prepare_candidate(
        self,
        context: EditGeometryContext,
        request_geometry: GeometryValue,
    ) -> PreparedGeometryHandle | RepositoryRejection:
        self.scope.require(context)
        rejection = check_baseline(context)
        if rejection is not None:
            return rejection
        prepared = prepare_geometry(
            request_geometry,
            decode_geometry(context.baseline.geometry_ewkb),
            context.root.policy,
        )
        return self.scope.issue(
            PreparedGeometryHandle(
                context,
                prepared,
            ),
            context.root.id,
        )

    async def validate_candidate(
        self,
        context: EditGeometryContext,
        prepared_geometry: PreparedGeometryHandle,
    ) -> ValidatedGeometryChange | RepositoryRejection:
        self.scope.require(context)
        self.scope.require(prepared_geometry)
        if prepared_geometry.context is not context:
            raise RepositoryProtocolError(
                "Предлагаемая геометрия подготовлена для другого контекста."
            )
        rejection = check_context(context)
        if rejection is not None:
            return rejection
        for feature in (
            context.baseline,
            context.current,
        ):
            verdict = await inspect_spatial(
                self.session,
                geometry_ewkb=feature.geometry_ewkb,
                aoi_ewkb=context.aoi_ewkb,
            )
            if not verdict.geometry_valid or not verdict.aoi_valid or not verdict.aoi_covered:
                return reject_context(
                    "Исходная геометрия или область работ нарушает пространственные ограничения."
                )
        if context.other_changed_feature_ids:
            return RepositoryRejection(
                "MULTIPLE_FEATURE_CHANGE_NOT_ALLOWED",
                "В версии уже изменён другой объект.",
            )
        baseline = decode_geometry(context.baseline.geometry_ewkb)
        current = decode_geometry(context.current.geometry_ewkb)
        try:
            transition = validate_transition(
                baseline,
                current,
                prepared_geometry.prepared,
            )
        except GeometryRuleError as error:
            return RepositoryRejection(
                error.code,
                "Предлагаемая геометрия нарушает правила изменения.",
            )
        candidate = prepared_geometry.prepared.geometry
        if transition.is_noop:
            after = context.current.geometry_ewkb
        elif candidate == baseline:
            after = context.baseline.geometry_ewkb
        else:
            after = encode_geometry(candidate)
        verdict = await inspect_spatial(
            self.session,
            geometry_ewkb=after,
            aoi_ewkb=context.aoi_ewkb,
        )
        if not verdict.geometry_valid:
            return RepositoryRejection(
                "GEOMETRY_INVALID",
                "Предлагаемая геометрия недопустима.",
            )
        if not verdict.aoi_covered:
            return RepositoryRejection(
                "GEOMETRY_OUTSIDE_AOI",
                "Предлагаемая геометрия выходит за пределы области работ.",
            )
        change = ValidatedGeometryChange(
            context,
            context.current.geometry_ewkb,
            after,
            transition.operation,
            transition.is_noop,
            transition.vertex_index,
        )
        return self.scope.issue(
            change,
            context.root.id,
        )

    async def write_current(
        self,
        validated_change: ValidatedGeometryChange,
    ) -> GeometryWriteResult:
        self.scope.require(validated_change)
        context = validated_change.context
        self.scope.require(context)
        if not validated_change.is_noop:
            with self.session.no_autoflush:
                result = await self.session.execute(
                    text(
                        """
                        UPDATE work_order.edit_version_features
                        SET
                            geometry = ST_GeomFromEWKB(:geometry),
                            operation = :operation
                        WHERE edit_version_id = :version
                            AND feature_id = :feature
                        RETURNING feature_id
                        """
                    ),
                    {
                        "geometry": validated_change.after_ewkb,
                        "operation": validated_change.operation,
                        "version": context.root.id,
                        "feature": context.current.feature_id,
                    },
                )
            if result.scalar_one_or_none() != context.current.feature_id:
                raise RepositoryProtocolError("Редактируемый объект исчез до обновления.")
        self.scope.consume(context.root.id)
        return GeometryWriteResult(
            not validated_change.is_noop,
            validated_change.operation,
            validated_change.before_ewkb,
            validated_change.after_ewkb,
        )
