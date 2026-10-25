from io import BytesIO
from copy import deepcopy
from importlib import import_module, util
import json
import base64
from uuid import uuid4
from urllib.error import HTTPError

import pytest

from tests.smoke import full_path_workspace_smoke as base
from tests.smoke.test_full_path_workspace_smoke import workspace_payload, FakeResponse


VERSION = "00000000-0000-4000-8000-000000000001"
FEATURE = "00000000-0000-4000-8000-000000000002"
ACTOR = "00000000-0000-4000-8000-000000000003"
RUN = "00000000-0000-4000-8000-000000000004"
TOKEN = (
    "header."
    + base64.urlsafe_b64encode(json.dumps({"sub": ACTOR}).encode()).decode().rstrip("=")
    + ".signature"
)
BASELINE = {
    "type": "LineString",
    "coordinates": [[65.52, 44.82], [65.525, 44.8205], [65.53, 44.82]],
}
MOVED = {"type": "LineString", "coordinates": [[65.52, 44.82], [65.525, 44.8215], [65.53, 44.82]]}
VALIDATION = {
    "geometryStatus": "passed",
    "aoiStatus": "passed",
    "positionalAccuracyStatus": "POSITIONAL_ACCURACY_UNVERIFIED",
    "dirtyRelativeToBaseline": "passed",
}


def command_id(number):
    return f"10000000-0000-4000-8000-{number:012d}"


def response(number, revision, changed=True):
    return {
        "commandId": command_id(number),
        "commandState": "succeeded",
        "draftVersionToken": str(revision),
        "operation": "updated" if changed else "unchanged",
        "hasPersistedChangeSet": changed,
        "updatedFeature": {"id": FEATURE, "geometry": deepcopy(MOVED if changed else BASELINE)},
        "basicValidation": deepcopy(VALIDATION) if changed else None,
    }


def workspace(revision, changed=False):
    result = workspace_payload(work_order_id=base.EXPECTED_WORK_ORDER_ID, edit_version_id=VERSION)
    version = result["workOrder"]["editVersion"]
    version.update(
        {
            "draftVersionToken": str(revision),
            "hasPersistedChangeSet": changed,
            "basicValidation": deepcopy(VALIDATION) if changed else None,
            "changeSet": (
                {
                    "featureId": FEATURE,
                    "vertexIndex": 1,
                    "baselineGeometry": deepcopy(BASELINE),
                    "operation": "updated",
                }
                if changed
                else None
            ),
        }
    )
    version["features"]["features"][0] = {
        "id": FEATURE,
        "geometry": deepcopy(MOVED if changed else BASELINE),
        "properties": {"assetCode": "L-003", "operation": "updated" if changed else "unchanged"},
    }
    result["workOrder"]["scope"]["aoi"]["geometry"] = {
        "type": "Polygon",
        "coordinates": [
            [
                [65.495, 44.795],
                [65.545, 44.795],
                [65.545, 44.835],
                [65.495, 44.835],
                [65.495, 44.795],
            ]
        ],
    }
    return result


def initial_snapshot():
    return {
        "work_order_id": base.EXPECTED_WORK_ORDER_ID,
        "edit_version_id": VERSION,
        "feature_id": FEATURE,
        "default_state_id": "00000000-0000-4000-8000-000000000005",
        "owner": ACTOR,
        "revision": 1,
        "geometry": deepcopy(BASELINE),
        "geometryBytes": "00",
        "baseline": deepcopy(BASELINE),
        "baselineBytes": "00",
        "operation": "unchanged",
        "commands": [],
        "events": [],
    }


def terminal(number, payload=None, code=None):
    return {
        "command_id": command_id(number),
        "edit_version_id": VERSION,
        "feature_id": FEATURE,
        "actor_user_id": ACTOR,
        "request_fingerprint": "test-fingerprint",
        "state": "rejected" if code else "succeeded",
        "response_payload": payload,
        "response_status": (409 if code == "DRAFT_VERSION_STALE" else 422) if code else 200,
        "rejection_code": code,
        "rejection_message": "Отклонено" if code else None,
        "completed_at": "2026-10-25T00:00:00Z",
        "retry_on_access_change": False,
    }


