from pydantic import BaseModel, ConfigDict

from utility_service.use_cases.schemas.auth.auth_user_out import AuthUserOut


class AuthMeOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user: AuthUserOut
