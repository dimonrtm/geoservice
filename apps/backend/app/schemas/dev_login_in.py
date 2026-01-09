# -*- coding: utf-8 -*-
"""
Created on Thu Jan  8 23:01:22 2026

@author: dimon
"""

from pydantic import BaseModel, ConfigDict, field_validator
from models.user import UserRole


class DevLoginIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str
    role: UserRole = UserRole.VIEWER

    @field_validator("role", mode="before")
    @classmethod
    def coerce_role(cls, v):
        if v is None or v == "":
            return UserRole.VIEWER
        try:
            return UserRole(v)
        except Exception:
            return UserRole.VIEWER