def event(number, revision, cleared=False):
    return {
        "command_id": command_id(number),
        "edit_version_id": VERSION,
        "feature_id": FEATURE,
        "work_order_id": base.EXPECTED_WORK_ORDER_ID,
        "actor_user_id": ACTOR,
        "default_state_id": initial_snapshot()["default_state_id"],
        "draft_revision_before": revision - 1,
        "draft_revision_after": revision,
        "event_type": "change_set_cleared" if cleared else "change_set_persisted",
        "beforeBytes": "01" if cleared else "00",
        "afterBytes": "00" if cleared else "01",
    }


class ScriptedRuntime:
    def __init__(self, replies, snapshots):
        self.replies = replies
        self.snapshots = snapshots
        self.puts = []

    def opener(self, request, timeout):
        method, status, payload = self.replies.pop(0)
        assert request.get_method() == method
        if method == "PUT":
            assert request.full_url.endswith(f"/{VERSION}/features/{FEATURE}/geometry")
            self.puts.append(json.loads(request.data))
        result = FakeResponse(deepcopy(payload))
        result.status = status
        return result

    def observer(self, **target):
        assert target == {
            "work_order_id": base.EXPECTED_WORK_ORDER_ID,
            "edit_version_id": VERSION,
            "feature_id": FEATURE,
        }
        return deepcopy(self.snapshots.pop(0))


def save_runtime():
    before = initial_snapshot()
    saved = deepcopy(before)
    saved.update(
        revision=2,
        geometry=deepcopy(MOVED),
        geometryBytes="01",
        operation="updated",
        commands=[terminal(1, response(1, 2))],
        events=[event(1, 2)],
    )
    return ScriptedRuntime(
        [
            ("POST", 200, {"access_token": TOKEN}),
            ("GET", 200, {"workOrders": [{"id": base.EXPECTED_WORK_ORDER_ID, "code": "WO-001"}]}),
            (
                "POST",
                200,
                {"editVersion": {"id": VERSION, "workOrderId": base.EXPECTED_WORK_ORDER_ID}},
            ),
            ("GET", 200, workspace(1)),
            ("PUT", 200, response(1, 2)),
            ("GET", 200, workspace(2, True)),
        ],
        [before, saved],
    )


def run_save(tmp_path, monkeypatch, runtime=None):
    module = phase_module()
    monkeypatch.setattr(module, "uuid4", lambda: command_id(1), raising=False)
    runtime = runtime or save_runtime()
    module.run_save_phase(
        base.SmokeConfig("http://test", "editor", "secret"),
        run_id=RUN,
        state_path=tmp_path / "state.json",
        evidence_path=tmp_path / "evidence.json",
        opener=runtime.opener,
        observer=runtime.observer,
    )
    return runtime


def phase_module():
    name = "tests.smoke.save_geometry_smoke"
    assert util.find_spec(name) is not None, "Отсутствует фазовый smoke"
    return import_module(name)


def test_expected_http_error_can_be_inspected_without_losing_status():
    def opener(request, timeout):
        raise HTTPError(
            request.full_url,
            409,
            "Conflict",
            {},
            BytesIO(b'{"code":"DRAFT_VERSION_STALE","message":"stale","correlationId":"id"}'),
        )

    assert hasattr(base, "request_json_response")
    status, payload = base.request_json_response(
        base.SmokeConfig("http://test", "editor", "secret"),
        "PUT",
        "/geometry",
        payload={},
        opener=opener,
    )
    assert status == 409
    assert payload["code"] == "DRAFT_VERSION_STALE"
    with pytest.raises(base.SmokeFailure, match="409"):
        base.request_json(
            base.SmokeConfig("http://test", "editor", "secret"),
            "PUT",
            "/geometry",
            payload={},
            opener=opener,
        )


