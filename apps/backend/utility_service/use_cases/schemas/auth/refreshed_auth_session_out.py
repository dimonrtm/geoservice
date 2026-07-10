from pydantic import ConfigDict

from utility_service.use_cases.dtos import AuthUserDTO
from utility_service.use_cases.schemas.auth.issued_auth_session_out import (
    IssuedAuthSessionOut,
)


class RefreshedAuthSessionOut(IssuedAuthSessionOut):
    model_config = ConfigDict(extra="forbid")

    user: AuthUserDTO
