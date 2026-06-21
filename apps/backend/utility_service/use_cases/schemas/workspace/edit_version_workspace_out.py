from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from utility_service.use_cases.schemas.workspace.association_out import (
    WorkspaceAssociationOut,
)
from utility_service.use_cases.schemas.workspace.feature_out import (
    WorkspaceFeatureCollectionOut,
)


class WorkspaceEditVersionOut(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: UUID
    status: str
    base_network_revision: int = Field(serialization_alias="baseNetworkRevision")
    features: WorkspaceFeatureCollectionOut
    associations: list[WorkspaceAssociationOut]
