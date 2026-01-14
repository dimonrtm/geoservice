# -*- coding: utf-8 -*-
"""
Created on Wed Jan 14 19:44:19 2026

@author: dimon
"""

from pydantic import BaseModel, ConfigDict
from .layer_out import LayerOut


class LayerListOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    layers: list[LayerOut]
