# -*- coding: utf-8 -*-
"""
Created on Sat Jan 10 17:32:50 2026

@author: dimon
"""

from fastapi import APIRouter, Depends, status
from fastapi.responses import Response
from utility_service.use_cases.schemas.feature.feature_collection_out import FeatureCollectionOut
from utility_service.use_cases.schemas.feature.feature_out import FeatureOut
from utility_service.use_cases.schemas.feature.create_feature_in import CreateFeatureIn
from utility_service.use_cases.schemas.feature.patch_feature_request import PatchFeatureRequest
from utility_service.use_cases.schemas.feature.patch_feature_succes_response import (
    PatchFeatureSuccesResponse,
)
from utility_service.use_cases.schemas.feature.delete_feature_request import DeleteFeatureRequest
from utility_service.use_cases.schemas.feature.delete_feature_response import DeleteFeatureResponse
from utility_service.use_cases.schemas.layer.layer_list_out import LayerListOut
from utility_service.use_cases.deps import get_feature_service
from utility_service.use_cases.deps import get_layer_service
from utility_service.use_cases.services.feature_service import FeatureService
from utility_service.use_cases.services.layer_service import LayerService
from utility_service.domain_services.bbox import parse_bbox
from uuid import UUID
from .auth import get_current_user, require_editor

layers_router = APIRouter(
    prefix="/api/v1/layers", tags=["layers"], dependencies=[Depends(get_current_user)]
)


@layers_router.get("", response_model=LayerListOut)
async def get_layers(layer_service: LayerService = Depends(get_layer_service)) -> LayerListOut:
    return await layer_service.get_layers()


@layers_router.get("/{layer_id}/features", response_model=FeatureCollectionOut)
async def get_layer_features_from_bbox(
    layer_id: UUID,
    bbox: str,
    limit: int | None = None,
    after_id: UUID | None = None,
    feature_service: FeatureService = Depends(get_feature_service),
) -> FeatureCollectionOut:
    bb = parse_bbox(bbox)
    return await feature_service.get_features_from_bbox(layer_id, bb, limit, after_id)


@layers_router.post(
    "/{layer_id}/features",
    dependencies=[Depends(require_editor)],
    status_code=status.HTTP_201_CREATED,
    response_model=FeatureOut,
)
async def create_feature(
    layer_id: UUID,
    request: CreateFeatureIn,
    response: Response,
    feature_service: FeatureService = Depends(get_feature_service),
) -> FeatureOut:
    feature = await feature_service.create_feature(layer_id, request)
    response.headers["Location"] = f"/api/v1/layers/{layer_id}/features/{feature.id}"
    return feature


@layers_router.patch(
    "/{layer_id}/features/{feature_id}",
    dependencies=[Depends(require_editor)],
    response_model=PatchFeatureSuccesResponse,
)
async def update_feature(
    layer_id: UUID,
    feature_id: UUID,
    request: PatchFeatureRequest,
    feature_service: FeatureService = Depends(get_feature_service),
) -> PatchFeatureSuccesResponse:
    feature = await feature_service.update_feature(layer_id, feature_id, request)
    return PatchFeatureSuccesResponse(feature=feature)


@layers_router.delete(
    "/{layer_id}/features/{feature_id}",
    dependencies=[Depends(require_editor)],
    response_model=DeleteFeatureResponse,
)
async def delete_feature(
    layer_id: UUID,
    feature_id: UUID,
    request: DeleteFeatureRequest,
    feature_service: FeatureService = Depends(get_feature_service),
) -> DeleteFeatureResponse:
    return await feature_service.delete_feature(layer_id, feature_id, request)


@layers_router.get("/{layer_id}/features/{feature_id}", response_model=FeatureOut)
async def get_feature(
    layer_id: UUID, feature_id: UUID, feature_service: FeatureService = Depends(get_feature_service)
) -> FeatureOut:
    feature = await feature_service.get_feature(layer_id, feature_id)
    return feature
