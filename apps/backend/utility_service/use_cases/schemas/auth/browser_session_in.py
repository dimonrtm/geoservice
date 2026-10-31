from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BrowserSessionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: UUID
