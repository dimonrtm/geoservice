from dataclasses import replace
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from utility_service.domain_services.edit_geometry.types import GeometryValue
from utility_service.infrastructure.postgresql.geometry_codec import encode_geometry
from utility_service.infrastructure.postgresql.repository_rows.edit_version_read import (
    CurrentDraftFeature,
)
from utility_service.infrastructure.postgresql.repositories.default_state_repository import (
    ComparisonBaseline,
    BaselineFeatureGeometry,
)
from utility_service.use_cases.services.version_change_projection import project_version_changes


def geometry(
    points=((1, 1), (2, 2), (3, 3)),
    kind="LineString",
):
    return encode_geometry(
        GeometryValue(
            kind,
            tuple(tuple(Decimal(str(v)) for v in p) for p in points),
        )
    ).hex()


def draft(
    *,
    current=None,
    operation="unchanged",
    visible=True,
):
    baseline_id, work_order_id = uuid4(), uuid4()
    feature_id = uuid4()
    version = SimpleNamespace(
        work_order_id=work_order_id,
        edit_version=SimpleNamespace(
            default_state_id=baseline_id,
            base_network_revision=1,
            draft_revision=1,
        ),
        features=(
            CurrentDraftFeature(feature_id, "line", current or geometry(), operation, visible),
        ),
    )
    state = SimpleNamespace(
        id=baseline_id, work_order_id=work_order_id, base_network_revision=1, status="active"
    )
    baseline = ComparisonBaseline(state, (BaselineFeatureGeometry(feature_id, "line", geometry()),))
    return version, baseline


def test_workspace_projection_states():
    version, baseline = draft()
    initial = project_version_changes(version, baseline)
    assert (
        initial.draft_version_token,
        initial.has_persisted_change_set,
        initial.basic_validation,
        initial.change_set,
    ) == ("1", False, None, None)
    version.edit_version.draft_revision = 2
    version.features = (
        replace(
            version.features[0],
            geometry_ewkb=geometry(((1, 1), (2, 2.1), (3, 3))),
            operation="updated",
        ),
    )
    saved = project_version_changes(version, baseline)
    assert saved.draft_version_token == "2"
    assert saved.has_persisted_change_set is True
    assert saved.basic_validation.geometry_status == "passed"
    assert saved.change_set.feature_id == version.features[0].feature_id
    assert saved.change_set.vertex_index == 1
    assert "baselineGeometry" not in saved.change_set.model_dump(by_alias=True)
    version.edit_version.draft_revision = 3
    version.features = (
        replace(
            version.features[0],
            geometry_ewkb=geometry(),
            operation="unchanged",
        ),
    )
    reverted = project_version_changes(version, baseline)
    assert (
        reverted.draft_version_token,
        reverted.has_persisted_change_set,
        reverted.basic_validation,
        reverted.change_set,
    ) == ("3", False, None, None)


@pytest.mark.parametrize(
    "case",
    [
        "baseline",
        "root",
        "owner",
        "revision",
        "status",
        "missing_current",
        "missing_baseline",
        "type",
        "operation",
        "false_updated",
        "false_unchanged",
        "multiple",
        "endpoint",
        "count",
        "hidden",
        "hidden_unchanged",
        "corrupt",
    ],
)
def test_workspace_projection_rejects_inconsistent_pairs(case):
    version, baseline = draft(
        current=geometry(((1, 1), (2, 2.1), (3, 3))),
        operation="updated",
    )
    pair = version.features[0]
    if case == "baseline":
        baseline = None
    elif case in ("root", "owner", "revision", "status"):
        field, value = {
            "root": ("id", uuid4()),
            "owner": ("work_order_id", uuid4()),
            "revision": ("base_network_revision", 2),
            "status": ("status", "archived"),
        }[case]
        setattr(
            baseline.state,
            field,
            value,
        )
    elif case == "missing_current":
        version.features = ()
    elif case == "missing_baseline":
        baseline = replace(baseline, features=())
    else:
        changes = {
            "type": {
                "feature_type": "junction",
            },
            "operation": {
                "operation": "added",
            },
            "false_updated": {
                "geometry_ewkb": geometry(),
            },
            "false_unchanged": {
                "operation": "unchanged",
            },
            "endpoint": {
                "geometry_ewkb": geometry(((1, 1.1), (2, 2), (3, 3))),
            },
            "count": {
                "geometry_ewkb": geometry(((1, 1), (3, 3))),
            },
            "hidden": {
                "visible": False,
            },
            "hidden_unchanged": {
                "visible": False,
                "operation": "unchanged",
            },
            "corrupt": {
                "geometry_ewkb": "bad",
            },
            "multiple": {},
        }[case]
        version.features = (
            replace(
                pair,
                **changes,
            ),
        )
        if case == "multiple":
            second_id = uuid4()
            version.features += (replace(pair, feature_id=second_id),)
            baseline = replace(
                baseline,
                features=(*baseline.features, replace(baseline.features[0], feature_id=second_id)),
            )
    with pytest.raises(ValueError):
        project_version_changes(version, baseline)


@pytest.mark.parametrize(
    "kind,points,feature_type",
    [("Point", ((1, 1),), "junction"), ("LineString", ((1, 1), (2, 2)), "line")],
)
def test_unchanged_points_and_short_lines_are_not_edit_candidates(
    kind,
    points,
    feature_type,
):
    version, baseline = draft()
    ewkb = geometry(
        points,
        kind,
    )
    version.features = (
        replace(
            version.features[0],
            feature_type=feature_type,
            geometry_ewkb=ewkb,
        ),
    )
    baseline = replace(
        baseline,
        features=(replace(baseline.features[0], feature_type=feature_type, geometry_ewkb=ewkb),),
    )
    assert project_version_changes(version, baseline).has_persisted_change_set is False


def test_signed_zero_does_not_create_diff():
    version, baseline = draft()
    baseline = replace(
        baseline,
        features=(
            replace(baseline.features[0], geometry_ewkb=geometry((("-0.0", 1), (2, 2), (3, 3)))),
        ),
    )
    version.features = (
        replace(
            version.features[0],
            geometry_ewkb=geometry(((0, 1), (2, 2), (3, 3))),
        ),
    )
    assert project_version_changes(version, baseline).has_persisted_change_set is False
