# -*- coding: utf-8 -*-
"""
Created on Tue Jan  6 19:28:48 2026

@author: dimon
"""

from uuid import UUID
from pydantic import BaseModel, ConfigDict
from typing import Literal, Any


class FeatureOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    type: Literal["Feature"]
    version: int
    geometry: dict[str, Any]
    properties: dict[str, Any]
