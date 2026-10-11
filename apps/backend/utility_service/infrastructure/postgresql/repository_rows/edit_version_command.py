from dataclasses import dataclass
from typing import Any
from uuid import UUID

from utility_service.infrastructure.postgresql.models.work_order import EditVersionCommandState


@dataclass(frozen=True)
class EditVersionCommandRow:
    command_id: UUID
    edit_version_id: UUID
    feature_id: UUID
    actor_user_id: UUID
    request_fingerprint: str
    state: EditVersionCommandState
    retry_on_access_change: bool
    response_status: int | None
    response_payload: dict[str, Any] | None
    rejection_code: str | None
    rejection_message: str | None
