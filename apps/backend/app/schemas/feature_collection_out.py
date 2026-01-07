# -*- coding: utf-8 -*-
"""
Created on Tue Jan  6 19:38:19 2026

@author: dimon
"""

from pydantic import BaseModel, ConfigDict
from typing import Literal
from .feature_out import FeatureOut


class FeatureCollectionOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[FeatureOut]
