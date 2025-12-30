# -*- coding: utf-8 -*-
"""
Created on Tue Dec 30 18:22:26 2025

@author: dimon
"""

from typing import Any
from .geojson_point import GeoJSONPoint
from pydantic import BaseModel, Field, ConfigDict


class CreateFeaturePointRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    geometry: GeoJSONPoint
    properties: dict[str, Any] = Field(default_factory=dict)
