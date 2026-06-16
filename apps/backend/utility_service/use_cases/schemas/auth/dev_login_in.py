# -*- coding: utf-8 -*-
"""
Created on Thu Jan  8 23:01:22 2026

@author: dimon
"""

from pydantic import BaseModel, ConfigDict
from utility_service.infrastructure.postgresql.models.user import UserRole


class DevLoginIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str
    role: UserRole = UserRole.EDITOR
