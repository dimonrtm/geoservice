from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BrowserSessionStatusOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    state: Literal["active", "ended"]


class BrowserSessionLogoutOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: Literal[True] = True
    session_id: UUID
