# -*- coding: utf-8 -*-
"""
Created on Tue Jan  6 20:03:39 2026

@author: dimon
"""

import json
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from schemas.feature_out import FeatureOut
from schemas.feature_collection_out import FeatureCollectionOut
from repositories.layer_repository import LayerRepository


class FeatureService:
    def __init__(self, session: AsyncSession, layer_repository: LayerRepository):
        self.session = session
        self.layer_repository = layer_repository

    def to_feature_out(
        self,
        feature_id: UUID,
        version: int,
        properties: dict[str, Any],
        geometry_json: str,
    ) -> FeatureOut:
        return FeatureOut(
            id=feature_id,
            version=version,
            properties=properties,
            geometry=json.loads(geometry_json),
        )

    def to_feature_collection_out(
        self, rows: list[tuple[UUID, int, dict[str, Any], str]]
    ) -> FeatureCollectionOut:
        features = []
        for feature_id, version, properties, geometry_json in rows:
            features.append(
                self.to_feature_out(
                    id=feature_id,
                    version=version,
                    properties=properties,
                    geometry=json.loads(geometry_json),
                )
            )
        return FeatureCollectionOut(features=features)

    async def get_features_from_bbox(
        self, layer_id: UUID, bbox, limit_value: int | None
    ) -> FeatureCollectionOut:
        limit_value = self.normalize_limit(limit_value)
        rows = await self.layer_repository.list_features_bbox(
            layer_id, bbox, limit_value
        )
        return self.to_feature_collection_out(rows)

    def normalize_limit(self, limit_value: int | None) -> int:
        if limit_value is None:
            limit_value = 500
        if limit_value < 1:
            limit_value = 1
        if limit_value > 5000:
            limit_value = 5000
        return limit_value
