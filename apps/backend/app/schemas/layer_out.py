# -*- coding: utf-8 -*-
"""
Created on Tue Jan  6 19:09:42 2026

@author: dimon
"""

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class LayerOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    name: str
    title: str
    geometryType: str
    srid: int
