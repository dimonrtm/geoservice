from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from utility_service.use_cases.schemas.geojson.geojson import FeatureGeometry


class MapAoiOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
    description: str | None
    geometry: dict[str, Any]
    extent: list[float]


class MapFeatureOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    type: Literal["Feature"] = "Feature"
    geometry: FeatureGeometry
    properties: dict[str, Any] = Field(default_factory=dict)


class MapFeatureCollectionOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[MapFeatureOut]


class MapAssociationOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    from_feature_id: UUID = Field(serialization_alias="fromFeatureId")
    to_feature_id: UUID = Field(serialization_alias="toFeatureId")
    association_type: str = Field(serialization_alias="associationType")
    version: int


class MapEditVersionOut(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: UUID
    status: str
    base_network_revision: int = Field(serialization_alias="baseNetworkRevision")
    draft_version_token: str = Field(
        alias="draftVersionToken",
        min_length=1,
    )
    features: MapFeatureCollectionOut
    associations: list[MapAssociationOut]


class MapScopeOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    aoi: MapAoiOut


class MapWorkOrderOut(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: UUID
    code: str
    title: str
    description: str | None
    status: str
    scope: MapScopeOut
    edit_version: MapEditVersionOut = Field(serialization_alias="editVersion")


class EditVersionMapOut(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    work_order: MapWorkOrderOut = Field(serialization_alias="workOrder")
