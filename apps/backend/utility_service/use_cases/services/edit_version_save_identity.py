"""Подготовка идентичности не выполняет mutation и не управляет transaction."""

from dataclasses import dataclass
from uuid import UUID

from utility_service.domain_services.edit_geometry.canonicalization import prepare_geometry
from utility_service.domain_services.edit_geometry.contextless_fingerprint import (
    contextless_command_fingerprint,
)
from utility_service.domain_services.edit_geometry.fingerprint import command_fingerprint
from utility_service.domain_services.edit_geometry.types import (
    FingerprintContext,
    InvalidGeometryContext,
)
from utility_service.infrastructure.postgresql.geometry_codec import decode_geometry
from utility_service.infrastructure.postgresql.repositories.edit_geometry_validation import (
    check_baseline,
)
from utility_service.infrastructure.postgresql.repository_rows.edit_geometry import (
    EditGeometryContext,
    RepositoryProtocolError,
)
from utility_service.use_cases.schemas.edit_version.geometry_save_in import GeometrySaveRequest
from utility_service.use_cases.schemas.edit_version.geometry_save_out import SaveGeometryRejection


@dataclass(frozen=True)
class SaveGeometryIdentity:
    fingerprint: str
    preparation_rejection: SaveGeometryRejection | None


def build_save_geometry_identity(
    context: EditGeometryContext,
    *,
    actor_id: UUID,
    request: GeometrySaveRequest,
    stored_fingerprint: str | None = None,
) -> SaveGeometryIdentity:
    root = context.root
    identity = FingerprintContext(
        root.work_order_id,
        root.id,
        context.current.feature_id,
        actor_id,
        root.default_state_id,
        root.base_network_revision,
        request.draft_version_token,
    )
    if stored_fingerprint is not None and not stored_fingerprint.startswith(
        ("geom-v1:sha256:", "geom-contextless-v1:sha256:")
    ):
        raise RepositoryProtocolError("Неизвестный формат идентичности команды.")
    if stored_fingerprint is not None and stored_fingerprint.startswith("geom-contextless-v1:"):
        return SaveGeometryIdentity(
            contextless_command_fingerprint(
                identity,
                root.policy,
                request.geometry,
            ),
            None,
        )
    rejection = check_baseline(context)
    early = (
        SaveGeometryRejection.from_code(
            rejection.code,
            rejection.reason,
        )
        if rejection
        else None
    )
    baseline, state = context.baseline, context.default_state
    geometry = None
    if (
        (early is None or early.code != "WORK_ORDER_CONTEXT_INVALID")
        and baseline is not None
        and state is not None
        and state.id == root.default_state_id
        and state.work_order_id == root.work_order_id
        and state.base_network_revision == root.base_network_revision
        and state.status == "active"
        and baseline.feature_id == context.current.feature_id
        and baseline.feature_type == context.current.feature_type
    ):
        try:
            geometry = decode_geometry(baseline.geometry_ewkb)
            # Fingerprint supports Point/short lines for ineligible targets, as in Day 4.
            prepared = prepare_geometry(
                request.geometry,
                geometry,
                root.policy,
            )
            fingerprint = command_fingerprint(
                identity,
                geometry,
                root.policy,
                prepared,
            )
        except InvalidGeometryContext:
            geometry = None
    if geometry is None:
        if stored_fingerprint is not None:
            raise InvalidGeometryContext("Базовое состояние для сравнения команды недоступно.")
        fingerprint = contextless_command_fingerprint(
            identity,
            root.policy,
            request.geometry,
        )
        early = early or SaveGeometryRejection.from_code(
            "WORK_ORDER_CONTEXT_INVALID",
            "Базовое состояние повреждено или неполно.",
        )
    return SaveGeometryIdentity(
        fingerprint,
        early,
    )
