# -*- coding: utf-8 -*-
"""
Created on Sat Jan 10 20:01:25 2026

@author: dimon
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Any


class CreateFeatureIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    geometry: dict[str, Any]
    properties: dict[str, Any] = Field(default_factory=dict)
