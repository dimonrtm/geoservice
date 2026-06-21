from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from utility_service.use_cases.schemas.utility_network.association_out import UtilityAssociationOut
from utility_service.use_cases.schemas.utility_network.feature_collection_out import (
    UtilityFeatureCollectionOut,
)


class UtilityFeederOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    code: str
    name: str
    is_active: bool = Field(serialization_alias="isActive")
    network: UtilityFeatureCollectionOut
    associations: list[UtilityAssociationOut]
