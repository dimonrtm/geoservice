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
from schemas.create_feature_in import CreateFeatureIn
from schemas.patch_feature_request import PatchFeatureRequest
from schemas.delete_feature_request import DeleteFeatureRequest
from repositories.layer_repository import LayerRepository
from models.layer import Layer
from domain.exceptions.layer_not_found_exception import LayerNotFoundException
from domain.exceptions.feature_not_found_exception import FeatureNotFoundException
from domain.exceptions.version_mismatch_exception import VersionMismatchException


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
        if not geometry_json:
            raise ValueError(f"У Feature с идентифкатором {feature_id} пустая геометрия")
        try:
            return FeatureOut(
                id=feature_id,
                version=version,
                properties=properties,
                geometry=json.loads(geometry_json),
            )
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(
                f"У Feature с идентификатором {feature_id} невалидный JSON геометрии: {e}"
            )

    def to_feature_collection_out(self, rows) -> FeatureCollectionOut:
        features = []
        for row in rows:
            features.append(
                self.to_feature_out(
                    feature_id=row.id,
                    version=row.version,
                    properties=row.properties,
                    geometry_json=row.geometry_json,
                )
            )
        return FeatureCollectionOut(features=features)

    async def get_features_from_bbox(
        self, layer_id: UUID, bbox, limit_value: int | None
    ) -> FeatureCollectionOut:
        limit_value = self.normalize_limit(limit_value)
        layer = await self.layer_repository.get_layer_by_id(layer_id)
        if layer is None:
            raise LayerNotFoundException(f"Слой с идентификатором {layer_id} не найден")
        rows = await self.layer_repository.list_features_bbox(layer, bbox, limit_value)
        return self.to_feature_collection_out(rows)

    async def create_feature(self, layer_id: UUID, request: CreateFeatureIn) -> FeatureOut:
        async with self.session.begin():
            layer = await self.layer_repository.get_layer_by_id(layer_id)
            if layer is None:
                raise LayerNotFoundException(f"Слой с идентификатором {layer_id} не найден")
            if not self.check_geometry_type_match(request, layer):
                raise ValueError("Тип создаваемой геометрии не соответствует типу геометрии слоя")
            row = await self.layer_repository.create_feature(
                layer, request.geometry, request.properties
            )
            return self.to_feature_out(
                feature_id=row.id,
                version=row.version,
                properties=row.properties,
                geometry_json=row.geometry_json,
            )

    async def update_feature(
        self, layer_id: UUID, feature_id: UUID, request: PatchFeatureRequest
    ) -> FeatureOut:
        async with self.session.begin():
            layer = await self.layer_repository.get_layer_by_id(layer_id)
            if layer is None:
                raise LayerNotFoundException(f"Слой с идентификатором {layer_id} не найден")
            if request.geometry and not self.check_geometry_type_match(request, layer):
                raise ValueError("Тип обновляемой геометрии не соответствует типу геометрии слоя")
            (row, model_type) = await self.layer_repository.update_feature_if_version_matches(
                layer, feature_id, request.geometry, request.properties, request.version
            )
            if row is None:
                await self.version_error_handler(feature_id, request.version, model_type)
            return self.to_feature_out(
                feature_id=row.id,
                version=row.version,
                properties=row.properties,
                geometry_json=row.geometry_json,
            )

    async def delete_feature(
        self, layer_id: UUID, feature_id: UUID, request: DeleteFeatureRequest
    ) -> dict[str, Any]:
        async with self.session.begin():
            layer = await self.layer_repository.get_layer_by_id(layer_id)
            if layer is None:
                raise LayerNotFoundException(f"Слой с идентификатором {layer_id} не найден")
            deleted, model_type = await self.layer_repository.delete_feature_if_version_matches(
                layer, feature_id, request.version
            )
            if not deleted:
                await self.version_error_handler(feature_id, request.version, model_type)
            return {"status": "deleted", "featureId": str(feature_id)}

    def normalize_limit(self, limit_value: int | None) -> int:
        if limit_value is None:
            limit_value = 500
        if limit_value < 1:
            limit_value = 1
        if limit_value > 5000:
            limit_value = 5000
        return limit_value

    def check_geometry_type_match(self, request: CreateFeatureIn, layer: Layer) -> bool:
        geojson_type = request.geometry.get("type")
        expected = layer.geometry_type
        return geojson_type == expected

    async def version_error_handler(
        self, feature_id: UUID, expected_version: int, model_type: type
    ):
        current = await self.layer_repository.get_current_version(model_type, feature_id)
        if current is None:
            raise FeatureNotFoundException(f"Feature с идентификатором {feature_id} не найдена")
        else:
            raise VersionMismatchException(
                feature_id=feature_id,
                request_version=expected_version,
                current_version=current.version,
                message=f"Ожидалась версия {current.version}, а получили {expected_version}. Перезагрузите фичу и отредактируйте ее снова",
            )
