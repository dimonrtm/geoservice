import pytest

from utility_service.infrastructure.postgresql.feature_registry import (
    ALL_FEATURE_MODELS,
    FEATURE_MODELS_BY_TABLE,
    get_layer_feature_model,
    resolve_feature_model,
)
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


EXPECTED_MODELS = [
    ("feature_points", FeaturePoint),
    ("feature_polygons", FeaturePolygon),
    ("feature_lines", FeatureLine),
    ("feature_multipoints", FeatureMultiPoint),
    ("feature_multipolygons", FeatureMultiPolygon),
    ("feature_multilines", FeatureMultiLine),
]


@pytest.mark.parametrize(("storage_table", "expected_model"), EXPECTED_MODELS)
def test_resolve_feature_model_maps_all_storage_tables(storage_table, expected_model) -> None:
    assert resolve_feature_model(storage_table) is expected_model


@pytest.mark.parametrize(("storage_table", "expected_model"), EXPECTED_MODELS)
def test_get_layer_feature_model_uses_storage_table(storage_table, expected_model) -> None:
    assert get_layer_feature_model(Layer(storage_table=storage_table)) is expected_model


def test_unknown_storage_table_preserves_error() -> None:
    with pytest.raises(UnknownStorageTableError) as raised:
        resolve_feature_model("unknown_table")
    assert str(raised.value) == "Для данного слоя не найдена подходящая модель"


def test_feature_registry_preserves_supported_models() -> None:
    assert set(FEATURE_MODELS_BY_TABLE) == {table for table, _ in EXPECTED_MODELS}
    assert ALL_FEATURE_MODELS == [model for _, model in EXPECTED_MODELS]
