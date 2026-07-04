from typing import Any

from pydantic import ConfigDict

from utility_service.use_cases.schemas.auth.issued_auth_session_out import (
    IssuedAuthSessionOut,
)


class RefreshedAuthSessionOut(IssuedAuthSessionOut):
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    user: Any
