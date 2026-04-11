from typing import Literal

from pydantic import BaseModel, ConfigDict


class AuthUserOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    email: str
    role: Literal["viewer", "editor"]
