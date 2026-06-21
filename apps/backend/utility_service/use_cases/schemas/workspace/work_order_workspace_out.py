from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from utility_service.use_cases.schemas.workspace.aoi_out import WorkspaceAoiOut
from utility_service.use_cases.schemas.workspace.edit_version_workspace_out import (
    WorkspaceEditVersionOut,
)


class WorkspaceScopeOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    aoi: WorkspaceAoiOut


class WorkspaceWorkOrderOut(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: UUID
    code: str
    title: str
    description: str | None
    status: str
    scope: WorkspaceScopeOut
    edit_version: WorkspaceEditVersionOut = Field(serialization_alias="editVersion")
