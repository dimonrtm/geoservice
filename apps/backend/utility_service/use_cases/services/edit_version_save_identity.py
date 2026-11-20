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
    GeometryValue,
    InvalidGeometryContext,
)
from utility_service.infrastructure.postgresql.repositories.edit_geometry_validation import (
    checked_baseline,
    read_baseline,
)
from utility_service.infrastructure.postgresql.repository_rows.edit_geometry import (
    EditGeometryContext,
    RepositoryProtocolError,
    RepositoryRejection,
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
    result = checked_baseline(context)
    early = None
    if isinstance(result, RepositoryRejection):
        early = SaveGeometryRejection.from_code(result.code, result.reason)
        if result.code == "FEATURE_NOT_EDITABLE":
            # A point or short line can still identify a previously rejected command.
            result = read_baseline(context)
    geometry = result if isinstance(result, GeometryValue) else None
    if geometry is not None:
        try:
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
