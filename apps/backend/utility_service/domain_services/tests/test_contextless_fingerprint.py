from dataclasses import replace
from decimal import Decimal
from uuid import UUID
import json

import pytest

from utility_service.domain_services.edit_geometry.contextless_fingerprint import (
    contextless_command_fingerprint,
    contextless_fingerprint_payload,
)
from utility_service.domain_services.edit_geometry.policy import GeometryPolicy
from utility_service.domain_services.tests.geometry_test_support import MOVED, line
from utility_service.domain_services.tests.test_geometry_fingerprint import CONTEXT


POLICY = GeometryPolicy(Decimal("0.0000001"))
GOLDEN = '{"actorUserId":"00000000-0000-0000-0000-000000000004","baseline":{"defaultStateId":"00000000-0000-0000-0000-000000000005","networkRevision":1},"commandType":"replace_feature_geometry","draftVersionToken":"1","editVersionId":"00000000-0000-0000-0000-000000000002","featureId":"00000000-0000-0000-0000-000000000003","fingerprintVersion":1,"geometry":{"coordinates":[["65.52","44.82"],["65.525","44.8215"],["65.53","44.82"]],"type":"LineString"},"geometryPolicy":{"origin":["0","0"],"roundingMode":"ROUND_HALF_AWAY_FROM_ZERO","srid":4326,"version":1,"xyResolution":"0.0000001"},"geometryRepresentation":"grid_aligned","identityMode":"contextless","workOrderId":"00000000-0000-0000-0000-000000000001"}'


def fingerprint(
    geometry=MOVED,
    context=CONTEXT,
    policy=POLICY,
):
    return contextless_command_fingerprint(
        context,
        policy,
        geometry,
    )


def test_contextless_golden_bytes_and_independent_digest():
    assert (
        contextless_fingerprint_payload(
            CONTEXT,
            POLICY,
            MOVED,
        )
        == GOLDEN.encode()
    )
    assert (
        fingerprint()
        == "geom-contextless-v1:sha256:0fb9c75959c3930c735f1a242a124287f74b293c30b7883fd5d8537c1bac98fa"
    )


def test_contextless_grid_equivalence():
    equivalent = line(
        ("65.520", "44.82"),
        ("65.52500001", "44.8215"),
        ("65.53", "44.82"),
    )
    assert fingerprint(equivalent) == fingerprint()
    assert fingerprint(
        line(
            (1, 2),
            (3, 4),
        )
    ) == fingerprint(
        line(
            ("1e0", "2.0"),
            (3, 4),
        )
    )


def test_contextless_rounding_boundary():
    assert fingerprint(
        line(
            (0, 0),
            ("65.525000049", 1),
        )
    ) != fingerprint(
        line(
            (0, 0),
            ("65.525000051", 1),
        )
    )
    payload = json.loads(
        contextless_fingerprint_payload(
            CONTEXT,
            POLICY,
            line(
                ("0.00000015", "-0.00000015"),
                (1, 2),
            ),
        )
    )
    assert payload["geometry"]["coordinates"] == [["0.0000002", "-0.0000002"], ["1", "2"]]
    assert payload["baseline"] == {
        "defaultStateId": str(UUID(int=5)),
        "networkRevision": 1,
    }
    assert "vertexIndex" not in payload
    assert payload["identityMode"] == "contextless"


@pytest.mark.parametrize(
    "field,value",
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
def test_contextless_identity_fields(
    field,
    value,
):
    assert (
        fingerprint(
            context=replace(
                CONTEXT,
                **{field: value},
            )
        )
        != fingerprint()
    )


def test_contextless_shape_and_policy_are_identity():
    assert (
        fingerprint(
            replace(
                MOVED,
                coordinates=MOVED.coordinates[::-1],
            )
        )
        != fingerprint()
    )
    assert (
        fingerprint(
            replace(
                MOVED,
                coordinates=MOVED.coordinates[:2],
            )
        )
        != fingerprint()
    )
    assert fingerprint(policy=GeometryPolicy(Decimal("0.000001"))) != fingerprint()
