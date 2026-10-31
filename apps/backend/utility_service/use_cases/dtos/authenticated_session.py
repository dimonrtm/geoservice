from dataclasses import dataclass
from uuid import UUID

from utility_service.use_cases.dtos.auth_user import AuthUserDTO


@dataclass(frozen=True)
class AuthenticatedSession:
    user: AuthUserDTO
    session_id: UUID
