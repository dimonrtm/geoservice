# -*- coding: utf-8 -*-
"""
Created on Tue Jan 13 19:47:34 2026

@author: dimon
"""

from pydantic import BaseModel, ConfigDict, field_validator


class DeleteFeatureRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: int

    @field_validator("version")
    @classmethod
    def validate_version(cls, version: int) -> int:
        if version < 1:
            raise ValueError("Версия должна быть >= 1")
        return version
