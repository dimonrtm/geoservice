import pytest
from pydantic import ValidationError

from utility_service.use_cases.schemas.feature.patch_feature_request import PatchFeatureRequest


@pytest.mark.parametrize(
    "payload",
    [
        {"version": 1, "properties": {}},
        {"version": 1, "geometry": {"type": "Point", "coordinates": [1, 2]}},
        {"version": 1, "geometry": None, "properties": None},
    ],
)
def test_patch_rejects_missing_fields_and_no_changes(payload) -> None:
    with pytest.raises(ValidationError):
        PatchFeatureRequest.model_validate(payload)


def test_patch_accepts_empty_properties_with_unchanged_geometry() -> None:
    request = PatchFeatureRequest.model_validate({"version": 1, "geometry": None, "properties": {}})
    assert request.geometry is None
    assert request.properties == {}


def test_patch_accepts_geometry_with_unchanged_properties() -> None:
    request = PatchFeatureRequest.model_validate(
        {"version": 1, "geometry": {"type": "Point", "coordinates": [1, 2]}, "properties": None}
    )
    assert request.properties is None
    assert request.geometry.model_dump(mode="json") == {"type": "Point", "coordinates": [1, 2]}
