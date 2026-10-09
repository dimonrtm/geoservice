from dataclasses import replace
from decimal import Decimal
import json
from uuid import UUID

import pytest

from utility_service.domain_services.edit_geometry.canonicalization import prepare_geometry
from utility_service.domain_services.edit_geometry.fingerprint import (
    baseline_structure_hash,
    command_fingerprint,
    fingerprint_payload,
)
from utility_service.domain_services.edit_geometry.policy import GeometryPolicy
from utility_service.domain_services.edit_geometry.types import FingerprintContext, GeometryValue
from utility_service.domain_services.tests.geometry_test_support import BASELINE, MOVED, line


POLICY = GeometryPolicy(Decimal("0.0000001"))
CONTEXT = FingerprintContext(
    work_order_id=UUID(int=1),
    edit_version_id=UUID(int=2),
    feature_id=UUID(int=3),
    actor_user_id=UUID(int=4),
    default_state_id=UUID(int=5),
    base_network_revision=1,
    draft_version_token="1",
)
GOLDEN = '{"actorUserId":"00000000-0000-0000-0000-000000000004","baseline":{"defaultStateId":"00000000-0000-0000-0000-000000000005","networkRevision":1,"structureHash":"sha256:342079da420e7190d6e5156e1ba210a5c41147c464569c4b8578f3568e8e8a39"},"commandType":"replace_feature_geometry","draftVersionToken":"1","editVersionId":"00000000-0000-0000-0000-000000000002","featureId":"00000000-0000-0000-0000-000000000003","fingerprintVersion":1,"geometry":{"coordinates":[["65.52","44.82"],["65.525","44.8215"],["65.53","44.82"]],"type":"LineString"},"geometryPolicy":{"origin":["0","0"],"roundingMode":"ROUND_HALF_AWAY_FROM_ZERO","srid":4326,"version":1,"xyResolution":"0.0000001"},"geometryRepresentation":"baseline_aligned","vertexIndex":1,"workOrderId":"00000000-0000-0000-0000-000000000001"}'


def test_fingerprint_matches_independent_golden_bytes_and_digest():
    prepared = prepare_geometry(
        MOVED,
        BASELINE,
        POLICY,
    )
    assert (
        baseline_structure_hash(BASELINE)
        == "sha256:342079da420e7190d6e5156e1ba210a5c41147c464569c4b8578f3568e8e8a39"
    )
    assert (
        fingerprint_payload(
            CONTEXT,
            BASELINE,
            POLICY,
            prepared,
        )
        == GOLDEN.encode()
    )
    assert (
        command_fingerprint(
            CONTEXT,
            BASELINE,
            POLICY,
            prepared,
        )
        == "geom-v1:sha256:1d01069ca8b22bf671865e99d831dc1ebc0fa2f65d71b64c972d99e2c414b622"
    )


@pytest.mark.parametrize(
    "field, value",
    [
        ("work_order_id", UUID(int=11)),
        ("edit_version_id", UUID(int=12)),
        ("feature_id", UUID(int=13)),
        ("actor_user_id", UUID(int=14)),
        ("default_state_id", UUID(int=15)),
        ("base_network_revision", 2),
        ("draft_version_token", "01"),
    ],
)
def test_each_context_field_changes_fingerprint(
    field,
    value,
):
    prepared = prepare_geometry(
        MOVED,
        BASELINE,
        POLICY,
    )
    assert command_fingerprint(
        replace(
            CONTEXT,
            **{
                field: value,
            },
        ),
        BASELINE,
        POLICY,
        prepared,
    ) != command_fingerprint(
        CONTEXT,
        BASELINE,
        POLICY,
        prepared,
    )


def test_grid_equivalent_requests_and_decimal_notation_match():
    noisy = line(
        ("65.52000001", "44.82"),
        ("65.5250", "44.82150001"),
        ("65.530", "44.82"),
    )
    assert command_fingerprint(
        CONTEXT,
        BASELINE,
        POLICY,
        prepare_geometry(
            noisy,
            BASELINE,
            POLICY,
        ),
    ) == command_fingerprint(
        CONTEXT,
        BASELINE,
        POLICY,
        prepare_geometry(
            MOVED,
            BASELINE,
            POLICY,
        ),
    )


