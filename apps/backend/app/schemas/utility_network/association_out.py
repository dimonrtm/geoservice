from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from models.utility_network import AssociationType


class UtilityAssociationOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    from_feature_id: UUID = Field(serialization_alias="fromFeatureId")
    to_feature_id: UUID = Field(serialization_alias="toFeatureId")
    association_type: AssociationType = Field(serialization_alias="associationType")
    version: int
