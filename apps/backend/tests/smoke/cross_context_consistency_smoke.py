from __future__ import annotations

import asyncio
import sys
import traceback
from pathlib import Path
from typing import TYPE_CHECKING

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

if TYPE_CHECKING:
    from utility_service.infrastructure.postgresql.consistency import (
        CrossContextConsistencyReport,
    )


def format_report(report: CrossContextConsistencyReport) -> str:
    if not report.issues:
        return f"Cross-context consistency: OK\nchecks={report.checks_run}\n"

    status = "OK" if report.ok else "FAILED"
    lines = [f"Cross-context consistency: {status}", ""]
    for issue in report.issues:
        lines.extend(
            [
                f"{issue.severity.upper()} {issue.check_name}",
                f"message: {issue.message}",
                f"source: {issue.source}",
                f"target: {issue.target}",
                f"count: {issue.count}",
                "sample:",
            ]
        )
        for sample_row in issue.sample_rows:
            values = " ".join(f"{key}={value}" for key, value in sample_row.items())
            lines.append(f"  {values}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def exit_code_for_report(report: CrossContextConsistencyReport) -> int:
    return 0 if report.ok else 1


async def load_report() -> CrossContextConsistencyReport:
    from utility_service.infrastructure.postgresql.consistency import (
        CrossContextConsistencyChecker,
    )
    from utility_service.infrastructure.postgresql.session import SessionFactory

    async with SessionFactory() as session:
        return await CrossContextConsistencyChecker(session).run()


def main() -> int:
    try:
        report = asyncio.run(load_report())
    except Exception:
        print(
            "Cross-context consistency check failed to run. "
            "See traceback for operational context.",
            file=sys.stderr,
        )
        traceback.print_exc(file=sys.stderr)
        return 1

    stream = sys.stdout if report.ok else sys.stderr
    print(format_report(report), end="", file=stream)
    return exit_code_for_report(report)


if __name__ == "__main__":
    raise SystemExit(main())
