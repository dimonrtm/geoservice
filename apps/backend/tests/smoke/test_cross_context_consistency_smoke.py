from __future__ import annotations

from datetime import datetime, timezone

import pytest

from tests.smoke.cross_context_consistency_smoke import (
    exit_code_for_report,
    format_report,
    main,
)
from utility_service.infrastructure.postgresql.consistency import (
    CrossContextConsistencyIssue,
    CrossContextConsistencyReport,
)


def report_with_issues(
    issues: list[CrossContextConsistencyIssue],
) -> CrossContextConsistencyReport:
    error_count = len([issue for issue in issues if issue.severity == "error"])
    return CrossContextConsistencyReport(
        ok=error_count == 0,
        checked_at=datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc),
        checks_run=6,
        error_count=error_count,
        warning_count=len([issue for issue in issues if issue.severity == "warning"]),
        issues=issues,
    )


def failed_report() -> CrossContextConsistencyReport:
    return report_with_issues(
        [
            CrossContextConsistencyIssue(
                check_name="edit_version_default_state_matches_work_order",
                severity="error",
                message="EditVersion default_state_id указывает на DefaultState другого WorkOrder.",
                source="work_order.edit_versions.default_state_id",
                target="utility_network.default_states.id",
                count=1,
                sample_rows=[
                    {
                        "editVersionId": "edit-version-1",
                        "editVersionWorkOrderId": "work-order-1",
                        "defaultStateId": "default-state-2",
                        "defaultStateWorkOrderId": "work-order-2",
                    }
                ],
            )
        ]
    )


def test_format_report_outputs_success_summary() -> None:
    report = report_with_issues([])

    assert exit_code_for_report(report) == 0
    assert format_report(report) == "Cross-context consistency: OK\nchecks=6\n"


def test_format_report_outputs_failed_issue_samples() -> None:
    report = failed_report()

    assert exit_code_for_report(report) == 1
    assert format_report(report) == (
        "Cross-context consistency: FAILED\n"
        "\n"
        "ERROR edit_version_default_state_matches_work_order\n"
        "message: EditVersion default_state_id указывает на DefaultState другого WorkOrder.\n"
        "source: work_order.edit_versions.default_state_id\n"
        "target: utility_network.default_states.id\n"
        "count: 1\n"
        "sample:\n"
        "  editVersionId=edit-version-1 "
        "editVersionWorkOrderId=work-order-1 "
        "defaultStateId=default-state-2 "
        "defaultStateWorkOrderId=work-order-2\n"
    )


def test_format_report_outputs_warning_issue_details_with_ok_exit_code() -> None:
    report = report_with_issues(
        [
            CrossContextConsistencyIssue(
                check_name="legacy_warning_check",
                severity="warning",
                message="Legacy reference is unusual.",
                source="source.table.legacy_id",
                target=None,
                count=1,
                sample_rows=[
                    {
                        "legacyId": "legacy-1",
                    }
                ],
            )
        ]
    )

    assert report.ok is True
    assert exit_code_for_report(report) == 0
    assert format_report(report) == (
        "Cross-context consistency: OK\n"
        "\n"
        "WARNING legacy_warning_check\n"
        "message: Legacy reference is unusual.\n"
        "source: source.table.legacy_id\n"
        "target: None\n"
        "count: 1\n"
        "sample:\n"
        "  legacyId=legacy-1\n"
    )


def test_format_report_preserves_issue_and_sample_row_order() -> None:
    report = report_with_issues(
        [
            CrossContextConsistencyIssue(
                check_name="first_check",
                severity="warning",
                message="First check warning.",
                source="source.first_id",
                target="target.first_id",
                count=2,
                sample_rows=[
                    {
                        "firstId": "first-1",
                        "targetId": "target-1",
                    },
                    {
                        "firstId": "first-2",
                        "targetId": "target-2",
                    },
                ],
            ),
            CrossContextConsistencyIssue(
                check_name="second_check",
                severity="error",
                message="Second check error.",
                source="source.second_id",
                target="target.second_id",
                count=1,
                sample_rows=[
                    {
                        "secondId": "second-1",
                        "targetId": "target-3",
                    }
                ],
            ),
        ]
    )

    assert exit_code_for_report(report) == 1
    assert format_report(report) == (
        "Cross-context consistency: FAILED\n"
        "\n"
        "WARNING first_check\n"
        "message: First check warning.\n"
        "source: source.first_id\n"
        "target: target.first_id\n"
        "count: 2\n"
        "sample:\n"
        "  firstId=first-1 targetId=target-1\n"
        "  firstId=first-2 targetId=target-2\n"
        "\n"
        "ERROR second_check\n"
        "message: Second check error.\n"
        "source: source.second_id\n"
        "target: target.second_id\n"
        "count: 1\n"
        "sample:\n"
        "  secondId=second-1 targetId=target-3\n"
    )


def test_main_prints_ok_report_to_stdout(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    async def fake_load_report() -> CrossContextConsistencyReport:
        return report_with_issues([])

    monkeypatch.setattr(
        "tests.smoke.cross_context_consistency_smoke.load_report",
        fake_load_report,
    )

    assert main() == 0
    captured = capsys.readouterr()
    assert captured.out == "Cross-context consistency: OK\nchecks=6\n"
    assert captured.err == ""


def test_main_prints_failed_report_to_stderr(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    async def fake_load_report() -> CrossContextConsistencyReport:
        return failed_report()

    monkeypatch.setattr(
        "tests.smoke.cross_context_consistency_smoke.load_report",
        fake_load_report,
    )

    assert main() == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("Cross-context consistency: FAILED\n")
    assert "ERROR edit_version_default_state_matches_work_order\n" in captured.err


def test_main_prints_runner_errors_to_stderr(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    async def fake_load_report() -> CrossContextConsistencyReport:
        raise RuntimeError("database down")

    monkeypatch.setattr(
        "tests.smoke.cross_context_consistency_smoke.load_report",
        fake_load_report,
    )

    assert main() == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith(
        "Cross-context consistency check failed to run. See traceback for operational context.\n"
    )
    assert "Traceback (most recent call last):\n" in captured.err
    assert "RuntimeError: database down\n" in captured.err
