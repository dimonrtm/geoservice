# -*- coding: utf-8 -*-
"""
Created on Tue Dec 30 20:55:34 2025

@author: dimon
"""

from pydantic import BaseModel, Field
from typing import Any
from geojson_polygon import GeoJSONPolygon


class CreateFeaturePolygonRequest(BaseModel):
    geometry: GeoJSONPolygon
    properties: dict[str, Any] = Field(default_factory=dict)
