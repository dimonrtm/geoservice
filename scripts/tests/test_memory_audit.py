import importlib.util
import sys
import unittest
from datetime import date
from pathlib import Path


def load_module():
    module_path = Path(__file__).resolve().parents[1] / "memory_audit.py"
    spec = importlib.util.spec_from_file_location("memory_audit", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


memory_audit = load_module()


class MemoryAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp_parent = Path.cwd() / ".tmp-tests"
        self.tmp_parent.mkdir(exist_ok=True)
        self.root = self.tmp_parent / self._testMethodName
        self.root.mkdir(exist_ok=True)

    def write(self, relative_path: str, text: str) -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def memory_entry(
        self,
        relative_path: str,
        *,
        entry_date: str = "2026-06-01",
        entry_type: str = "session",
        tags: str = "example",
        related: tuple[str, ...] = (),
        summary: str = "Уникальное проверяемое знание для будущей работы.",
    ) -> Path:
        related_lines = "\n".join(f"- `{path}`" for path in related) or "- none"
        return self.write(
            relative_path,
            f"""# Example

Date: {entry_date}
Type: {entry_type}
Tags: {tags}
Related files:

{related_lines}

## Summary

{summary}

## Context

Контекст.

## Actions

- Действие.

## Verification

Проверка.

## Retrieval Hints

example
""",
        )

    def test_reports_broken_related_file(self):
        self.memory_entry(
            "docs/agent-memory/sessions/example.md",
            related=("docs/missing.md",),
        )

        report = memory_audit.audit(self.root, today=date(2026, 6, 13))

        self.assertFinding(
            report,
            "broken_reference",
            "docs/agent-memory/sessions/example.md",
        )

    def test_reports_broken_superseded_by_reference(self):
        path = self.memory_entry(
            "docs/agent-memory/decisions/example.md",
            entry_type="decision",
        )
        path.write_text(
            path.read_text(encoding="utf-8")
            + "\nSuperseded by: docs/agent-memory/decisions/missing.md\n",
            encoding="utf-8",
        )

        report = memory_audit.audit(self.root, today=date(2026, 6, 13))

        self.assertFinding(
            report,
            "broken_reference",
            "docs/agent-memory/decisions/example.md",
        )

    def test_accepts_existing_backticked_superseded_by_reference(self):
        self.memory_entry(
            "docs/agent-memory/decisions/current.md",
            entry_type="decision",
        )
        path = self.memory_entry(
            "docs/agent-memory/decisions/old.md",
            entry_type="decision",
        )
        path.write_text(
            path.read_text(encoding="utf-8")
            + ("\nSuperseded by: " "`docs/agent-memory/decisions/current.md`\n"),
            encoding="utf-8",
        )

        report = memory_audit.audit(self.root, today=date(2026, 6, 13))

        broken_paths = {
            finding.path.as_posix()
            for finding in report.findings
            if finding.code == "broken_reference"
        }
        self.assertNotIn(
            "docs/agent-memory/decisions/old.md",
            broken_paths,
        )

    def test_reports_broken_file_map_reference(self):
        self.write(
            "docs/agent-memory/file-map.md",
            "- missing topic: `docs/missing.md`\n",
        )

        report = memory_audit.audit(self.root, today=date(2026, 6, 13))

        self.assertFinding(
            report,
            "broken_reference",
            "docs/agent-memory/file-map.md",
        )

    def test_old_decision_is_not_candidate_by_age_alone(self):
        self.memory_entry(
            "docs/agent-memory/decisions/example.md",
            entry_date="2025-01-01",
            entry_type="decision",
        )

        report = memory_audit.audit(self.root, today=date(2026, 6, 13))

        self.assertNotIn(
            "aged_session",
            {finding.code for finding in report.findings},
        )

    def test_marks_old_session_for_review(self):
        self.memory_entry(
            "docs/agent-memory/sessions/old.md",
            entry_date="2026-03-14",
        )

        report = memory_audit.audit(self.root, today=date(2026, 6, 13))

        self.assertFinding(
            report,
            "aged_session",
            "docs/agent-memory/sessions/old.md",
        )

    def test_marks_sync_session_for_replacement_by_canonical_source(self):
        self.write("docs/superpowers/plans/example.md", "# Plan\n")
        self.memory_entry(
            "docs/agent-memory/sessions/2026-06-01-sync-vision-example.md",
            tags="sync-vision, wiki",
            related=("docs/superpowers/plans/example.md",),
        )

        report = memory_audit.audit(self.root, today=date(2026, 6, 13))

        finding = self.findFinding(
            report,
            "noisy_session",
            "docs/agent-memory/sessions/2026-06-01-sync-vision-example.md",
        )
        self.assertEqual("replace-reference", finding.recommendation)

    def test_marks_session_that_repeats_canonical_plan(self):
        self.write("docs/superpowers/plans/example.md", "# Plan\n")
        self.memory_entry(
            "docs/agent-memory/sessions/example.md",
            related=("docs/superpowers/plans/example.md",),
        )

        report = memory_audit.audit(self.root, today=date(2026, 6, 13))

        finding = self.findFinding(
            report,
            "canonical_source_session",
            "docs/agent-memory/sessions/example.md",
        )
        self.assertEqual("replace-reference", finding.recommendation)

    def test_marks_session_that_repeats_sprint_plan(self):
        self.write("docs/sprint_1/example.md", "# Plan\n")
        self.memory_entry(
            "docs/agent-memory/sessions/example.md",
            related=("docs/sprint_1/example.md",),
        )

        report = memory_audit.audit(self.root, today=date(2026, 6, 13))

        finding = self.findFinding(
            report,
            "canonical_source_session",
            "docs/agent-memory/sessions/example.md",
        )
        self.assertEqual("replace-reference", finding.recommendation)

    def test_marks_exact_duplicate_summary_for_merge(self):
        summary = (
            "Одинаковое устойчивое знание достаточной длины, "
            "которое не должно храниться в двух активных записях."
        )
        self.memory_entry(
            "docs/agent-memory/sessions/a.md",
            summary=summary,
        )
        self.memory_entry(
            "docs/agent-memory/sessions/b.md",
            summary=summary,
        )

        report = memory_audit.audit(self.root, today=date(2026, 6, 13))

        self.assertFinding(
            report,
            "duplicate_summary",
            "docs/agent-memory/sessions/b.md",
        )

    def test_warns_when_session_budget_is_exceeded(self):
        for index in range(memory_audit.SESSION_BUDGET + 1):
            self.memory_entry(
                f"docs/agent-memory/sessions/{index:02d}.md",
                summary=f"Уникальное знание номер {index}.",
            )

        report = memory_audit.audit(self.root, today=date(2026, 6, 13))

        self.assertFinding(
            report,
            "session_budget_exceeded",
            "docs/agent-memory/sessions",
        )

    def test_warns_when_registry_budget_is_exceeded(self):
        self.write(
            "Code_wiki/состояние_проекта/repository_change_ingest.md",
            "\n".join(["legacy"] * (memory_audit.REGISTRY_MAX_LINES + 1)),
        )

        report = memory_audit.audit(self.root, today=date(2026, 6, 13))

        self.assertFinding(
            report,
            "registry_budget_exceeded",
            "Code_wiki/состояние_проекта/repository_change_ingest.md",
        )

    def test_reports_each_legacy_registry_heading(self):
        self.write(
            "Code_wiki/состояние_проекта/repository_change_ingest.md",
            """# Registry

## Исторические Записи, Ожидающие Ревизии

### 2026-06-01 - Первая задача

Описание.

### 2026-06-02 - Вторая задача

Описание.
""",
        )

        report = memory_audit.audit(self.root, today=date(2026, 6, 13))

        legacy = [
            finding
            for finding in report.findings
            if finding.code == "legacy_registry_entry"
        ]
        self.assertEqual(2, len(legacy))

    def test_reports_project_state_history_fields(self):
        self.write(
            "memory/project-state.md",
            """# State

## Состояние Pipeline

- Последний repository-change ingest: завершена задача.

## Изменения С Прошлого `/sync-vision`

- Завершённая история.
""",
        )

        report = memory_audit.audit(self.root, today=date(2026, 6, 13))

        self.assertFinding(
            report,
            "project_state_history",
            "memory/project-state.md",
        )

    def test_markdown_output_is_deterministic_and_audit_is_read_only(self):
        self.memory_entry("docs/agent-memory/sessions/example.md")
        before = {
            path.relative_to(self.root): path.read_bytes()
            for path in self.root.rglob("*")
            if path.is_file()
        }

        first = memory_audit.format_markdown(
            memory_audit.audit(self.root, today=date(2026, 6, 13))
        )
        second = memory_audit.format_markdown(
            memory_audit.audit(self.root, today=date(2026, 6, 13))
        )
        after = {
            path.relative_to(self.root): path.read_bytes()
            for path in self.root.rglob("*")
            if path.is_file()
        }

        self.assertEqual(first, second)
        self.assertEqual(before, after)

    def findFinding(self, report, code: str, relative_path: str):
        matches = [
            finding
            for finding in report.findings
            if finding.code == code and finding.path.as_posix() == relative_path
        ]
        self.assertTrue(matches, f"Missing {code} for {relative_path}: {report}")
        return matches[0]

    def assertFinding(self, report, code: str, relative_path: str):
        self.findFinding(report, code, relative_path)


if __name__ == "__main__":
    unittest.main()
