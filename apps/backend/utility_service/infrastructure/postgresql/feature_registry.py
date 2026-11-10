# -*- coding: utf-8 -*-
"""
Created on Sat Jan 10 14:44:27 2026

@author: dimon
"""

from utility_service.infrastructure.postgresql.models.feature_point import FeaturePoint
from utility_service.infrastructure.postgresql.models.feature_polygon import FeaturePolygon
from utility_service.infrastructure.postgresql.models.feature_line import FeatureLine
from utility_service.infrastructure.postgresql.models.feature_multipoint import FeatureMultiPoint
from utility_service.infrastructure.postgresql.models.feature_multiline import FeatureMultiLine
from utility_service.infrastructure.postgresql.models.feature_multipolygon import (
    FeatureMultiPolygon,
)
from utility_service.infrastructure.postgresql.models.layer import Layer
from utility_service.use_cases.domain.exceptions.unknown_storage_table_error import (
    UnknownStorageTableError,
)

FEATURE_MODELS_BY_TABLE: dict[str, type] = {
    "feature_points": FeaturePoint,
    "feature_polygons": FeaturePolygon,
    "feature_lines": FeatureLine,
    "feature_multipoints": FeatureMultiPoint,
    "feature_multipolygons": FeatureMultiPolygon,
    "feature_multilines": FeatureMultiLine,
}

ALL_FEATURE_MODELS = [
    FeaturePoint,
    FeaturePolygon,
    FeatureLine,
    FeatureMultiPoint,
    FeatureMultiPolygon,
    FeatureMultiLine,
]


def resolve_feature_model(storage_table: str) -> type:
    if storage_table not in FEATURE_MODELS_BY_TABLE.keys():
        raise UnknownStorageTableError("Для данного слоя не найдена подходящая модель")
    return FEATURE_MODELS_BY_TABLE[storage_table]


def get_layer_feature_model(layer: Layer) -> type:
    return resolve_feature_model(layer.storage_table)
