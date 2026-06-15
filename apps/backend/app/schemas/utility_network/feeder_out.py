from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from schemas.utility_network.association_out import UtilityAssociationOut
from schemas.utility_network.feature_collection_out import UtilityFeatureCollectionOut


class UtilityFeederOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    code: str
    name: str
    is_active: bool = Field(serialization_alias="isActive")
    aois: UtilityFeatureCollectionOut
    network: UtilityFeatureCollectionOut
    associations: list[UtilityAssociationOut]