def test_policy_and_baseline_coordinates_change_identity():
    prepared = prepare_geometry(
        MOVED,
        BASELINE,
        POLICY,
    )
    assert command_fingerprint(
        CONTEXT,
        BASELINE,
        GeometryPolicy(Decimal("0.00000025")),
        prepared,
    ) != command_fingerprint(
        CONTEXT,
        BASELINE,
        POLICY,
        prepared,
    )
    different_baseline = line(
        (65.52, 44.82),
        (65.525, 44.8206),
        (65.53, 44.82),
    )
    assert baseline_structure_hash(different_baseline) != baseline_structure_hash(BASELINE)


def test_unmatched_structure_keeps_raw_values_without_grid_rounding():
    first = line(
        (65.52, 44.82),
        ("65.53000001", 44.82),
    )
    second = line(
        (65.52, 44.82),
        ("65.53000002", 44.82),
    )
    a = prepare_geometry(
        first,
        BASELINE,
        POLICY,
    )
    b = prepare_geometry(
        second,
        BASELINE,
        POLICY,
    )
    payload = json.loads(
        fingerprint_payload(
            CONTEXT,
            BASELINE,
            POLICY,
            a,
        )
    )
    assert payload["geometryRepresentation"] == "unmatched_structure"
    assert payload["vertexIndex"] is None
    assert payload["geometry"]["coordinates"][-1][0] == "65.53000001"
    assert command_fingerprint(
        CONTEXT,
        BASELINE,
        POLICY,
        a,
    ) != command_fingerprint(
        CONTEXT,
        BASELINE,
        POLICY,
        b,
    )


def test_point_baseline_has_durable_ineligible_identity():
    baseline = GeometryValue(
        "Point",
        ((Decimal("65.52"), Decimal("44.82")),),
    )
    prepared = prepare_geometry(
        MOVED,
        baseline,
        POLICY,
    )
    payload = json.loads(
        fingerprint_payload(
            CONTEXT,
            baseline,
            POLICY,
            prepared,
        )
    )
    assert prepared.rejection_code == "FEATURE_NOT_EDITABLE"
    assert payload["geometryRepresentation"] == "unmatched_structure"


def test_rejection_verdict_and_global_settings_are_not_identity(monkeypatch):
    prepared = prepare_geometry(
        MOVED,
        BASELINE,
        POLICY,
    )
    original = command_fingerprint(
        CONTEXT,
        BASELINE,
        POLICY,
        prepared,
    )
    monkeypatch.setenv(
        "UTILITY_GEOMETRY_XY_RESOLUTION",
        "1",
    )
    assert (
        command_fingerprint(
            CONTEXT,
            BASELINE,
            POLICY,
            replace(
                prepared,
                rejection_code="GEOMETRY_OUTSIDE_AOI",
            ),
        )
        == original
    )


def test_endpoint_violation_and_baseline_revert_have_different_fingerprints():
    invalid = line(
        (65.521, 44.82),
        (65.525, 44.8205),
        (65.53, 44.82),
    )
    prepared = prepare_geometry(
        invalid,
        BASELINE,
        POLICY,
    )
    assert prepared.rejection_code == "GEOMETRY_STRUCTURE_CHANGED"
    assert command_fingerprint(
        CONTEXT,
        BASELINE,
        POLICY,
        prepared,
    ) != command_fingerprint(
        CONTEXT,
        BASELINE,
        POLICY,
        prepare_geometry(
            BASELINE,
            BASELINE,
            POLICY,
        ),
    )


def test_vertex_order_and_multiple_changes_remain_in_fingerprint():
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
    reversed_request = replace(
        request,
        coordinates=tuple(reversed(request.coordinates)),
    )
    assert prepared.rejection_code == "GEOMETRY_STRUCTURE_CHANGED"
    assert command_fingerprint(
        CONTEXT,
        baseline,
        POLICY,
        prepared,
    ) != command_fingerprint(
        CONTEXT,
        baseline,
        POLICY,
        prepare_geometry(
            reversed_request,
            baseline,
            POLICY,
        ),
    )