@pytest.mark.parametrize("body", [b"broken json", b"[]"])
def test_error_json_must_be_an_object(body):
    def opener(request, timeout):
        raise HTTPError(request.full_url, 422, "Invalid", {}, BytesIO(body))

    assert hasattr(base, "request_json_response")
    with pytest.raises(base.SmokeFailure):
        base.request_json_response(
            base.SmokeConfig("http://test", "editor", "secret"),
            "PUT",
            "/geometry",
            opener=opener,
        )


@pytest.mark.parametrize(
    "value",
    [None, [], {}, {"schemaVersion": 2}, {"schemaVersion": 1, "status": "complete"}],
)
def test_invalid_phase_state_prevents_network_requests(tmp_path, value):
    module = phase_module()
    path = tmp_path / "state.json"
    path.write_text(json.dumps(value), encoding="utf-8")

    def unexpected(*args, **kwargs):
        pytest.fail("Invalid state reached network/observer")

    with pytest.raises(base.SmokeFailure):
        module.run_verify_phase(
            base.SmokeConfig("http://test", "editor", "secret"),
            run_id=str(uuid4()),
            state_path=path,
            evidence_path=tmp_path / "evidence.json",
            opener=unexpected,
            observer=unexpected,
        )


def test_atomic_state_write_keeps_previous_file_on_replace_failure(tmp_path, monkeypatch):
    module = phase_module()
    path = tmp_path / "state.json"
    path.write_text('{"old": true}', encoding="utf-8")

    def fail(*args):
        raise OSError("write failure")

    monkeypatch.setattr(module.os, "replace", fail)
    with pytest.raises(OSError):
        module.write_phase_state(path, {"new": True})
    assert json.loads(path.read_text()) == {"old": True}


def test_existing_save_state_prevents_new_mutation(tmp_path):
    module = phase_module()
    path = tmp_path / "state.json"
    path.write_text("{}", encoding="utf-8")

    def unexpected(*args, **kwargs):
        pytest.fail("Existing state reached network")

    with pytest.raises(base.SmokeFailure):
        module.run_save_phase(
            base.SmokeConfig("http://test", "editor", "secret"),
            run_id=str(uuid4()),
            state_path=path,
            evidence_path=tmp_path / "evidence.json",
            opener=unexpected,
            observer=unexpected,
        )


def test_save_persists_only_verified_phase_state(tmp_path, monkeypatch):
    runtime = run_save(tmp_path, monkeypatch)
    state = phase_module().load_phase_state(tmp_path / "state.json", run_id=RUN)
    assert state["originalRequest"] == {
        "commandId": command_id(1),
        "draftVersionToken": "1",
        "geometry": MOVED,
    }
    assert state["savedSnapshot"]["revision"] == 2
    assert not runtime.replies and not runtime.snapshots


@pytest.mark.parametrize("fault", ["baseline", "event", "noop", "readback", "dirty"])
def test_save_refuses_unproven_success(tmp_path, monkeypatch, fault):
    runtime = save_runtime()
    if fault == "baseline":
        runtime.snapshots[-1]["baselineBytes"] = "ff"
    elif fault == "event":
        runtime.snapshots[-1]["events"] = []
    elif fault == "noop":
        runtime.replies[-2][2]["updatedFeature"]["geometry"] = deepcopy(BASELINE)
    elif fault == "readback":
        runtime.replies[-1][2]["workOrder"]["editVersion"]["draftVersionToken"] = "3"
    else:
        runtime.replies[3][2]["workOrder"]["editVersion"]["hasPersistedChangeSet"] = True
    with pytest.raises(base.SmokeFailure):
        run_save(tmp_path, monkeypatch, runtime)
    assert not (tmp_path / "state.json").exists()


