from typing import Annotated, Any, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, field_validator

Longitude = Annotated[float, Field(ge=-180, le=180)]
Latitude = Annotated[float, Field(ge=-90, le=90)]
Position2D = tuple[Longitude, Latitude]
LineCoordinates = list[Position2D]
LinearRing = list[Position2D]
PolygonCoordinates = list[LinearRing]
MultiPointCoordinates = list[Position2D]
MultiLineStringCoordinates = list[LineCoordinates]
MultiPolygonCoordinates = list[PolygonCoordinates]
FeatureProperties: TypeAlias = dict[str, Any]


class GeoJSONPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["Point"]
    coordinates: Position2D


class GeoJSONMultiPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["MultiPoint"]
    coordinates: MultiPointCoordinates

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(cls, coords: MultiPointCoordinates) -> MultiPointCoordinates:
        if not coords:
            raise ValueError("MultiPoint должен содержать хотя бы одну точку")
        return coords


class GeoJSONLineString(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["LineString"]
    coordinates: LineCoordinates

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(cls, coords: LineCoordinates) -> LineCoordinates:
        if len(coords) < 2:
            raise ValueError("LineString должен содержать минимум 2 точки")
        return coords


class GeoJSONMultiLineString(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["MultiLineString"]
    coordinates: MultiLineStringCoordinates

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(cls, coords: MultiLineStringCoordinates) -> MultiLineStringCoordinates:
        if not coords:
            raise ValueError("MultiLineString должен содержать хотя бы одну линию")
        for line in coords:
            if len(line) < 2:
                raise ValueError("Каждая линия в MultiLineString должна содержать минимум 2 точки")
        return coords


class GeoJSONPolygon(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["Polygon"]
    coordinates: PolygonCoordinates

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(cls, coords: PolygonCoordinates) -> PolygonCoordinates:
        validate_polygon_coordinates(coords)
        return coords


class GeoJSONMultiPolygon(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["MultiPolygon"]
    coordinates: MultiPolygonCoordinates

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(cls, coords: MultiPolygonCoordinates) -> MultiPolygonCoordinates:
        if not coords:
            raise ValueError("MultiPolygon должен содержать хотя бы один полигон")
        for polygon in coords:
            validate_polygon_coordinates(polygon)
        return coords


FeatureGeometry = Annotated[
    GeoJSONPoint
    | GeoJSONMultiPoint
    | GeoJSONLineString
    | GeoJSONMultiLineString
    | GeoJSONPolygon
    | GeoJSONMultiPolygon,
    Field(discriminator="type"),
]


def dump_feature_geometry(geometry: FeatureGeometry) -> dict[str, Any]:
    return geometry.model_dump(mode="python")


def validate_polygon_coordinates(coords: PolygonCoordinates) -> None:
    if not coords:
        raise ValueError("coordinates должен иметь хотя бы одно кольцо (внешнее)")

    for ring in coords:
        if len(ring) < 4:
            raise ValueError("Каждое кольцо полигона должно содержать минимум 4 точки")
        if ring[0] != ring[-1]:
            raise ValueError("Все кольца полигона должны быть замкнутыми")
