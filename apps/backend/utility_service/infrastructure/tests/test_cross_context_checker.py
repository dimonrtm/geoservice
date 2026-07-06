from __future__ import annotations

import asyncio
from datetime import date, datetime, time, timezone
from decimal import Decimal
import importlib
import json
import re
from uuid import uuid4

import pytest
from sqlalchemy import text

from utility_service.infrastructure.postgresql.consistency.cross_context_checker import (
    CrossContextConsistencyChecker,
    UnknownCrossContextConsistencyCheckError,
)
from utility_service.infrastructure.postgresql.consistency.cross_context_checks import (
    ALL_CROSS_CONTEXT_CHECKS,
    DEFAULT_CROSS_CONTEXT_CHECKS,
)
from utility_service.infrastructure.postgresql.consistency.contracts import (
    CrossContextConsistencyCheck,
)


class FakeMappingResult:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows

    def all(self) -> list[dict]:
        return self.rows


class FakeResult:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows

    def mappings(self) -> FakeMappingResult:
        return FakeMappingResult(self.rows)


class FakeSession:
    def __init__(self, rows_by_call: list[list[dict]]) -> None:
        self.rows_by_call = list(rows_by_call)
        self.execute_calls: list[tuple[object, dict]] = []

    async def execute(self, statement, params):  # type: ignore[no-untyped-def]
        self.execute_calls.append((statement, params))
        return FakeResult(self.rows_by_call.pop(0))


def sample_check(name: str = "sample_check") -> CrossContextConsistencyCheck:
    return CrossContextConsistencyCheck(
        name=name,
        severity="error",
        message="Sample check failed.",
        source="source.table.source_id",
        target="target.table.id",
        sql=text("select 1"),
        sample_fields={
            "source_id": "sourceId",
            "target_id": "targetId",
        },
        sample_limit=5,
    )


def test_clean_check_result_builds_ok_report() -> None:
    checked_at = datetime(2026, 7, 6, 10, 0, tzinfo=timezone.utc)
    session = FakeSession(rows_by_call=[[]])
    check = sample_check()

    report = asyncio.run(
        CrossContextConsistencyChecker(
            session,
            checks=[check],
            clock=lambda: checked_at,
        ).run()
    )

    assert report.ok is True
    assert report.checked_at == checked_at
    assert report.checks_run == 1
    assert report.error_count == 0
    assert report.warning_count == 0
    assert report.issues == []
    assert session.execute_calls == [(check.sql, {"sample_limit": 5})]


def test_rows_build_issue_with_count_and_human_readable_sample_rows() -> None:
    source_id = uuid4()
    target_id = uuid4()
    second_source_id = uuid4()
    second_target_id = uuid4()
    session = FakeSession(
        rows_by_call=[
            [
                {
                    "issue_count": 2,
                    "source_id": source_id,
                    "target_id": target_id,
                },
                {
                    "issue_count": 2,
                    "source_id": second_source_id,
                    "target_id": second_target_id,
                },
            ]
        ]
    )

    report = asyncio.run(
        CrossContextConsistencyChecker(
            session,
            checks=[sample_check()],
        ).run()
    )

    assert report.ok is False
    assert report.error_count == 1
    assert report.warning_count == 0
    assert len(report.issues) == 1
    issue = report.issues[0]
    assert issue.check_name == "sample_check"
    assert issue.severity == "error"
    assert issue.message == "Sample check failed."
    assert issue.source == "source.table.source_id"
    assert issue.target == "target.table.id"
    assert issue.count == 2
    assert issue.sample_rows == [
        {
            "sourceId": str(source_id),
            "targetId": str(target_id),
        },
        {
            "sourceId": str(second_source_id),
            "targetId": str(second_target_id),
        },
    ]


def test_subset_run_executes_only_named_checks() -> None:
    first = sample_check("first_check")
    second = sample_check("second_check")
    session = FakeSession(rows_by_call=[[]])

    report = asyncio.run(
        CrossContextConsistencyChecker(
            session,
            checks=[first, second],
        ).run(["second_check"])
    )

    assert report.ok is True
    assert report.checks_run == 1
    assert session.execute_calls == [(second.sql, {"sample_limit": 5})]


def test_subset_run_preserves_registry_order_for_requested_names() -> None:
    first = sample_check("first_check")
    second = sample_check("second_check")
    session = FakeSession(rows_by_call=[[], []])

    report = asyncio.run(
        CrossContextConsistencyChecker(
            session,
            checks=[first, second],
        ).run(["second_check", "first_check"])
    )

    assert report.ok is True
    assert report.checks_run == 2
    assert session.execute_calls == [
        (first.sql, {"sample_limit": 5}),
        (second.sql, {"sample_limit": 5}),
    ]