def verify_runtime(state):
    saved = deepcopy(state["savedSnapshot"])
    stale = deepcopy(saved)
    stale["commands"].append(terminal(2, code="DRAFT_VERSION_STALE"))
    invalid = deepcopy(stale)
    invalid["commands"].append(terminal(3, code="GEOMETRY_INVALID"))
    outside = deepcopy(invalid)
    outside["commands"].append(terminal(4, code="GEOMETRY_OUTSIDE_AOI"))
    final = deepcopy(outside)
    final.update(revision=3, geometry=deepcopy(BASELINE), geometryBytes="00", operation="unchanged")
    final["commands"].append(terminal(5, response(5, 3, False)))
    final["events"].append(event(5, 3, True))
    replies = [
        ("POST", 200, {"access_token": TOKEN}),
        ("GET", 200, workspace(2, True)),
        ("PUT", 200, response(1, 2)),
        ("GET", 200, workspace(2, True)),
    ]
    for status, code in [
        (409, "DRAFT_VERSION_STALE"),
        (409, "COMMAND_ID_REUSED"),
        (422, "GEOMETRY_INVALID"),
        (422, "GEOMETRY_OUTSIDE_AOI"),
    ]:
        replies.append(
            ("PUT", status, {"code": code, "message": "Отклонено", "correlationId": RUN})
        )
    replies += [("PUT", 200, response(5, 3, False)), ("GET", 200, workspace(3))]
    return ScriptedRuntime(replies, [saved, saved, stale, stale, invalid, outside, final])


def run_verify(tmp_path, monkeypatch, runtime):
    module = phase_module()
    ids = iter(command_id(n) for n in range(2, 6))
    monkeypatch.setattr(module, "uuid4", lambda: next(ids))
    module.run_verify_phase(
        base.SmokeConfig("http://test", "editor", "secret"),
        run_id=RUN,
        state_path=tmp_path / "state.json",
        evidence_path=tmp_path / "evidence.json",
        opener=runtime.opener,
        observer=runtime.observer,
    )


def test_verify_replays_exact_request_then_reverts_readback_baseline(tmp_path, monkeypatch):
    run_save(tmp_path, monkeypatch)
    state = json.loads((tmp_path / "state.json").read_text())
    runtime = verify_runtime(state)
    run_verify(tmp_path, monkeypatch, runtime)
    assert runtime.puts[0] == state["originalRequest"]
    assert runtime.puts[-1]["geometry"] == BASELINE
    assert len(runtime.puts) == 6  # replay, four rejections, Revert
    assert len({p["commandId"] for p in runtime.puts}) == 5
    assert not runtime.replies and not runtime.snapshots
    result = json.loads((tmp_path / "evidence.json").read_text())
    assert result["status"] == "passed"
    assert result["finalSnapshot"]["revision"] == 3
    assert len(result["finalSnapshot"]["events"]) == 2
    assert json.loads((tmp_path / "state.json").read_text())["status"] == "complete"


@pytest.mark.parametrize(
    "fault",
    [
        "replay_event",
        "replay_token",
        "wrong_code",
        "reused_row",
        "rejection_geometry",
        "uncleared",
        "final_baseline",
    ],
)
def test_verify_detects_false_success(tmp_path, monkeypatch, fault):
    run_save(tmp_path, monkeypatch)
    state = json.loads((tmp_path / "state.json").read_text())
    runtime = verify_runtime(state)
    if fault == "replay_event":
        runtime.snapshots[1] = deepcopy(runtime.snapshots[1])
        runtime.snapshots[1]["events"].append(event(9, 3))
    elif fault == "replay_token":
        runtime.replies[2][2]["draftVersionToken"] = "9"
    elif fault == "wrong_code":
        runtime.replies[6][2]["code"] = "GEOMETRY_STRUCTURE_CHANGED"
    elif fault == "reused_row":
        runtime.snapshots[3] = deepcopy(runtime.snapshots[3])
        runtime.snapshots[3]["commands"][0]["request_fingerprint"] = "changed"
    elif fault == "rejection_geometry":
        runtime.snapshots[4]["geometryBytes"] = "ff"
    elif fault == "uncleared":
        runtime.replies[-1][2]["workOrder"]["editVersion"]["hasPersistedChangeSet"] = True
    else:
        runtime.snapshots[-1]["baselineBytes"] = "ff"
    with pytest.raises(base.SmokeFailure):
        run_verify(tmp_path, monkeypatch, runtime)
    assert json.loads((tmp_path / "state.json").read_text())["status"] != "complete"


