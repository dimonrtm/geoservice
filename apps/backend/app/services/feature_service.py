from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from domain.exceptions.business_validation_exception import BusinessValidationException
from domain.exceptions.feature_not_found_exception import FeatureNotFoundException
from domain.exceptions.layer_not_found_exception import LayerNotFoundException
from domain.exceptions.version_mismatch_exception import VersionMismatchException
from models.layer import Layer
from repositories.layer_repository import LayerRepository
from schemas.create_feature_in import CreateFeatureIn
from schemas.delete_feature_request import DeleteFeatureRequest
from schemas.delete_feature_response import DeleteFeatureResponse
from schemas.feature_collection_out import FeatureCollectionMetaOut, FeatureCollectionOut
from schemas.feature_out import FeatureOut
from schemas.geojson import FeatureProperties, dump_feature_geometry
from schemas.patch_feature_request import PatchFeatureRequest


class FeatureService:
    def __init__(self, session: AsyncSession, layer_repository: LayerRepository):
        self.session = session
        self.layer_repository = layer_repository

    def to_feature_out(
        self,
        feature_id: UUID,
        version: int,
        properties: FeatureProperties,
        geometry_data: dict[str, object],
    ) -> FeatureOut:
        if not geometry_data:
            raise BusinessValidationException(
                f"У Feature с идентификатором {feature_id} пустая геометрия"
            )
        try:
            return FeatureOut(
                id=feature_id,
                version=version,
                properties=properties,
                geometry=geometry_data,
            )
        except (TypeError, ValidationError, ValueError) as e:
            raise BusinessValidationException(
                f"У Feature с идентификатором {feature_id} невалидная геометрия: {e}"
            ) from e

    def to_feature_collection_out(
        self,
        rows,
        bbox,
        limit_value: int,
        truncated: bool,
        next_cursor: str | None,
    ) -> FeatureCollectionOut:
        features = []
        for row in rows:
            features.append(
                self.to_feature_out(
                    feature_id=row.id,
                    version=row.version,
                    properties=row.properties,
                    geometry_data=row.geometry_data,
                )
            )
        return FeatureCollectionOut(
            features=features,
            meta=FeatureCollectionMetaOut(
                bbox=(bbox.min_lon, bbox.min_lat, bbox.max_lon, bbox.max_lat),
                limit=limit_value,
                returned=len(features),
                truncated=truncated,
                next_cursor=next_cursor,
            ),
        )

    async def get_features_from_bbox(
        self,
        layer_id: UUID,
        bbox,
        limit_value: int | None,
        after_id: UUID | None = None,
    ) -> FeatureCollectionOut:
        limit_value = self.normalize_limit(limit_value)
        layer = await self.layer_repository.get_layer_by_id(layer_id)
        if layer is None:
            raise LayerNotFoundException(f"Слой с идентификатором {layer_id} не найден")
        rows, truncated, next_cursor = await self.layer_repository.list_features_bbox(
            layer, bbox, limit_value, after_id
        )
        return self.to_feature_collection_out(rows, bbox, limit_value, truncated, next_cursor)

    async def create_feature(self, layer_id: UUID, request: CreateFeatureIn) -> FeatureOut:
        async with self.session.begin():
            layer = await self.layer_repository.get_layer_by_id(layer_id)
            if layer is None:
                raise LayerNotFoundException(f"Слой с идентификатором {layer_id} не найден")
            if not self.check_geometry_type_match(request, layer):
                raise BusinessValidationException(
                    "Тип создаваемой геометрии не соответствует типу геометрии слоя"
                )
            row = await self.layer_repository.create_feature(
                layer, dump_feature_geometry(request.geometry), request.properties
            )
            return FeatureOut(
                id=row.id,
                version=row.version,
                properties=request.properties,
                geometry=request.geometry,
            )

    async def update_feature(
        self, layer_id: UUID, feature_id: UUID, request: PatchFeatureRequest
    ) -> FeatureOut:
        async with self.session.begin():
            layer = await self.layer_repository.get_layer_by_id(layer_id)
            if layer is None:
                raise LayerNotFoundException(f"Слой с идентификатором {layer_id} не найден")
            if request.geometry and not self.check_geometry_type_match(request, layer):
                raise BusinessValidationException(
                    "Тип обновляемой геометрии не соответствует типу геометрии слоя"
                )

            current_feature = None
            if request.geometry is None or request.properties is None:
                current_feature = await self.get_feature(layer_id, feature_id)

            (row, model_type) = await self.layer_repository.update_feature_if_version_matches(
                layer,
                feature_id,
                dump_feature_geometry(request.geometry) if request.geometry else None,
                request.properties,
                request.version,
            )
            if row is None:
                await self.version_error_handler(feature_id, request.version, model_type)

            geometry = request.geometry or (current_feature.geometry if current_feature else None)
            properties = request.properties or (
                current_feature.properties if current_feature else None
            )
            if geometry is None or properties is None:
                raise BusinessValidationException(
                    f"Не удалось собрать актуальное состояние feature {feature_id} после update"
                )

            return FeatureOut(
                id=row.id,
                version=row.version,
                properties=properties,
                geometry=geometry,
            )

    async def delete_feature(
        self, layer_id: UUID, feature_id: UUID, request: DeleteFeatureRequest
    ) -> DeleteFeatureResponse:
        async with self.session.begin():
            layer = await self.layer_repository.get_layer_by_id(layer_id)
            if layer is None:
                raise LayerNotFoundException(f"Слой с идентификатором {layer_id} не найден")
            deleted, model_type = await self.layer_repository.delete_feature_if_version_matches(
                layer, feature_id, request.version
            )
            if not deleted:
                await self.version_error_handler(feature_id, request.version, model_type)
            return DeleteFeatureResponse(featureId=feature_id)

    async def get_feature(self, layer_id: UUID, feature_id: UUID) -> FeatureOut:
        layer = await self.layer_repository.get_layer_by_id(layer_id)
        if layer is None:
            raise LayerNotFoundException(f"Слой с идентификатором {layer_id} не найден")
        row = await self.layer_repository.get_feature(layer, feature_id)
        if row is None:
            raise FeatureNotFoundException(f"Feature с идентификатором {feature_id} не найдена")
        return self.to_feature_out(
            feature_id=row.id,
            version=row.version,
            properties=row.properties,
            geometry_data=row.geometry_data,
        )

    def normalize_limit(self, limit_value: int | None) -> int:
        if limit_value is None:
            limit_value = 500
        if limit_value < 1:
            limit_value = 1
        if limit_value > 5000:
            limit_value = 5000
        return limit_value

    def check_geometry_type_match(self, request: CreateFeatureIn, layer: Layer) -> bool:
        geojson_type = request.geometry.type
        expected = layer.geometry_type
        return geojson_type == expected

    async def version_error_handler(
        self, feature_id: UUID, expected_version: int, model_type: type
    ):
        current = await self.layer_repository.get_current_version(model_type, feature_id)
        if current is None:
            raise FeatureNotFoundException(f"Feature с идентификатором {feature_id} не найдена")
        raise VersionMismatchException(
            feature_id=feature_id,
            request_version=expected_version,
            current_version=current.version,
            message=(
                f"Ожидалась версия {current.version}, а получили {expected_version}. "
                "Перезагрузите фичу и отредактируйте ее снова"
            ),
        )
