from decimal import Decimal

import pytest

from utility_service.domain_services.edit_geometry.canonicalization import prepare_geometry
from utility_service.domain_services.edit_geometry.policy import GeometryPolicy
from utility_service.domain_services.tests.geometry_test_support import BASELINE, MOVED, line


POLICY = GeometryPolicy(Decimal("0.0000001"))


def test_noise_restores_exact_off_grid_baseline_ordinates():
    baseline = line(
        ("65.52000004", "44.82000004"),
        ("65.52500004", "44.82050004"),
        ("65.53000004", "44.82000004"),
    )
    request = line(
        ("65.52000003", "44.82000003"),
        ("65.52500003", "44.8215"),
        ("65.53000003", "44.82000003"),
    )
    prepared = prepare_geometry(
        request,
        baseline,
        POLICY,
    )
    assert prepared.rejection_code is None
    assert prepared.geometry.coordinates[0] == baseline.coordinates[0]
    assert prepared.geometry.coordinates[-1] == baseline.coordinates[-1]
    assert prepared.geometry.coordinates[1] == (Decimal("65.52500004"), Decimal("44.8215"))
    assert (
        prepare_geometry(
            prepared.geometry,
            baseline,
            POLICY,
        ).geometry
        == prepared.geometry
    )
    assert (
        prepare_geometry(
            baseline,
            baseline,
            POLICY,
        ).geometry
        == baseline
    )


def test_multiple_raw_internal_changes_can_collapse_to_one():
    baseline = line(
        (0, 0),
        (1, 1),
        (2, 2),
        (3, 3),
    )
    request = line(
        (0, 0),
        ("1.00000001", 1),
        (2, "2.00000016"),
        (3, 3),
    )
    prepared = prepare_geometry(
        request,
        baseline,
        POLICY,
    )
    assert prepared.vertex_index == 2
    assert prepared.geometry.coordinates[1] == baseline.coordinates[1]
    assert prepared.geometry.coordinates[2][1] == Decimal("2.0000002")
    assert prepared.rejection_code is None


@pytest.mark.parametrize(
    "geometry, expected",
    [
        (
            line(
                (65, 44),
                (65.525, 44.8215),
                (65.53, 44.82),
            ),
            "GEOMETRY_STRUCTURE_CHANGED",
        ),
        (
            line(
                (65.52, 44.82),
                (65.53, 44.82),
            ),
            "GEOMETRY_STRUCTURE_CHANGED",
        ),
    ],
)
def test_rejected_requests_still_have_complete_identity(
    geometry,
    expected,
):
    prepared = prepare_geometry(
        geometry,
        BASELINE,
        POLICY,
    )
    assert prepared.rejection_code == expected
    assert len(prepared.geometry.coordinates) == len(geometry.coordinates)
    assert prepared.vertex_index is None


def test_both_axes_of_one_vertex_are_one_change():
    request = line(
        (65.52, 44.82),
        (65.526, 44.8215),
        (65.53, 44.82),
    )
    assert (
        prepare_geometry(
            request,
            BASELINE,
            POLICY,
        ).vertex_index
        == 1
    )


def test_result_outside_latitude_range_is_not_clamped():
    baseline = line(
        (0, 0),
        (1, 1),
        (2, 0),
    )
    request = line(
        (0, 0),
        (1, 90),
        (2, 0),
    )
    prepared = prepare_geometry(
        request,
        baseline,
        GeometryPolicy(Decimal("100")),
    )
    assert prepared.geometry.coordinates[1][1] == Decimal("100")
    assert prepared.rejection_code == "GEOMETRY_INVALID"


def test_two_vertex_baseline_is_not_editable():
    baseline = line(
        (0, 0),
        (1, 1),
    )
    prepared = prepare_geometry(
        MOVED,
        baseline,
        POLICY,
    )
    assert prepared.rejection_code == "FEATURE_NOT_EDITABLE"
    assert prepared.representation == "unmatched_structure"


def test_multiple_actual_internal_changes_are_rejected_without_truncating_request():
    baseline = line(
        (0, 0),
        (1, 1),
        (2, 2),
        (3, 3),
    )
    request = line(
        (0, 0),
        (1, 2),
        (2, 3),
        (3, 3),
    )
    prepared = prepare_geometry(
        request,
        baseline,
        POLICY,
    )
    assert prepared.rejection_code == "GEOMETRY_STRUCTURE_CHANGED"
    assert prepared.geometry == request
    assert prepared.vertex_index is None
