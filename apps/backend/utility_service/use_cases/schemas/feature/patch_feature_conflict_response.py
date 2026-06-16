# -*- coding: utf-8 -*-
"""
Created on Tue Jan  6 20:28:01 2026

@author: dimon
"""

from pydantic import BaseModel, ConfigDict
from typing import Literal


class PatchFeatureConflictResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["VERSION_MISMATCH"] = "VERSION_MISMATCH"
    featureId: str
    requestVersion: int
    currentVersion: int
    message: str
