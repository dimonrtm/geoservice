from dataclasses import replace

import pytest

from utility_service.domain_services.edit_geometry.save_policy import (
    EditRejection,
    NeedCurrent,
    SpatialFacts,
    begin_baseline,
    begin_save_validation,
)
from utility_service.domain_services.edit_geometry.types import PreparedGeometry
from utility_service.domain_services.tests.geometry_test_support import BASELINE, MOVED


GOOD = SpatialFacts(geometry_valid=True, aoi_valid=True, aoi_covered=True)
PREPARED = PreparedGeometry("baseline_aligned", MOVED, 1, None)


@pytest.mark.parametrize(
    "kind,operation", [("junction", "unchanged"), ("line", "created"), ("line", "deleted")]
)
def test_ineligible_target_finishes_before_requesting_baseline(kind, operation):
    assert begin_baseline(kind, operation).code == "FEATURE_NOT_EDITABLE"


def test_baseline_type_and_short_line_have_distinct_outcomes():
    phase = begin_baseline("line", "unchanged")
    assert phase.evaluate(BASELINE) is None
    assert phase.evaluate(replace(BASELINE, type="Point")).code == "WORK_ORDER_CONTEXT_INVALID"
    assert (
        phase.evaluate(replace(BASELINE, coordinates=BASELINE.coordinates[:2])).code
        == "FEATURE_NOT_EDITABLE"
    )


def start(current=BASELINE, other=False, prepared=PREPARED):
    phase = begin_save_validation("line", "unchanged", other, prepared)
    need_current = phase.evaluate(BASELINE)
    assert isinstance(need_current, NeedCurrent)
    return need_current.evaluate(current)


def test_full_validation_requests_current_only_for_an_eligible_baseline():
    rejected = begin_save_validation("line", "deleted", True, PREPARED)
    assert rejected.code == "FEATURE_NOT_EDITABLE"
    phase = begin_save_validation("line", "updated", True, PREPARED)
    short = replace(BASELINE, coordinates=BASELINE.coordinates[:2])
    assert phase.evaluate(short).code == "FEATURE_NOT_EDITABLE"
    damage = EditRejection.invalid_context("Область работ отсутствует.")
    assert phase.evaluate(BASELINE).evaluate(damage) == damage


@pytest.mark.parametrize("field", ["geometry_valid", "aoi_valid", "aoi_covered"])
@pytest.mark.parametrize("source", ["baseline", "current"])
def test_saved_spatial_error_precedes_other_changed_object(source, field):
    phase = start(other=True)
    if source == "current":
        phase = phase.evaluate(GOOD)
    assert phase.source == source
    assert phase.evaluate(replace(GOOD, **{field: False})).code == "WORK_ORDER_CONTEXT_INVALID"


def test_saved_state_then_other_object_precede_candidate_error():
    deferred = replace(PREPARED, rejection_code="GEOMETRY_STRUCTURE_CHANGED")
    assert start(MOVED, True, deferred).code == "WORK_ORDER_CONTEXT_INVALID"
    result = start(other=True, prepared=deferred).evaluate(GOOD).evaluate(GOOD)
    assert result.code == "MULTIPLE_FEATURE_CHANGE_NOT_ALLOWED"


@pytest.mark.parametrize(
    "valid,covered,code",
    [
        (True, True, None),
        (True, False, "GEOMETRY_OUTSIDE_AOI"),
        (False, True, "GEOMETRY_INVALID"),
        (False, False, "GEOMETRY_INVALID"),
    ],
)
def test_candidate_spatial_decision_including_noop(valid, covered, code):
    noop = replace(PREPARED, geometry=BASELINE, vertex_index=None)
    phase = start(prepared=noop).evaluate(GOOD).evaluate(GOOD)
    assert phase.transition.is_noop
    result = phase.evaluate(replace(GOOD, geometry_valid=valid, aoi_covered=covered))
    if code:
        assert isinstance(result, EditRejection)
        assert result.code == code
    else:
        assert result == phase.transition
