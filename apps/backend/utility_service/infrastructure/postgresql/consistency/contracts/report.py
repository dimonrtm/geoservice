from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from utility_service.infrastructure.postgresql.consistency.contracts.check import Severity


@dataclass(frozen=True)
class CrossContextConsistencyIssue:
    check_name: str
    severity: Severity
    message: str
    source: str
    target: str | None
    count: int
    sample_rows: list[dict[str, Any]]


@dataclass(frozen=True)
class CrossContextConsistencyReport:
    ok: bool
    checked_at: datetime
    checks_run: int
    error_count: int
    warning_count: int
    issues: list[CrossContextConsistencyIssue]
