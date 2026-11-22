from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class WebSocketUserContext:
    user_id: UUID
    email: str
    role: str
    session_id: UUID
