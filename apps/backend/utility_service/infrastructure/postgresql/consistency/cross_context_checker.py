from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence, Set
from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.consistency.contracts import (
    CrossContextConsistencyCheck,
    CrossContextConsistencyIssue,
    CrossContextConsistencyReport,
)
from utility_service.infrastructure.postgresql.consistency.cross_context_checks import (
    ALL_CROSS_CONTEXT_CHECKS,
)


class UnknownCrossContextConsistencyCheckError(ValueError):
    """Raised when a caller asks for a check name that is not registered."""


class CrossContextConsistencyChecker:
    def __init__(
        self,
        session: AsyncSession,
        *,
        checks: Sequence[CrossContextConsistencyCheck] = ALL_CROSS_CONTEXT_CHECKS,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.session = session
        self._checks = list(checks)
        duplicate_names = self._duplicate_check_names(self._checks)
        if duplicate_names:
            duplicate_names_text = ", ".join(duplicate_names)
            raise ValueError(
                "Повторяющиеся имена проверок согласованности cross-context: "
                f"{duplicate_names_text}"
            )
        self._checks_by_name = {check.name: check for check in self._checks}
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    async def run(
        self,
        check_names: Sequence[str] | None = None,
    ) -> CrossContextConsistencyReport:
        selected_checks = self._select_checks(check_names)
        issues: list[CrossContextConsistencyIssue] = []

        for check in selected_checks:
            issue = await self._run_check(check)
            if issue is not None:
                issues.append(issue)

        error_count = sum(1 for issue in issues if issue.severity == "error")
        warning_count = sum(1 for issue in issues if issue.severity == "warning")

        return CrossContextConsistencyReport(
            ok=error_count == 0,
            checked_at=self._clock(),
            checks_run=len(selected_checks),
            error_count=error_count,
            warning_count=warning_count,
            issues=issues,
        )

    def _select_checks(
        self,
        check_names: Sequence[str] | None,
    ) -> list[CrossContextConsistencyCheck]:
        if check_names is None:
            return list(self._checks)

        unknown_names = [name for name in check_names if name not in self._checks_by_name]
        if unknown_names:
            known_names = ", ".join(sorted(self._checks_by_name))
            missing_names = ", ".join(unknown_names)
            raise UnknownCrossContextConsistencyCheckError(
                "Неизвестные проверки согласованности cross-context: "
                f"{missing_names}. Известные проверки: {known_names}"
            )

        requested_names = set(check_names)
        return [check for check in self._checks if check.name in requested_names]

    def _duplicate_check_names(
        self,
        checks: Sequence[CrossContextConsistencyCheck],
    ) -> list[str]:
        seen_names: set[str] = set()
        duplicate_names: list[str] = []

        for check in checks:
            if check.name in seen_names and check.name not in duplicate_names:
                duplicate_names.append(check.name)
            seen_names.add(check.name)

        return duplicate_names

    async def _run_check(
        self,
        check: CrossContextConsistencyCheck,
    ) -> CrossContextConsistencyIssue | None:
        result = await self.session.execute(
            check.sql,
            {"sample_limit": check.sample_limit},
        )
        rows = list(result.mappings().all())
        if not rows:
            return None

        return CrossContextConsistencyIssue(
            check_name=check.name,
            severity=check.severity,
            message=check.message,
            source=check.source,
            target=check.target,
            count=int(rows[0]["issue_count"]),
            sample_rows=[self._sample_row(check, row) for row in rows],
        )

    def _sample_row(
        self,
        check: CrossContextConsistencyCheck,
        row: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            output_name: self._jsonable_value(row[input_name])
            for input_name, output_name in check.sample_fields.items()
        }

    def _jsonable_value(self, value: Any) -> Any:
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, time):
            return value.isoformat()
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, (bytes, bytearray)):
            return bytes(value).decode("utf-8", errors="replace")
        if isinstance(value, Mapping):
            return {
                self._jsonable_mapping_key(key): self._jsonable_value(nested_value)
                for key, nested_value in value.items()
            }
        if isinstance(value, Set):
            return sorted(
                (self._jsonable_value(nested_value) for nested_value in value),
                key=repr,
            )
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return [self._jsonable_value(nested_value) for nested_value in value]
        return value

    def _jsonable_mapping_key(self, value: Any) -> str | int | float | bool | None:
        jsonable_key = self._jsonable_value(value)
        if jsonable_key is None or isinstance(jsonable_key, (str, int, float, bool)):
            return jsonable_key
        return str(jsonable_key)
