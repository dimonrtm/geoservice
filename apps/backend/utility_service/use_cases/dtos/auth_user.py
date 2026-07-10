from dataclasses import dataclass
from typing import Literal, TypeAlias
from uuid import UUID


AuthRole: TypeAlias = Literal["editor", "reviewer"]


@dataclass(frozen=True, slots=True)
class AuthUserDTO:
    id: UUID
    email: str
    role: AuthRole
    is_active: bool
