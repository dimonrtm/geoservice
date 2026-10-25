"""Live HTTP smoke phases; no scenario writes through the SQL observer."""

from __future__ import annotations

import json
import base64
import os
import re
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from urllib.request import urlopen
from uuid import UUID, uuid4

from tests.smoke.full_path_workspace_smoke import (
    SmokeFailure,
    assert_workspace,
    load_assigned_work_order,
    open_edit_version,
    load_workspace,
    login,
    request_json_response,
)
from tests.smoke.save_geometry_observer import snapshot_save_state


VALIDATION = {
    "geometryStatus": "passed",
    "aoiStatus": "passed",
    "positionalAccuracyStatus": "POSITIONAL_ACCURACY_UNVERIFIED",
    "dirtyRelativeToBaseline": "passed",
}


class SmokeCheckFailure(SmokeFailure):
    """Harness-authored assertion text, safe to include in evidence."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeCheckFailure(message)


def authenticated_subject(token: str) -> str:
    # The API authenticates the token; this only correlates its subject with SQL evidence.
    try:
        payload = token.split(".")[1]
        return str(
            UUID(json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))["sub"])
        )
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise SmokeFailure("Login JWT не содержит actor UUID") from exc


def write_phase_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        temporary.write_bytes(
            (json.dumps(state, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode(
                "utf-8"
            )
        )
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def load_phase_state(path: Path, *, run_id: str) -> dict:
    try:
        UUID(run_id)
        state = json.loads(path.read_text(encoding="utf-8"))
        require(isinstance(state, dict), "State должен быть объектом")
        require(state["schemaVersion"] == 1, "Несовместимый state")
        require(state["runId"] == run_id, "Чужой runId")
        require(state["status"] == "save-complete", "Save не завершён или фаза уже выполнена")
        for name in ("work_order_id", "edit_version_id", "feature_id"):
            UUID(state["target"][name])
        UUID(state["originalRequest"]["commandId"])
        require(isinstance(state["originalRequest"]["draftVersionToken"], str), "Нет token")
        for name in (
            "originalRequest",
            "saveResponse",
            "savedWorkspace",
            "beforeSnapshot",
            "savedSnapshot",
        ):
            require(isinstance(state[name], dict) and bool(state[name]), f"Нет {name}")
        require(isinstance(state["originalRequest"]["geometry"], dict), "Нет geometry")
        before, saved, target = state["beforeSnapshot"], state["savedSnapshot"], state["target"]
        require(
            before["revision"] == 1 and before["commands"] == before["events"] == [],
            "State не от fresh run",
        )
        require(
            before["geometryBytes"] == before["baselineBytes"]
            and before["geometry"] == before["baseline"],
            "State baseline не совпадает",
        )
        require(
            all(before[key] == value for key, value in target.items()), "State target не совпадает"
        )
        require(state["originalRequest"]["draftVersionToken"] == "1", "Неверный исходный token")
        require(
            state["originalRequest"]["geometry"] == changed_geometry(before["baseline"]),
            "Неверная исходная geometry",
        )
        check_response(state["saveResponse"], state["originalRequest"], target, 2, True)
        check_workspace(state["savedWorkspace"], target, state["saveResponse"], before["baseline"])
        check_mutation(before, saved, target, state["saveResponse"])
        return state
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        raise SmokeFailure("Повреждён или отсутствует фазовый state") from error


def target_feature(workspace: dict, target: dict) -> dict:
    assert_workspace(
        workspace, work_order_id=target["work_order_id"], edit_version_id=target["edit_version_id"]
    )
    features = workspace["workOrder"]["editVersion"]["features"]["features"]
    found = [feature for feature in features if feature.get("id") == target["feature_id"]]
    require(len(found) == 1, "Target feature отсутствует или дублируется")
    return found[0]


def check_workspace(workspace: dict, target: dict, response: dict, baseline: dict) -> None:
    feature = target_feature(workspace, target)
    version = workspace["workOrder"]["editVersion"]
    require(
        feature["geometry"] == response["updatedFeature"]["geometry"],
        "Readback geometry не совпадает",
    )
    require(
        feature["properties"]["operation"] == response["operation"],
        "Readback operation не совпадает",
    )
    for key in ("draftVersionToken", "basicValidation", "hasPersistedChangeSet"):
        require(version[key] == response[key], f"Readback {key} не совпадает")
    expected = {
        "featureId": target["feature_id"],
        "vertexIndex": 1,
        "baselineGeometry": baseline,
        "operation": "updated",
    }
    require(
        version["changeSet"] == (expected if response["hasPersistedChangeSet"] else None),
        "Readback changeSet не совпадает",
    )


def check_response(
    payload: dict, command: dict, target: dict, revision: int, changed: bool
) -> None:
    expected = {
        "commandId": command["commandId"],
        "commandState": "succeeded",
        "draftVersionToken": str(revision),
        "operation": "updated" if changed else "unchanged",
        "hasPersistedChangeSet": changed,
        "updatedFeature": {"id": target["feature_id"], "geometry": command["geometry"]},
        "basicValidation": VALIDATION if changed else None,
    }
    require(payload == expected, "Save/Revert response не соответствует контракту")


def unchanged_except(before: dict, after: dict, *allowed: str) -> None:
    require(before.keys() == after.keys(), "SQL snapshot shape изменился")
    for key in before.keys() - set(allowed):
        require(before[key] == after[key], f"Неожиданная mutation: {key}")


def check_command(row: dict, target: dict, owner: str, command_id: str) -> None:
    for key in ("edit_version_id", "feature_id"):
        require(row[key] == target[key], f"Command {key} не совпадает")
    require(
        row["command_id"] == command_id and row["actor_user_id"] == owner,
        "Command identity не совпадает",
    )
    require(bool(row["request_fingerprint"]) and bool(row["completed_at"]), "Команда не terminal")
    require(row["retry_on_access_change"] is False, "Неожиданный access retry")


def added_command(before: dict, after: dict, target: dict, command_id: str) -> dict:
    old = {row["command_id"]: row for row in before["commands"]}
    new = {row["command_id"]: row for row in after["commands"]}
    require(
        len(after["commands"]) == len(old) + 1 and set(new) == set(old) | {command_id},
        "Неверное число/identity команд",
    )
    for key, value in old.items():
        require(new[key] == value, "Старая команда изменена")
    row = new[command_id]
    check_command(row, target, after["owner"], command_id)
    return row


def check_mutation(before: dict, after: dict, target: dict, response: dict, cleared=False) -> None:
    unchanged_except(
        before, after, "revision", "geometry", "geometryBytes", "operation", "commands", "events"
    )
    require(after["revision"] == before["revision"] + 1, "Неверный прирост revision")
    require(
        after["geometry"] == response["updatedFeature"]["geometry"],
        "SQL geometry не соответствует HTTP",
    )
    require(after["geometryBytes"] != before["geometryBytes"], "Mutation оказалась no-op")
    require(after["operation"] == response["operation"], "SQL operation не соответствует HTTP")
    row = added_command(before, after, target, response["commandId"])
    require(
        row["state"] == "succeeded"
        and row["response_status"] == 200
        and row["response_payload"] == response,
        "Terminal success не совпадает",
    )
    require(
        row["rejection_code"] is None and row["rejection_message"] is None,
        "Success содержит rejection",
    )
    require(
        len(after["events"]) == len(before["events"]) + 1
        and after["events"][:-1] == before["events"],
        "Append-only history нарушена",
    )
    event = after["events"][-1]
    expected = {
        **target,
        "command_id": response["commandId"],
        "actor_user_id": after["owner"],
        "default_state_id": after["default_state_id"],
        "draft_revision_before": before["revision"],
        "draft_revision_after": after["revision"],
        "beforeBytes": before["geometryBytes"],
        "afterBytes": after["geometryBytes"],
        "event_type": "change_set_cleared" if cleared else "change_set_persisted",
    }
    require(
        all(event.get(key) == value for key, value in expected.items()),
        "Event не соответствует mutation",
    )


def changed_geometry(baseline: dict, *, delta="0.001") -> dict:
    require(
        baseline.get("type") == "LineString" and len(baseline.get("coordinates", [])) == 3,
        "Ожидается трёхвершинная L-003",
    )
    geometry = deepcopy(baseline)
    require(all(len(point) == 2 for point in geometry["coordinates"]), "Ожидается XY")
    geometry["coordinates"][1][1] = float(
        Decimal(str(geometry["coordinates"][1][1])) + Decimal(delta)
    )
    return geometry


def geometry_path(target: dict) -> str:
    return f"/api/v1/work-orders/{target['work_order_id']}/edit-versions/{target['edit_version_id']}/features/{target['feature_id']}/geometry"


def evidence(path: Path, run_id: str, stage: str, **details) -> None:
    write_phase_state(
        path,
        {
            "runId": run_id,
            "stage": stage,
            "verifiedAt": datetime.now(timezone.utc).isoformat(),
            **details,
        },
    )


def put_success(config, token, target, command, *, opener, evidence_path, run_id, stage):
    evidence(
        evidence_path,
        run_id,
        stage,
        status="running",
        expectedStatus=200,
        commandId=command["commandId"],
    )
    status, result = request_json_response(
        config, "PUT", geometry_path(target), token=token, payload=command, opener=opener
    )
    evidence(
        evidence_path,
        run_id,
        stage,
        status="running",
        expectedStatus=200,
        actualStatus=status,
        commandId=command["commandId"],
    )
    require(status == 200, "Ожидается HTTP 200 для успешного PUT")
    return result


def run_save_phase(
    config, *, run_id, state_path, evidence_path, opener=urlopen, observer=snapshot_save_state
):
    require(not state_path.exists(), "State уже существует; нужен fresh run")
    UUID(run_id)
    evidence(evidence_path, run_id, "save-preflight", status="running")
    token = login(config, opener=opener)
    work_order = load_assigned_work_order(config, token, opener=opener)
    version_id = open_edit_version(config, token, work_order["id"], opener=opener)
    workspace = load_workspace(config, token, work_order["id"], version_id, opener=opener)
    version = workspace["workOrder"]["editVersion"]
    features = [
        f
        for f in version["features"]["features"]
        if f.get("properties", {}).get("assetCode") == "L-003"
    ]
    require(len(features) == 1, "Ожидается одна L-003")
    feature = features[0]
    target = {
        "work_order_id": work_order["id"],
        "edit_version_id": version_id,
        "feature_id": feature["id"],
    }
    for value in target.values():
        UUID(value)
    target_feature(workspace, target)
    before = observer(**target)
    require(all(before[key] == value for key, value in target.items()), "SQL target не совпадает")
    require(before["owner"] == authenticated_subject(token), "Owner не совпадает с actor")
    require(before["revision"] == 1 and version["draftVersionToken"] == "1", "Нужна fresh revision")
    require(before["commands"] == before["events"] == [], "Registry/history не пусты")
    require(
        before["geometryBytes"] == before["baselineBytes"] and before["operation"] == "unchanged",
        "Начальная geometry не baseline",
    )
    require(
        feature["geometry"] == before["baseline"] == before["geometry"],
        "Baseline/current расходятся",
    )
    require(
        version["hasPersistedChangeSet"] is False
        and version["changeSet"] is None
        and version["basicValidation"] is None,
        "Начальный workspace dirty",
    )
    command = {
        "commandId": str(uuid4()),
        "draftVersionToken": version["draftVersionToken"],
        "geometry": changed_geometry(feature["geometry"]),
    }
    evidence(
        evidence_path,
        run_id,
        "save-put",
        status="running",
        beforeSnapshot=before,
        originalRequest=command,
    )
    result = put_success(
        config,
        token,
        target,
        command,
        opener=opener,
        evidence_path=evidence_path,
        run_id=run_id,
        stage="save-put",
    )
    check_response(result, command, target, 2, True)
    saved_workspace = load_workspace(config, token, work_order["id"], version_id, opener=opener)
    check_workspace(saved_workspace, target, result, before["baseline"])
    saved = observer(**target)
    evidence(
        evidence_path,
        run_id,
        "save-sql",
        status="running",
        beforeSnapshot=before,
        savedSnapshot=saved,
    )
    check_mutation(before, saved, target, result)
    state = {
        "schemaVersion": 1,
        "runId": run_id,
        "status": "save-complete",
        "target": target,
        "originalRequest": command,
        "saveResponse": result,
        "savedWorkspace": saved_workspace,
        "beforeSnapshot": before,
        "savedSnapshot": saved,
    }
    write_phase_state(state_path, state)
    evidence(evidence_path, run_id, "save-complete", status="passed", state=state)


def run_verify_phase(
    config, *, run_id, state_path, evidence_path, opener=urlopen, observer=snapshot_save_state
):
    state = load_phase_state(state_path, run_id=run_id)
    target = state["target"]
    saved = state["savedSnapshot"]
    # A failed/interrupted verification must not be restarted as a fresh scenario.
    state["status"] = "verify-running"
    write_phase_state(state_path, state)
    evidence(evidence_path, run_id, "restart-readback", status="running", savedSnapshot=saved)
    token = login(config, opener=opener)
    require(saved["owner"] == authenticated_subject(token), "Actor после restart изменился")

    def readback():
        return load_workspace(
            config, token, target["work_order_id"], target["edit_version_id"], opener=opener
        )

    workspace = readback()
    check_workspace(workspace, target, state["saveResponse"], state["beforeSnapshot"]["baseline"])
    restarted = observer(**target)
    evidence(
        evidence_path,
        run_id,
        "restart-sql",
        status="running",
        expectedSnapshot=saved,
        actualSnapshot=restarted,
    )
    require(restarted == saved, "Persistence изменилась при restart")
    result = put_success(
        config,
        token,
        target,
        state["originalRequest"],
        opener=opener,
        evidence_path=evidence_path,
        run_id=run_id,
        stage="replay-put",
    )
    require(result == state["saveResponse"], "Replay не вернул исходный terminal result")
    check_workspace(readback(), target, result, state["beforeSnapshot"]["baseline"])
    after_replay = observer(**target)
    evidence(
        evidence_path,
        run_id,
        "replay-sql",
        status="running",
        expectedSnapshot=saved,
        actualSnapshot=after_replay,
    )
    require(after_replay == saved, "Replay изменил persistence")
    evidence(evidence_path, run_id, "replay-verified", status="running", afterReplay=after_replay)

    baseline = workspace["workOrder"]["editVersion"]["changeSet"]["baselineGeometry"]
    current_token = workspace["workOrder"]["editVersion"]["draftVersionToken"]
    invalid = deepcopy(baseline)
    invalid["coordinates"][1] = deepcopy(invalid["coordinates"][0])
    outside = deepcopy(baseline)
    aoi = workspace["workOrder"]["scope"]["aoi"]["geometry"]
    require(aoi["type"] == "Polygon", "Smoke ожидает Polygon AOI")
    outside["coordinates"][1][1] = float(
        max(Decimal(str(p[1])) for ring in aoi["coordinates"] for p in ring) + Decimal("0.01")
    )
    cases = [
        (
            "DRAFT_VERSION_STALE",
            409,
            changed_geometry(baseline),
            state["originalRequest"]["draftVersionToken"],
        ),
        ("COMMAND_ID_REUSED", 409, changed_geometry(baseline, delta="0.002"), current_token),
        ("GEOMETRY_INVALID", 422, invalid, current_token),
        ("GEOMETRY_OUTSIDE_AOI", 422, outside, current_token),
    ]
    previous = saved
    rejections = []
    for code, expected_status, geometry, version_token in cases:
        command = {
            "commandId": (
                state["originalRequest"]["commandId"]
                if code == "COMMAND_ID_REUSED"
                else str(uuid4())
            ),
            "draftVersionToken": version_token,
            "geometry": geometry,
        }
        evidence(
            evidence_path,
            run_id,
            code,
            status="running",
            expectedStatus=expected_status,
            expectedCode=code,
            commandId=command["commandId"],
            rejections=rejections,
        )
        status, error = request_json_response(
            config, "PUT", geometry_path(target), token=token, payload=command, opener=opener
        )
        actual_code = error.get("code")
        if not isinstance(actual_code, str) or not re.fullmatch(
            r"[A-Z][A-Z0-9_]{0,79}", actual_code
        ):
            actual_code = "<invalid-code>"
        outcome = {
            "expectedStatus": expected_status,
            "actualStatus": status,
            "expectedCode": code,
            "actualCode": actual_code,
            "commandId": command["commandId"],
            "rejections": rejections,
        }
        evidence(evidence_path, run_id, code, status="running", **outcome)
        require(
            status == expected_status
            and set(error) == {"code", "message", "correlationId"}
            and error["code"] == code,
            f"Неверный HTTP отказ: {code}",
        )
        require(
            isinstance(error["message"], str) and bool(error["message"].strip()),
            "Отказ без message",
        )
        try:
            UUID(error["correlationId"])
        except (ValueError, TypeError, AttributeError) as exc:
            raise SmokeFailure("Отказ без correlation UUID") from exc
        after = observer(**target)
        evidence(
            evidence_path,
            run_id,
            code,
            status="running",
            expectedSnapshot=previous,
            actualSnapshot=after,
            **outcome,
        )
        unchanged_except(previous, after, "commands")
        if code == "COMMAND_ID_REUSED":
            require(after == previous, "Reused CommandId изменил registry")
        else:
            row = added_command(previous, after, target, command["commandId"])
            require(
                row["state"] == "rejected"
                and row["response_payload"] is None
                and row["rejection_code"] == code
                and row["response_status"] == expected_status
                and row["rejection_message"] == error["message"],
                "Terminal rejection не совпадает",
            )
        rejections.append(
            {"code": code, "status": status, "commandId": command["commandId"], "snapshot": after}
        )
        previous = after
        evidence(
            evidence_path,
            run_id,
            code,
            status="running",
            afterReplay=after_replay,
            rejections=rejections,
        )

    command = {"commandId": str(uuid4()), "draftVersionToken": current_token, "geometry": baseline}
    result = put_success(
        config,
        token,
        target,
        command,
        opener=opener,
        evidence_path=evidence_path,
        run_id=run_id,
        stage="revert-put",
    )
    check_response(result, command, target, previous["revision"] + 1, False)
    check_workspace(readback(), target, result, baseline)
    final = observer(**target)
    evidence(
        evidence_path,
        run_id,
        "revert-sql",
        status="running",
        beforeSnapshot=previous,
        finalSnapshot=final,
    )
    check_mutation(previous, final, target, result, cleared=True)
    require(
        final["geometryBytes"]
        == final["baselineBytes"]
        == state["beforeSnapshot"]["baselineBytes"],
        "Revert/baseline bytes не совпадают",
    )
    require(
        final["revision"] == 3 and len(final["commands"]) == 5 and len(final["events"]) == 2,
        "Итоговые counters не совпадают",
    )
    state["status"] = "complete"
    write_phase_state(state_path, state)
    evidence(
        evidence_path,
        run_id,
        "complete",
        status="passed",
        afterReplay=after_replay,
        rejections=rejections,
        finalSnapshot=final,
    )
