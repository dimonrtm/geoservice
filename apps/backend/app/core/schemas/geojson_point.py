# -*- coding: utf-8 -*-
"""
Created on Tue Dec 30 18:23:26 2025

@author: dimon
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Annotated

Longitude = Annotated[float, Field(ge=-180, le=180)]
Lattitude = Annotated[float, Field(ge=-90, le=90)]


class GeoJSONPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["POINT"]
    coordinates: tuple[Longitude, Lattitude]
