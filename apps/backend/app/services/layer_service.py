# -*- coding: utf-8 -*-
"""
Created on Tue Jan  6 19:18:09 2026

@author: dimon
"""

from schemas.layer_out import LayerOut
from schemas.layer_list_out import LayerListOut
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.layer_repository import LayerRepository
from models.layer import Layer


class LayerService:
    def __init__(self, session: AsyncSession, layer_repository: LayerRepository):
        self.session = session
        self.layer_repository = layer_repository

    def to_layer_out(self, layer: Layer) -> LayerOut:
        return LayerOut(
            id=layer.id,
            name=layer.name,
            title=layer.title,
            geometryType=layer.geometry_type,
            srid=layer.srid,
        )

    async def get_layers(self) -> LayerListOut:
        layers = await self.layer_repository.get_layers()
        return LayerListOut(layers=[self.to_layer_out(layer) for layer in layers])
