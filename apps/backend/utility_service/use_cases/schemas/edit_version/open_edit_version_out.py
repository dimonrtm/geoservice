from pydantic import BaseModel, ConfigDict, Field

from utility_service.use_cases.schemas.edit_version.edit_version_out import EditVersionOut


class OpenEditVersionOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    created: bool
    edit_version: EditVersionOut = Field(serialization_alias="editVersion")