def test_unknown_subset_check_name_fails_with_known_names() -> None:
    checker = CrossContextConsistencyChecker(
        FakeSession(rows_by_call=[]),
        checks=[sample_check("known_check")],
    )

    with pytest.raises(
        UnknownCrossContextConsistencyCheckError,
        match=(
            "Неизвестные проверки согласованности cross-context: "
            "missing_check. Известные проверки: known_check"
        ),
    ):
        asyncio.run(checker.run(["missing_check"]))


def test_duplicate_check_names_fail_fast() -> None:
    with pytest.raises(
        ValueError,
        match="Повторяющиеся имена проверок согласованности cross-context: duplicate_check",
    ):
        CrossContextConsistencyChecker(
            FakeSession(rows_by_call=[]),
            checks=[
                sample_check("duplicate_check"),
                sample_check("duplicate_check"),
            ],
        )


def test_check_rejects_sample_limit_less_than_one() -> None:
    with pytest.raises(
        ValueError,
        match="sample_limit должен быть больше или равен 1",
    ):
        CrossContextConsistencyCheck(
            name="sample_check",
            severity="error",
            message="Sample check failed.",
            source="source.table.source_id",
            target="target.table.id",
            sql=text("select 1"),
            sample_fields={
                "source_id": "sourceId",
            },
            sample_limit=0,
        )


def test_sample_rows_serialize_jsonable_values_recursively() -> None:
    source_id = uuid4()
    mapping_key_id = uuid4()
    created_at = datetime(2026, 7, 6, 10, 30, tzinfo=timezone.utc)
    work_date = date(2026, 7, 7)
    window_start = time(8, 15)
    raw_bytes = b"bad-\xff"
    check = CrossContextConsistencyCheck(
        name="sample_check",
        severity="error",
        message="Sample check failed.",
        source="source.table.source_id",
        target="target.table.id",
        sql=text("select 1"),
        sample_fields={
            "payload": "payload",
        },
    )
    session = FakeSession(
        rows_by_call=[
            [
                {
                    "issue_count": 1,
                    "payload": {
                        "source_id": source_id,
                        "created_at": created_at,
                        "work_date": work_date,
                        "window_start": window_start,
                        "cost": Decimal("12.50"),
                        "nested": [
                            (source_id, Decimal("1.25")),
                            {"labels": {"primary", "secondary"}},
                        ],
                        mapping_key_id: {
                            b"bytes-key": bytearray(b"stable-bytearray"),
                        },
                        "plain": "stable",
                        "raw": raw_bytes,
                    },
                }
            ]
        ]
    )

    report = asyncio.run(
        CrossContextConsistencyChecker(
            session,
            checks=[check],
        ).run()
    )

    json.dumps(report.issues[0].sample_rows)
    assert report.issues[0].sample_rows == [
        {
            "payload": {
                "source_id": str(source_id),
                "created_at": created_at.isoformat(),
                "work_date": work_date.isoformat(),
                "window_start": window_start.isoformat(),
                "cost": "12.50",
                "nested": [
                    [str(source_id), "1.25"],
                    {"labels": ["primary", "secondary"]},
                ],
                str(mapping_key_id): {
                    "bytes-key": "stable-bytearray",
                },
                "plain": "stable",
                "raw": raw_bytes.decode("utf-8", errors="replace"),
            }
        }
    ]


def test_default_cross_context_check_registry_contains_first_increment_contract() -> None:
    check_names = [check.name for check in ALL_CROSS_CONTEXT_CHECKS]

    assert check_names == [
        "work_order_assignee_user_exists",
        "work_order_created_by_user_exists",
        "default_state_work_order_exists",
        "edit_version_owner_user_exists",
        "edit_version_default_state_exists",
        "edit_version_default_state_matches_work_order",
    ]
    assert DEFAULT_CROSS_CONTEXT_CHECKS is ALL_CROSS_CONTEXT_CHECKS
    assert {check.severity for check in ALL_CROSS_CONTEXT_CHECKS} == {"error"}
    assert all(check.sample_limit == 10 for check in ALL_CROSS_CONTEXT_CHECKS)


def test_cross_context_check_registry_sql_contract_is_static_read_only_selects() -> None:
    for check in ALL_CROSS_CONTEXT_CHECKS:
        sql = check.sql.text.lower()
        selected_aliases = set(re.findall(r"\bas\s+([a-z_][a-z0-9_]*)", sql))

        assert sql.lstrip().startswith("select"), check.name
        assert not re.search(r"\b(insert|update|delete|merge|truncate|drop|alter|create)\b", sql)
        assert "issue_count" in selected_aliases
        assert "limit :sample_limit" in sql
        assert set(check.sample_fields).issubset(selected_aliases)


def test_consistency_package_public_exports_include_all_checks_registry() -> None:
    consistency_package = importlib.import_module(
        "utility_service.infrastructure.postgresql.consistency"
    )

    assert consistency_package.ALL_CROSS_CONTEXT_CHECKS is ALL_CROSS_CONTEXT_CHECKS
    assert "ALL_CROSS_CONTEXT_CHECKS" in consistency_package.__all__
