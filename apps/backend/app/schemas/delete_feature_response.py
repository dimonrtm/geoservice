# -*- coding: utf-8 -*-
"""
Created on Tue Jan 13 22:02:10 2026

@author: dimon
"""

from pydantic import BaseModel, ConfigDict
from typing import Literal
from uuid import UUID


class DeleteFeatureResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["deleted"] = "deleted"
    featureId: UUID
