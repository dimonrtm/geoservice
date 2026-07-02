from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WebSocketTicketOut(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    ticket: str
    expires_at: datetime = Field(serialization_alias="expiresAt")
