from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class IssuedAuthSessionOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str
    session_id: UUID
    expires_at: datetime
