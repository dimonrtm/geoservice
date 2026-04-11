from pydantic import BaseModel, ConfigDict

from schemas.auth_user_out import AuthUserOut


class AuthMeOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user: AuthUserOut
