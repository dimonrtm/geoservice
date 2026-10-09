from dataclasses import dataclass
from uuid import UUID

from utility_service.domain_services.edit_geometry.types import GeometryValue


@dataclass(frozen=True)
class GeometrySaveRequest:
    command_id: UUID
    draft_version_token: str
    geometry: GeometryValue
