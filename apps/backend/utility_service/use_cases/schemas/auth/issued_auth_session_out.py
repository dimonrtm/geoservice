from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IssuedAuthSessionOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str
    expires_at: datetime
