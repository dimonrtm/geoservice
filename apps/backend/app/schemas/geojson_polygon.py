# -*- coding: utf-8 -*-
"""
Created on Tue Dec 30 20:26:58 2025

@author: dimon
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Literal, Annotated

Longitude = Annotated[float, Field(ge=-180, le=180)]
Lattitude = Annotated[float, Field(ge=-90, le=90)]
Point = tuple[Longitude, Lattitude]
LinearRing = list[Point]
PolygonCoordinates = list[LinearRing]


class GeoJSONPolygon(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["Polygon"]
    coordinates: PolygonCoordinates

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(cls, coords: PolygonCoordinates) -> PolygonCoordinates:
        if not coords:
            raise ValueError("coordinates должен иметь хотя бы одно кольцо (внешнее)")

        outer_ring = coords[0]

        if len(outer_ring) < 4:
            raise ValueError("Внешнее кольцо должно содержать минимум 4 точки")
        return coords
