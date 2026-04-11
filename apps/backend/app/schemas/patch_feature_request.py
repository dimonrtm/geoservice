from pydantic import BaseModel, ConfigDict, model_validator, field_validator

from .geojson import FeatureGeometry, FeatureProperties


class PatchFeatureRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: int
    geometry: FeatureGeometry | None
    properties: FeatureProperties | None

    @model_validator(mode="after")
    def ensure_has_changes(self):
        if self.geometry is None and self.properties is None:
            raise ValueError("Должны быть предоставлены или геометрия или properties")
        return self

    @field_validator("version")
    @classmethod
    def validate_version(cls, version: int) -> int:
        if version < 1:
            raise ValueError("Версия должна быть >= 1")
        return version
