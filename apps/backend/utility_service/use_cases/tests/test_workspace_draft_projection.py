from dataclasses import replace
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from utility_service.domain_services.edit_geometry.types import GeometryValue
from utility_service.infrastructure.postgresql.geometry_codec import encode_geometry
from utility_service.infrastructure.postgresql.repository_rows.workspace import (
    WorkspaceDraftFeaturePairRow,
)
from utility_service.use_cases.services.workspace_draft_projection import project_workspace_draft


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
    return SimpleNamespace(
        work_order=SimpleNamespace(id=work_order_id),
        edit_version=SimpleNamespace(
            default_state_id=baseline_id,
            base_network_revision=1,
            draft_revision=1,
        ),
        baseline_state=SimpleNamespace(
            id=baseline_id,
            work_order_id=work_order_id,
            base_network_revision=1,
            status="active",
        ),
        draft_feature_pairs=(
            WorkspaceDraftFeaturePairRow(
                feature_id=uuid4(),
                current_feature_type="line",
                baseline_feature_type="line",
                current_geometry_ewkb=current or geometry(),
                baseline_geometry_ewkb=geometry(),
                operation=operation,
                visible=visible,
            ),
        ),
    )


def test_workspace_projection_states():
    row = draft()
    initial = project_workspace_draft(row)
    assert (
        initial.draft_version_token,
        initial.has_persisted_change_set,
        initial.basic_validation,
        initial.change_set,
    ) == ("1", False, None, None)
    row.edit_version.draft_revision = 2
    row.draft_feature_pairs = (
        replace(
            row.draft_feature_pairs[0],
            current_geometry_ewkb=geometry(((1, 1), (2, 2.1), (3, 3))),
            operation="updated",
        ),
    )
    saved = project_workspace_draft(row)
    assert saved.draft_version_token == "2"
    assert saved.has_persisted_change_set is True
    assert saved.basic_validation.geometry_status == "passed"
    assert saved.change_set.feature_id == row.draft_feature_pairs[0].feature_id
    assert saved.change_set.vertex_index == 1
    assert saved.change_set.baseline_geometry.model_dump(mode="json")["coordinates"] == [
        [1.0, 1.0],
        [2.0, 2.0],
        [3.0, 3.0],
    ]
    row.edit_version.draft_revision = 3
    row.draft_feature_pairs = (
        replace(
            row.draft_feature_pairs[0],
            current_geometry_ewkb=geometry(),
            operation="unchanged",
        ),
    )
    reverted = project_workspace_draft(row)
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
    row = draft(
        current=geometry(((1, 1), (2, 2.1), (3, 3))),
        operation="updated",
    )
    pair = row.draft_feature_pairs[0]
    if case == "baseline":
        row.baseline_state = None
    elif case in ("root", "owner", "revision", "status"):
        field, value = {
            "root": ("id", uuid4()),
            "owner": ("work_order_id", uuid4()),
            "revision": ("base_network_revision", 2),
            "status": ("status", "archived"),
        }[case]
        setattr(
            row.baseline_state,
            field,
            value,
        )
    else:
        changes = {
            "missing_current": {
                "current_geometry_ewkb": None,
            },
            "missing_baseline": {
                "baseline_geometry_ewkb": None,
            },
            "type": {
                "current_feature_type": "junction",
            },
            "operation": {
                "operation": "added",
            },
            "false_updated": {
                "current_geometry_ewkb": geometry(),
            },
            "false_unchanged": {
                "operation": "unchanged",
            },
            "endpoint": {
                "current_geometry_ewkb": geometry(((1, 1.1), (2, 2), (3, 3))),
            },
            "count": {
                "current_geometry_ewkb": geometry(((1, 1), (3, 3))),
            },
            "hidden": {
                "visible": False,
            },
            "hidden_unchanged": {
                "visible": False,
                "operation": "unchanged",
            },
            "corrupt": {
                "current_geometry_ewkb": "bad",
            },
            "multiple": {},
        }[case]
        row.draft_feature_pairs = (
            replace(
                pair,
                **changes,
            ),
        )
        if case == "multiple":
            row.draft_feature_pairs += (
                replace(
                    pair,
                    feature_id=uuid4(),
                ),
            )
    with pytest.raises(ValueError):
        project_workspace_draft(row)


@pytest.mark.parametrize(
    "kind,points,feature_type",
    [("Point", ((1, 1),), "junction"), ("LineString", ((1, 1), (2, 2)), "line")],
)
def test_unchanged_points_and_short_lines_are_not_edit_candidates(
    kind,
    points,
    feature_type,
):
    row = draft()
    ewkb = geometry(
        points,
        kind,
    )
    row.draft_feature_pairs = (
        replace(
            row.draft_feature_pairs[0],
            current_feature_type=feature_type,
            baseline_feature_type=feature_type,
            current_geometry_ewkb=ewkb,
            baseline_geometry_ewkb=ewkb,
        ),
    )
    assert project_workspace_draft(row).has_persisted_change_set is False


def test_signed_zero_does_not_create_diff():
    row = draft()
    row.draft_feature_pairs = (
        replace(
            row.draft_feature_pairs[0],
            current_geometry_ewkb=geometry(((0, 1), (2, 2), (3, 3))),
            baseline_geometry_ewkb=geometry((("-0.0", 1), (2, 2), (3, 3))),
        ),
    )
    assert project_workspace_draft(row).has_persisted_change_set is False