@pytest.mark.parametrize(
    "fault", ["run", "geometry", "target", "response", "snapshot", "completed"]
)
def test_corrupt_saved_state_rejected_before_http(tmp_path, monkeypatch, fault):
    run_save(tmp_path, monkeypatch)
    path = tmp_path / "state.json"
    state = json.loads(path.read_text())
    if fault == "run":
        state["runId"] = str(uuid4())
    elif fault == "geometry":
        state["originalRequest"]["geometry"] = {}
    elif fault == "target":
        state["target"]["feature_id"] = ACTOR
    elif fault == "response":
        state["saveResponse"]["commandId"] = ACTOR
    elif fault == "snapshot":
        state["savedSnapshot"].pop("events")
    else:
        state["status"] = "complete"
    path.write_text(json.dumps(state), encoding="utf-8")
    runtime = ScriptedRuntime([], [])
    with pytest.raises(base.SmokeFailure):
        run_verify(tmp_path, monkeypatch, runtime)


def test_cli_bad_state_returns_failure_evidence(tmp_path):
    assert "argv" in __import__("inspect").signature(base.main).parameters
    result = base.main(
        [
            "--phase",
            "verify-retry-revert",
            "--run-id",
            RUN,
            "--state-file",
            str(tmp_path / "missing.json"),
            "--evidence-file",
            str(tmp_path / "result.json"),
        ]
    )
    assert result == 1
    evidence = json.loads((tmp_path / "result.json").read_text())
    assert evidence["status"] == "failed"
    assert "secret" not in json.dumps(evidence)


@pytest.mark.parametrize("phase", ["save", "replay", "revert"])
def test_successful_put_requires_exact_http_200(tmp_path, monkeypatch, phase):
    if phase == "save":
        runtime = save_runtime()
        method, _, payload = runtime.replies[-2]
        runtime.replies[-2] = (method, 202, payload)
        with pytest.raises(base.SmokeFailure, match="200"):
            run_save(tmp_path, monkeypatch, runtime)
    else:
        run_save(tmp_path, monkeypatch)
        state = json.loads((tmp_path / "state.json").read_text())
        runtime = verify_runtime(state)
        index = 2 if phase == "replay" else -2
        method, _, payload = runtime.replies[index]
        runtime.replies[index] = (method, 201, payload)
        with pytest.raises(base.SmokeFailure, match="200"):
            run_verify(tmp_path, monkeypatch, runtime)


def test_cli_failure_evidence_identifies_current_case_and_actual_outcome(tmp_path, monkeypatch):
    run_save(tmp_path, monkeypatch)
    state = json.loads((tmp_path / "state.json").read_text())
    runtime = verify_runtime(state)
    runtime.replies[6] = (
        "PUT",
        400,
        {"code": "BAD_REQUEST", "message": "do-not-log-secret", "correlationId": RUN},
    )
    module = phase_module()
    original = module.run_verify_phase
    ids = iter(command_id(n) for n in range(2, 6))
    monkeypatch.setattr(module, "uuid4", lambda: next(ids))
    monkeypatch.setattr(
        module,
        "run_verify_phase",
        lambda config, **kwargs: original(
            config, opener=runtime.opener, observer=runtime.observer, **kwargs
        ),
    )
    result = base.main(
        [
            "--phase",
            "verify-retry-revert",
            "--run-id",
            RUN,
            "--state-file",
            str(tmp_path / "state.json"),
            "--evidence-file",
            str(tmp_path / "failure.json"),
        ]
    )
    assert result == 1
    saved = json.loads((tmp_path / "failure.json").read_text())
    assert saved["stage"] == "GEOMETRY_INVALID"
    assert saved["expectedStatus"] == 422
    assert saved["actualStatus"] == 400
    assert saved["actualCode"] == "BAD_REQUEST"
    assert saved["reason"] == "Неверный HTTP отказ: GEOMETRY_INVALID"
    assert "do-not-log-secret" not in json.dumps(saved)
