from typing import Literal

from pydantic import BaseModel, ConfigDict

from schemas.auth_user_out import AuthUserOut


class AuthSuccessOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: Literal["bearer"]
    user: AuthUserOut
