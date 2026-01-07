# -*- coding: utf-8 -*-
"""
Created on Tue Jan  6 19:18:09 2026

@author: dimon
"""

from schemas.layer_out import LayerOut
from sqlalchemy.ext.asyncio import AsyncSession
from models.layer import Layer


class LayerService:
    def __init__(self, session: AsyncSession):
        self.session = session

    def to_layer_out(self, layer: Layer) -> LayerOut:
        return LayerOut(
            id=layer.id,
            name=layer.name,
            title=layer.title,
            geometryType=layer.geometry_type,
            srid=layer.srid,
        )
