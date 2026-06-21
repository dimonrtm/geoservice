from pydantic import BaseModel, ConfigDict, Field

from utility_service.use_cases.schemas.workspace.work_order_workspace_out import (
    WorkspaceWorkOrderOut,
)


class WorkspaceOut(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    work_order: WorkspaceWorkOrderOut = Field(serialization_alias="workOrder")
