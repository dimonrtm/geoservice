# -*- coding: utf-8 -*-
"""
Created on Tue Jan  6 20:45:11 2026

@author: dimon
"""

from pydantic import BaseModel, ConfigDict
from .feature_out import FeatureOut


class PatchFeatureSuccesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    feature: FeatureOut
