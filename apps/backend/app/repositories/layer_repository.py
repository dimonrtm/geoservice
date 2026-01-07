# -*- coding: utf-8 -*-
"""
Created on Wed Jan  7 12:12:19 2026

@author: dimon
"""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Any
from models.layer import Layer
from model.feature_point import FeaturePoint
from model.feature_polygon import FeaturePolygon
from model.feature_line import FeatureLine
from model.feature_multipoint import FeatureMultiPoint
from model.feature_multiline import FeatureMultiLine
from model.feature_multipolygon import FeatureMultiPolygon
from .exceptions.layer_not_found_exception import LayerNotFoundException
from .exceptions.layer_storage_mapping_exception import LayerStorageMappingException


class LayerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.table_mapping = {
            "feature_points": FeaturePoint,
            "feature_polygons": FeaturePolygon,
            "feature_lines": FeatureLine,
            "feature_multipoints": FeatureMultiPoint,
            "feature_multipolygons": FeatureMultiPolygon,
            "feature_multilines": FeatureMultiLine,
        }

    async def get_layer_storage(self, layer_id: UUID) -> dict[str, Any]:
        stmt = select(
            Layer.storage_table.label("storage_table"),
            Layer.srid.label("srid"),
            Layer.geometry_type.label("geometry_type"),
        ).where(Layer.id == layer_id)
        res = await self.session.execute(stmt)
        row = res.one_or_none()
        if row is None:
            raise LayerNotFoundException(f"Слой с идентификатором {layer_id} не найден")
        return row

    async def list_features_bbox(self, layer_id: UUID, bbox, limit_value: int):
        layer_storage = await self.get_layer_storage(layer_id)
        storage_table = layer_storage["storage_table"]
        model_type = self.table_mapping.get(storage_table)
        if model_type is None:
            raise LayerStorageMappingException(
                f"Неизвестная таблица хранения '{storage_table}' для слоя {layer_id}"
            )
        stmt = (
            select(
                model_type.id.label("id"),
                model_type.version.label("version"),
                model_type.properties.label("properties"),
                func.ST_AsGeoJSON(model_type.geom).label("geometry_json"),
            )
            .where(
                func.ST_Intersects(
                    model_type.geom,
                    func.ST_MakeEnvelope(
                        bbox.min_lon, bbox.min_lat, bbox.max_lon, bbox.max_lat, 4326
                    ),
                )
            )
            .limit(limit_value)
        )
        res = await self.session.execute(stmt)
        return res.all()
