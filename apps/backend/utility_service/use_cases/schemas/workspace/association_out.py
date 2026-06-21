from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceAssociationOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    from_feature_id: UUID = Field(serialization_alias="fromFeatureId")
    to_feature_id: UUID = Field(serialization_alias="toFeatureId")
    association_type: str = Field(serialization_alias="associationType")
    version: int
