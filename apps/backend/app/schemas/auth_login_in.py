from pydantic import BaseModel, ConfigDict


class AuthLoginIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: str
