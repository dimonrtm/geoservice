# -*- coding: utf-8 -*-
"""
Created on Wed Jan  7 12:12:19 2026

@author: dimon
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, insert, update, delete
from models.layer import Layer
from domain.feature_registry import get_layer_feature_model
from uuid import UUID
import uuid
import json


class LayerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_features_bbox(self, layer: Layer, bbox, limit_value: int):
        model_type = get_layer_feature_model(layer)
        envelope = func.ST_MakeEnvelope(
            bbox.min_lon, bbox.min_lat, bbox.max_lon, bbox.max_lat, 4326
        )
        stmt = (
            select(
                model_type.id.label("id"),
                model_type.version.label("version"),
                model_type.properties.label("properties"),
                func.ST_AsGeoJSON(model_type.geom).label("geometry_json"),
            )
            .where(model_type.geom.op("&&")(envelope))
            .where(
                func.ST_Intersects(
                    model_type.geom,
                    envelope,
                )
            )
            .limit(limit_value)
        )
        res = await self.session.execute(stmt)
        return res.all()

    async def get_layer_by_id(self, layer_id: UUID) -> Layer:
        stmt = select(Layer).where(Layer.id == layer_id)
        res = await self.session.execute(stmt)
        return res.scalars().one_or_none()

    async def create_feature(self, layer: Layer, geometry: dict, properties: dict):
        geom_expr = self.get_geom_expr(geometry)
        model_type = get_layer_feature_model(layer)
        stmt = (
            insert(model_type)
            .values(id=uuid.uuid4(), version=1, properties=properties, geom=geom_expr)
            .returning(
                model_type.id.label("id"),
                model_type.version.label("version"),
                model_type.properties.label("properties"),
                func.ST_AsGeoJSON(model_type.geom).label("geometry_json"),
            )
        )
        res = await self.session.execute(stmt)
        return res.one_or_none()

    async def update_feature_if_version_matches(
        self,
        layer: Layer,
        feature_id: UUID,
        geometry: dict | None,
        properties: dict | None,
        expected_version: int,
    ):
        if geometry:
            geom_expr = self.get_geom_expr(geometry)
        model_type = get_layer_feature_model(layer)
        update_stmt = update(model_type).where(
            model_type.id == feature_id, model_type.version == expected_version
        )
        if geometry is None and properties is not None:
            update_stmt = update_stmt.values(
                properties=properties, version=model_type.version + 1, updated_at=func.now()
            )
        elif properties is None and geometry is not None:
            update_stmt = update_stmt.values(
                geom=geom_expr, version=model_type.version + 1, updated_at=func.now()
            )
        else:
            update_stmt = update_stmt.values(
                geom=geom_expr,
                properties=properties,
                version=model_type.version + 1,
                updated_at=func.now(),
            )
        update_stmt = update_stmt.returning(
            model_type.id.label("id"),
            model_type.version.label("version"),
            model_type.properties.label("properties"),
            func.ST_AsGeoJSON(model_type.geom).label("geometry_json"),
        )
        update_stmt = update_stmt
        res = await self.session.execute(update_stmt)
        return (res.one_or_none(), model_type)

    async def delete_feature_if_version_matches(
        self, layer: Layer, feature_id: UUID, expected_version: int
    ) -> tuple[bool, type]:
        model_type = get_layer_feature_model(layer)
        stmt = (
            delete(model_type)
            .where(model_type.id == feature_id, model_type.version == expected_version)
            .returning(model_type.id)
        )
        res = await self.session.execute(stmt)
        deleted_id = res.scalar_one_or_none()
        return (deleted_id is not None, model_type)

    async def get_feature(self, layer: Layer, feature_id: UUID):
        model_type = get_layer_feature_model(layer)
        stmt = select(
            model_type.id.label("id"),
            model_type.version.label("version"),
            model_type.properties.label("properties"),
            func.ST_AsGeoJSON(model_type.geom).label("geometry_json"),
        ).where(model_type.id == feature_id)
        res = await self.session.execute(stmt)
        return res.one_or_none()

    async def get_layers(self):
        stmt = select(Layer)
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def get_current_version(self, model_type: type, feature_id: UUID):
        stmt = select(model_type.version.label("version")).where(model_type.id == feature_id)
        res = await self.session.execute(stmt)
        return res.one_or_none()

    def get_geom_expr(self, geometry: dict):
        geometry_str = json.dumps(geometry)
        return func.ST_SetSRID(func.ST_GeomFromGeoJSON(geometry_str), 4326)
