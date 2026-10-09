from decimal import Decimal

import pytest

from utility_service.domain_services.edit_geometry.canonicalization import prepare_geometry
from utility_service.domain_services.edit_geometry.policy import GeometryPolicy
from utility_service.domain_services.edit_geometry.structure import validate_transition
from utility_service.domain_services.edit_geometry.types import (
    GeometryRuleError,
    InvalidGeometryContext,
)
from utility_service.domain_services.tests.geometry_test_support import BASELINE, MOVED, line


POLICY = GeometryPolicy(Decimal("0.0000001"))


@pytest.mark.parametrize(
    "current, geometry, operation, noop",
    [
        (BASELINE, BASELINE, "unchanged", True),
        (BASELINE, MOVED, "updated", False),
        (MOVED, MOVED, "updated", True),
        (MOVED, BASELINE, "unchanged", False),
    ],
)
def test_transition_distinguishes_baseline_and_current(
    current,
    geometry,
    operation,
    noop,
):
    result = validate_transition(
        BASELINE,
        current,
        prepare_geometry(
            geometry,
            BASELINE,
            POLICY,
        ),
    )
    assert result.operation == operation
    assert result.is_noop is noop


def test_repeated_move_of_same_vertex_is_allowed():
    request = line(
        (65.52, 44.82),
        (65.525, 44.8225),
        (65.53, 44.82),
    )
    result = validate_transition(
        BASELINE,
        MOVED,
        prepare_geometry(
            request,
            BASELINE,
            POLICY,
        ),
    )
    assert result.vertex_index == 1
    assert not result.is_noop


def test_switching_vertex_requires_separate_revert():
    baseline = line(
        (0, 0),
        (1, 1),
        (2, 2),
        (3, 3),
    )
    current = line(
        (0, 0),
        (1, 2),
        (2, 2),
        (3, 3),
    )
    request = line(
        (0, 0),
        (1, 1),
        (2, 3),
        (3, 3),
    )
    prepared = prepare_geometry(
        request,
        baseline,
        POLICY,
    )
    assert prepared.rejection_code is None
    with pytest.raises(
        GeometryRuleError,
        match="GEOMETRY_STRUCTURE_CHANGED",
    ):
        validate_transition(
            baseline,
            current,
            prepared,
        )
    assert (
        validate_transition(
            baseline,
            baseline,
            prepared,
        ).vertex_index
        == 2
    )


def test_multiple_current_changes_are_corrupt_context():
    baseline = line(
        (0, 0),
        (1, 1),
        (2, 2),
        (3, 3),
    )
    current = line(
        (0, 0),
        (1, 2),
        (2, 3),
        (3, 3),
    )
    with pytest.raises(InvalidGeometryContext):
        validate_transition(
            baseline,
            current,
            prepare_geometry(
                baseline,
                baseline,
                POLICY,
            ),
        )


def test_endpoint_rejection_is_not_a_successful_transition():
    request = line(
        (65, 44.82),
        (65.525, 44.8205),
        (65.53, 44.82),
    )
    with pytest.raises(
        GeometryRuleError,
        match="GEOMETRY_STRUCTURE_CHANGED",
    ):
        validate_transition(
            BASELINE,
            BASELINE,
            prepare_geometry(
                request,
                BASELINE,
                POLICY,
            ),
        )
