# -*- coding: utf-8 -*-
"""
Created on Sat Jan 10 17:32:50 2026

@author: dimon
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from schemas.feature_collection_out import FeatureCollectionOut
from schemas.feature_out import FeatureOut
from schemas.create_feature_in import CreateFeatureIn
from .deps import get_feature_service
from services.feature_service import FeatureService
from domain.bbox import parse_bbox
from uuid import UUID
from .auth import get_current_user, require_editor

layers_router = APIRouter(
    prefix="/api/v1/layers", tags=["layers"], dependencies=[Depends(get_current_user)]
)


@layers_router.get("/{layer_id}/features", response_model=FeatureCollectionOut)
async def get_layer_features_from_bbox(
    layer_id: UUID,
    bbox: str,
    limit: int | None = None,
    feature_service: FeatureService = Depends(get_feature_service),
    user=Depends(get_current_user),
) -> FeatureCollectionOut:
    if user.get("role") in ("viewer", "editor"):
        try:
            bb = parse_bbox(bbox)
            return await feature_service.get_features_from_bbox(layer_id, bb, limit)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
    else:
        raise HTTPException(
            status_code=403,
            detail="Отправлять запросы на чтение могут только пользователи с ролями 'viewer' или 'editor'",
        )


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
    try:
        feature = await feature_service.create_feature(layer_id, request)
        response.headers["Location"] = f"/api/v1/layers/{layer_id}/features/{feature.id}"
        return feature
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
