# -*- coding: utf-8 -*-
"""
Created on Tue Jan  6 19:47:19 2026

@author: dimon
"""

from pydantic import BaseModel, ConfigDict, model_validator
from typing import Any


class PatchFeatureRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: int
    geometry: dict[str, Any] | None
    properties: dict[str, Any] | None

    @model_validator(mode="after")
    def ensure_has_changes(self):
        if self.geometry is None and self.properties is None:
            raise ValueError("Должны быть предоставлены или геометрия или properties")
        return self
