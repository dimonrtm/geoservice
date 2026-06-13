# Оптимизация Памяти И Базы Знаний Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Перевести agent memory и `repository-change` ingest с хронологического логирования на хранение уникального долговременного знания и добавить read-only аудит кандидатов на очистку.

**Architecture:** Правила хранения остаются в Markdown и repo-local skills. Автоматизация состоит из небольшого import-friendly модуля `scripts/memory_audit.py`, тонкого CLI `scripts/audit-memory.py` и существующего staged-files guard `scripts/check-memory-needed.py`; аудит только читает репозиторий, детерминированно классифицирует кандидатов и никогда не удаляет файлы. Текущий подробный `repository_change_ingest.md` получает компактный табличный реестр для новых записей, а старые блоки временно сохраняются как legacy до отдельного пользовательского подтверждения.

**Tech Stack:** Python 3 standard library, `unittest`, Markdown, PowerShell, repo-local skills.

---

## Scope И Этапы

Этот plan реализует новые правила, tooling, компактный формат новых
repository-change записей и формирует разовый отчёт по существующему шуму.

Удаление, объединение или сокращение существующих 35 session-файлов и 19
legacy repository-change блоков не входит в этот plan. После Task 7 выполнение
останавливается для пользовательского подтверждения конкретных кандидатов.
Подтверждённая очистка получает отдельный короткий implementation plan.

## Файловая Структура

### Новые файлы

- `scripts/memory_audit.py` — чистая логика чтения memory entries, поиска
  ссылок, классификации кандидатов и форматирования отчёта.
- `scripts/audit-memory.py` — CLI с `--root`, `--today` и `--format`.
- `scripts/tests/test_memory_audit.py` — fixture-based unit tests без изменения
  реального репозитория.
- `.agents/skills/source-command-audit-memory/SKILL.md` — ручная процедура
  `/audit-memory`.

### Изменяемые файлы

- `scripts/check-memory-needed.py` — убрать автоматический trigger для обычных
  specs/plans и оставить operating-rule paths.
- `scripts/tests/test_check_memory_needed.py` — зафиксировать новую матрицу
  trigger/no-trigger.
- `AGENTS.md` — обновить критерии memory write, weekly workflow и
  repository-change gate.
- `docs/agent-memory/protocol.md` — сделать уникальность знания и
  retrieval-сценарий обязательными.
- `docs/agent-memory/README.md` — обозначить `sessions/` как исключение.
- `docs/agent-memory/file-map.md` — добавить audit tooling и убрать
  хронологические session-ссылки, если они не являются навигацией.
- `docs/agent-memory/decisions/2026-05-30-agent-memory-operating-rules.md` —
  обновить действующее решение и связать implementation plan.
- `docs/agent-memory/decisions/2026-05-30-agent-driven-repository-change-ingest.md`
  — пометить старый trigger как superseded.
- `.agents/skills/source-command-ingest/SKILL.md` — требовать конкретную
  `Code_wiki` ноду и новое устойчивое знание до ingest.
- `.agents/skills/source-command-lint-wiki/SKILL.md` — отделить wiki lint от
  memory audit.
- `.agents/skills/source-command-sync-vision/SKILL.md` — хранить в
  `project-state` только живое состояние.
- `docs/knowledge-pipeline/README.md` — описать weekly audit и новый gate.
- `scripts/README.md` — документировать команды аудита.
- `Code_wiki/состояние_проекта/repository_change_ingest.md` — добавить
  компактный активный реестр, сохранив legacy блоки до подтверждения.
- `Code_wiki/состояние_проекта/_info.md` и `Code_wiki/index.md` — заменить
  формулировки «журнал задач» на «реестр изменений нод».
- `Code_wiki/сборка/ci_and_quality.md` и
  `Code_wiki/правила_и_стиль/testing_strategy.md` — добавить memory audit в
  локальные quality checks.
- `memory/project-state.md` — убрать требование хранить последний
  repository-change как хронику; оставить только актуальный pipeline status.

## Принятые Технические Пороги

- `SESSION_BUDGET = 20`.
- `STALE_SESSION_DAYS = 90`.
- `REGISTRY_MAX_LINES = 200`.
- `REGISTRY_MAX_BYTES = 24 * 1024`.

Пороги создают warnings/candidates, но не удаляют данные и не делают CLI
неуспешным. Ненулевой exit code используется только для неверных аргументов
или невозможности прочитать корень репозитория.

### Task 1: Сузить Trigger `check-memory-needed.py`

**Files:**
- Modify: `scripts/tests/test_check_memory_needed.py`
- Modify: `scripts/check-memory-needed.py`

- [ ] **Step 1: Заменить tests новой матрицей поведения**

В `scripts/tests/test_check_memory_needed.py` заменить три текущих test methods
следующими:

```python
    def test_does_not_require_memory_for_regular_plan_or_spec(self):
        checker = load_module()

        for path in (
            "docs/superpowers/plans/example.md",
            "docs/superpowers/specs/example.md",
        ):
            with self.subTest(path=path):
                self.assertFalse(checker.needs_memory_update([path], []))

    def test_requires_memory_for_agent_and_pipeline_rules(self):
        checker = load_module()

        for path in (
            "AGENTS.md",
            "CONTRIBUTING.md",
            "docs/knowledge-pipeline/README.md",
            ".agents/skills/source-command-ingest/SKILL.md",
        ):
            with self.subTest(path=path):
                self.assertTrue(checker.needs_memory_update([path], []))

    def test_protocol_change_is_itself_a_memory_update(self):
        checker = load_module()

        self.assertFalse(
            checker.needs_memory_update(
                ["docs/agent-memory/protocol.md"],
                ["docs/agent-memory/protocol.md"],
            )
        )

    def test_allows_operating_rule_change_with_memory(self):
        checker = load_module()

        self.assertFalse(
            checker.needs_memory_update(
                ["AGENTS.md"],
                ["docs/agent-memory/decisions/operating-rules.md"],
            )
        )

    def test_ignores_regular_code_changes(self):
        checker = load_module()

        self.assertFalse(checker.needs_memory_update(["apps/backend/app/main.py"], []))
```

- [ ] **Step 2: Запустить test и подтвердить старое поведение**

Run:

```powershell
$python = 'C:\Users\dimon\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $python -m unittest scripts.tests.test_check_memory_needed -v
```

Expected: FAIL на
`test_does_not_require_memory_for_regular_plan_or_spec`, потому что текущий
`DURABLE_PREFIXES` включает `docs/superpowers/plans/` и
`docs/superpowers/specs/`.

- [ ] **Step 3: Заменить широкие durable prefixes на operating-rule paths**

В `scripts/check-memory-needed.py` заменить `DURABLE_PREFIXES` и
`is_durable_path()`:

```python
OPERATING_RULE_PATHS = {
    "AGENTS.md",
    "CONTRIBUTING.md",
    "docs/agent-memory/protocol.md",
    "docs/agent-memory/README.md",
}
OPERATING_RULE_PREFIXES = (
    "docs/knowledge-pipeline/",
    ".agents/skills/source-command-",
)
MEMORY_PREFIX = "docs/agent-memory/"


def is_durable_path(path: str) -> bool:
    normalized = normalize(path)
    return normalized in OPERATING_RULE_PATHS or any(
        normalized.startswith(prefix) for prefix in OPERATING_RULE_PREFIXES
    )
```

Изменить module docstring:

```python
"""Warn when staged operating-rule changes are missing durable memory context."""
```

Изменить warning text в `main()`:

```python
        print(
            "Operating memory or knowledge-pipeline rules are staged "
            "without docs/agent-memory updates."
        )
        print(
            "Update an existing durable memory entry, create one only if it "
            "adds unique knowledge, or document why the rule is self-contained."
        )
```

- [ ] **Step 4: Запустить targeted и полный scripts test suite**

Run:

```powershell
& $python -m unittest scripts.tests.test_check_memory_needed -v
& $python -m unittest discover -s scripts\tests -v
```

Expected: все tests проходят; текущий baseline до добавления audit tests —
`8 tests OK`.

### Task 2: Добавить Парсер И Структурные Findings Memory Audit

**Files:**
- Create: `scripts/memory_audit.py`
- Create: `scripts/tests/test_memory_audit.py`

- [ ] **Step 1: Создать fixture helpers и failing tests структурного аудита**

Создать `scripts/tests/test_memory_audit.py`:

```python
import sys
import unittest
from datetime import date
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import memory_audit


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

    def assertFinding(self, report, code: str, relative_path: str):
        matches = [
            finding
            for finding in report.findings
            if finding.code == code
            and finding.path.as_posix() == relative_path
        ]
        self.assertTrue(matches, f"Missing {code} for {relative_path}: {report}")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Запустить tests и подтвердить отсутствие модуля**

Run:

```powershell
& $python -m unittest scripts.tests.test_memory_audit -v
```

Expected: ERROR `ModuleNotFoundError: No module named 'memory_audit'`.

- [ ] **Step 3: Создать data model, parser и broken-reference checks**

Создать `scripts/memory_audit.py`:

```python
"""Read-only audit for repo-local agent memory and repository-change history."""

from __future__ import annotations

import dataclasses
import re
from collections import defaultdict
from datetime import date
from pathlib import Path


MEMORY_DIRS = ("sessions", "decisions", "patterns", "bugfixes")
SESSION_BUDGET = 20
STALE_SESSION_DAYS = 90
REGISTRY_MAX_LINES = 200
REGISTRY_MAX_BYTES = 24 * 1024
REGISTRY_PATH = Path(
    "Code_wiki/состояние_проекта/repository_change_ingest.md"
)
FIELD_RE = re.compile(r"^(Date|Type|Tags):\s*(.+)$", re.MULTILINE)
BACKTICK_PATH_RE = re.compile(r"`([^`\n]+)`")
SUPERSEDED_RE = re.compile(r"^Superseded by:\s*(\S+)\s*$", re.MULTILINE)
LEGACY_HEADING_RE = re.compile(r"^###\s+(.+)$", re.MULTILINE)


@dataclasses.dataclass(frozen=True)
class MemoryEntry:
    path: Path
    entry_date: date | None
    entry_type: str
    tags: tuple[str, ...]
    related_files: tuple[str, ...]
    summary: str
    text: str


@dataclasses.dataclass(frozen=True)
class Finding:
    code: str
    path: Path
    message: str
    recommendation: str


@dataclasses.dataclass(frozen=True)
class AuditReport:
    entries: tuple[MemoryEntry, ...]
    findings: tuple[Finding, ...]


def audit(root: Path | str, *, today: date | None = None) -> AuditReport:
    root = Path(root).resolve()
    today = today or date.today()
    entries = tuple(read_entries(root))
    findings: list[Finding] = []
    findings.extend(find_broken_references(root, entries))
    findings.extend(find_file_map_broken_references(root))
    findings.extend(find_age_candidates(entries, today))
    findings.extend(find_noise_candidates(entries))
    findings.extend(find_duplicate_summaries(entries))
    findings.extend(find_budget_warnings(root, entries))
    findings.extend(find_legacy_registry_entries(root))
    findings.extend(find_project_state_history(root))
    return AuditReport(
        entries=entries,
        findings=tuple(
            sorted(
                findings,
                key=lambda item: (
                    item.path.as_posix(),
                    item.code,
                    item.message,
                ),
            )
        ),
    )


def read_entries(root: Path) -> list[MemoryEntry]:
    entries: list[MemoryEntry] = []
    base = root / "docs" / "agent-memory"
    for directory in MEMORY_DIRS:
        entry_dir = base / directory
        if not entry_dir.exists():
            continue
        for path in sorted(entry_dir.glob("*.md")):
            entries.append(parse_entry(root, path))
    return entries


def parse_entry(root: Path, path: Path) -> MemoryEntry:
    text = path.read_text(encoding="utf-8")
    fields = {name: value.strip() for name, value in FIELD_RE.findall(text)}
    raw_date = fields.get("Date")
    try:
        entry_date = date.fromisoformat(raw_date) if raw_date else None
    except ValueError:
        entry_date = None
    tags = tuple(
        item.strip()
        for item in fields.get("Tags", "").split(",")
        if item.strip()
    )
    related_section = section_body(text, "Related files:", level=None)
    related_files = tuple(
        value
        for value in BACKTICK_PATH_RE.findall(related_section)
        if looks_like_repo_path(value)
    )
    return MemoryEntry(
        path=path.relative_to(root),
        entry_date=entry_date,
        entry_type=fields.get("Type", "").strip().lower(),
        tags=tags,
        related_files=related_files,
        summary=normalize_text(section_body(text, "Summary", level=2)),
        text=text,
    )


def section_body(text: str, heading: str, *, level: int | None) -> str:
    marker = heading if level is None else f"{'#' * level} {heading}"
    start = text.find(marker)
    if start == -1:
        return ""
    body_start = start + len(marker)
    next_heading = re.search(r"^##\s+", text[body_start:], re.MULTILINE)
    if next_heading is None:
        return text[body_start:]
    return text[body_start : body_start + next_heading.start()]


def normalize_text(value: str) -> str:
    return " ".join(value.lower().split())


def looks_like_repo_path(value: str) -> bool:
    normalized = value.replace("\\", "/")
    return (
        ("/" in normalized or Path(normalized).suffix in {".md", ".py", ".yml", ".yaml"})
        and not normalized.startswith(("http://", "https://"))
        and re.match(r"^[A-Za-z]:/", normalized) is None
        and "*" not in normalized
        and not normalized.startswith("<")
    )


def reference_exists(root: Path, value: str) -> bool:
    normalized = value.replace("\\", "/").split("#", 1)[0].strip()
    return bool(normalized) and (root / normalized).exists()


def find_broken_references(
    root: Path, entries: tuple[MemoryEntry, ...]
) -> list[Finding]:
    findings: list[Finding] = []
    for entry in entries:
        references = list(entry.related_files)
        references.extend(SUPERSEDED_RE.findall(entry.text))
        for reference in sorted(set(references)):
            if looks_like_repo_path(reference) and not reference_exists(root, reference):
                findings.append(
                    Finding(
                        code="broken_reference",
                        path=entry.path,
                        message=f"Не найдена ссылка: {reference}",
                        recommendation="replace-reference",
                    )
                )
    return findings


def find_file_map_broken_references(root: Path) -> list[Finding]:
    relative = Path("docs/agent-memory/file-map.md")
    path = root / relative
    if not path.exists():
        return []
    findings: list[Finding] = []
    references = BACKTICK_PATH_RE.findall(path.read_text(encoding="utf-8"))
    for reference in sorted(set(references)):
        if looks_like_repo_path(reference) and not reference_exists(root, reference):
            findings.append(
                Finding(
                    code="broken_reference",
                    path=relative,
                    message=f"Не найдена ссылка: {reference}",
                    recommendation="replace-reference",
                )
            )
    return findings
```

Временно добавить минимальные реализации ещё не тестируемых функций, чтобы
модуль импортировался:

```python
def find_age_candidates(entries, today):
    return []


def find_noise_candidates(entries):
    return []


def find_duplicate_summaries(entries):
    return []


def find_budget_warnings(root, entries):
    return []


def find_legacy_registry_entries(root):
    return []


def find_project_state_history(root):
    return []
```

- [ ] **Step 4: Запустить structural tests**

Run:

```powershell
& $python -m unittest scripts.tests.test_memory_audit -v
```

Expected: `4 tests ... OK`.

### Task 3: Добавить Классификацию, Бюджеты И Детерминированный CLI

**Files:**
- Modify: `scripts/tests/test_memory_audit.py`
- Modify: `scripts/memory_audit.py`
- Create: `scripts/audit-memory.py`

- [ ] **Step 1: Добавить failing tests классификации и read-only поведения**

Перед `assertFinding` в `MemoryAuditTests` добавить:

```python
    def test_marks_old_session_for_review(self):
        self.memory_entry(
            "docs/agent-memory/sessions/old.md",
            entry_date="2026-03-14",
        )

        report = memory_audit.audit(self.root, today=date(2026, 6, 13))

        self.assertFinding(report, "aged_session", "docs/agent-memory/sessions/old.md")

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

## Исторические записи, ожидающие ревизии

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
            if finding.code == code
            and finding.path.as_posix() == relative_path
        ]
        self.assertTrue(matches, f"Missing {code} for {relative_path}: {report}")
        return matches[0]
```

Изменить `assertFinding`, чтобы он использовал helper:

```python
    def assertFinding(self, report, code: str, relative_path: str):
        self.findFinding(report, code, relative_path)
```

- [ ] **Step 2: Запустить tests и подтвердить отсутствующие реализации**

Run:

```powershell
& $python -m unittest scripts.tests.test_memory_audit -v
```

Expected: FAIL для age/noise/duplicate/budget/legacy и
`AttributeError: module 'memory_audit' has no attribute 'format_markdown'`.

- [ ] **Step 3: Реализовать классификаторы**

В `scripts/memory_audit.py` заменить временные функции:

```python
NOISY_SESSION_MARKERS = (
    "sync-vision",
    "raw-ingest",
    "repository-snapshot",
    "implementation-plan",
)
CANONICAL_PREFIXES = (
    "docs/superpowers/plans/",
    "docs/superpowers/specs/",
    "Vision_wiki/",
    "Code_wiki/",
    "RAW_inputs/",
)


def find_age_candidates(
    entries: tuple[MemoryEntry, ...], today: date
) -> list[Finding]:
    findings: list[Finding] = []
    for entry in entries:
        if entry.entry_type != "session" or entry.entry_date is None:
            continue
        age = (today - entry.entry_date).days
        if age >= STALE_SESSION_DAYS:
            findings.append(
                Finding(
                    code="aged_session",
                    path=entry.path,
                    message=f"Session не обновлялась {age} дней.",
                    recommendation="review",
                )
            )
    return findings


def find_noise_candidates(entries: tuple[MemoryEntry, ...]) -> list[Finding]:
    findings: list[Finding] = []
    for entry in entries:
        if entry.entry_type != "session":
            continue
        haystack = " ".join(
            (
                entry.path.stem.lower(),
                " ".join(tag.lower() for tag in entry.tags),
            )
        )
        markers = [
            marker for marker in NOISY_SESSION_MARKERS if marker in haystack
        ]
        has_canonical_source = any(
            reference.replace("\\", "/").startswith(CANONICAL_PREFIXES)
            for reference in entry.related_files
        )
        if not markers and not has_canonical_source:
            continue
        if markers:
            code = "noisy_session"
            message = f"Процессная session-запись: {', '.join(markers)}."
        else:
            code = "canonical_source_session"
            message = (
                "Session ссылается на canonical plan/spec/wiki source "
                "и требует проверки уникальности знания."
            )
        findings.append(
            Finding(
                code=code,
                path=entry.path,
                message=message,
                recommendation=(
                    "replace-reference" if has_canonical_source else "delete"
                ),
            )
        )
    return findings


def find_duplicate_summaries(
    entries: tuple[MemoryEntry, ...]
) -> list[Finding]:
    grouped: dict[str, list[MemoryEntry]] = defaultdict(list)
    for entry in entries:
        if len(entry.summary) >= 80:
            grouped[entry.summary].append(entry)

    findings: list[Finding] = []
    for duplicate_entries in grouped.values():
        if len(duplicate_entries) < 2:
            continue
        canonical = sorted(
            duplicate_entries, key=lambda entry: entry.path.as_posix()
        )[0]
        for duplicate in sorted(
            duplicate_entries, key=lambda entry: entry.path.as_posix()
        )[1:]:
            findings.append(
                Finding(
                    code="duplicate_summary",
                    path=duplicate.path,
                    message=(
                        "Summary совпадает с "
                        f"{canonical.path.as_posix()}."
                    ),
                    recommendation="merge",
                )
            )
    return findings


def find_budget_warnings(
    root: Path, entries: tuple[MemoryEntry, ...]
) -> list[Finding]:
    findings: list[Finding] = []
    session_count = sum(
        entry.entry_type == "session" for entry in entries
    )
    if session_count > SESSION_BUDGET:
        findings.append(
            Finding(
                code="session_budget_exceeded",
                path=Path("docs/agent-memory/sessions"),
                message=(
                    f"Активных session-записей {session_count}; "
                    f"ориентир {SESSION_BUDGET}."
                ),
                recommendation="review",
            )
        )

    registry = root / REGISTRY_PATH
    if registry.exists():
        raw = registry.read_bytes()
        line_count = len(raw.decode("utf-8").splitlines())
        if line_count > REGISTRY_MAX_LINES or len(raw) > REGISTRY_MAX_BYTES:
            findings.append(
                Finding(
                    code="registry_budget_exceeded",
                    path=REGISTRY_PATH,
                    message=(
                        f"Реестр: {line_count} строк, {len(raw)} байт; "
                        f"лимиты {REGISTRY_MAX_LINES} строк и "
                        f"{REGISTRY_MAX_BYTES} байт."
                    ),
                    recommendation="review",
                )
            )
    return findings


def find_legacy_registry_entries(root: Path) -> list[Finding]:
    registry = root / REGISTRY_PATH
    if not registry.exists():
        return []
    text = registry.read_text(encoding="utf-8")
    marker = "## Исторические записи, ожидающие ревизии"
    if marker not in text:
        return []
    legacy_text = text.split(marker, 1)[1]
    return [
        Finding(
            code="legacy_registry_entry",
            path=REGISTRY_PATH,
            message=f"Legacy block: {heading.strip()}",
            recommendation="delete",
        )
        for heading in LEGACY_HEADING_RE.findall(legacy_text)
    ]


def find_project_state_history(root: Path) -> list[Finding]:
    relative = Path("memory/project-state.md")
    path = root / relative
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    markers = (
        "Последний repository-change ingest:",
        "## Изменения С Прошлого",
    )
    present = [marker for marker in markers if marker in text]
    if not present:
        return []
    return [
        Finding(
            code="project_state_history",
            path=relative,
            message=(
                "Live state содержит исторические поля: "
                + ", ".join(present)
            ),
            recommendation="review",
        )
    ]
```

- [ ] **Step 4: Добавить deterministic formatters**

В конец `scripts/memory_audit.py` добавить:

```python
def format_text(report: AuditReport) -> str:
    lines = [
        f"Memory entries: {len(report.entries)}",
        f"Findings: {len(report.findings)}",
    ]
    for finding in report.findings:
        lines.append(
            f"{finding.recommendation}: {finding.code}: "
            f"{finding.path.as_posix()}: {finding.message}"
        )
    return "\n".join(lines)


def format_markdown(report: AuditReport) -> str:
    lines = [
        "# Отчёт Аудита Памяти",
        "",
        f"- Memory entries: {len(report.entries)}",
        f"- Findings: {len(report.findings)}",
        "",
        "| Действие | Код | Путь | Причина |",
        "| --- | --- | --- | --- |",
    ]
    for finding in report.findings:
        message = finding.message.replace("|", "\\|")
        lines.append(
            f"| {finding.recommendation} | {finding.code} | "
            f"`{finding.path.as_posix()}` | {message} |"
        )
    return "\n".join(lines)
```

- [ ] **Step 5: Создать тонкий CLI без write operations**

Создать `scripts/audit-memory.py`:

```python
#!/usr/bin/env python3
"""Print a deterministic read-only audit of repo-local agent memory."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from memory_audit import audit, format_markdown, format_text


def parse_today(value: str) -> date:
    return date.fromisoformat(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument(
        "--today",
        type=parse_today,
        help="ISO date override for deterministic audits.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "markdown"),
        default="text",
        help="Report format written to stdout.",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.exists():
        parser.error(f"Repository root does not exist: {root}")

    report = audit(root, today=args.today)
    formatter = format_markdown if args.format == "markdown" else format_text
    print(formatter(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 6: Запустить tests и CLI дважды**

Run:

```powershell
& $python -m unittest scripts.tests.test_memory_audit -v
$first = & $python scripts/audit-memory.py --root . --today 2026-06-13 --format markdown
$second = & $python scripts/audit-memory.py --root . --today 2026-06-13 --format markdown
if (($first -join "`n") -ne ($second -join "`n")) { throw 'Audit output changed' }
```

Expected: audit tests проходят; два отчёта идентичны; команда не меняет
`git status --short`.

### Task 4: Обновить Правила Memory Lifecycle

**Files:**
- Create: `.agents/skills/source-command-audit-memory/SKILL.md`
- Modify: `AGENTS.md`
- Modify: `docs/agent-memory/protocol.md`
- Modify: `docs/agent-memory/README.md`
- Modify: `docs/agent-memory/decisions/2026-05-30-agent-memory-operating-rules.md`
- Modify: `scripts/README.md`
- Modify: `.agents/skills/source-command-lint-wiki/SKILL.md`
- Modify: `.agents/skills/source-command-sync-vision/SKILL.md`
- Modify: `docs/knowledge-pipeline/README.md`

- [ ] **Step 1: Создать ручную процедуру `/audit-memory`**

Создать `.agents/skills/source-command-audit-memory/SKILL.md`:

```markdown
---
name: source-command-audit-memory
description: Ручная read-only процедура /audit-memory для поиска шума, дублей, устаревших ссылок и кандидатов на очистку agent memory.
---

# /audit-memory

`/audit-memory` анализирует `docs/agent-memory/` и legacy записи
`repository_change_ingest.md`. Команда формирует кандидатов, но не изменяет и
не удаляет файлы.

## Шаг 1. Запустить Детерминированный Аудит

```powershell
python scripts/audit-memory.py --root . --format markdown
```

Если системный `python` недоступен, использовать bundled Python текущей среды.

## Шаг 2. Проверить Findings

Для каждого кандидата проверить:

- есть ли уникальное знание, которого нет в design, plan, code или wiki;
- существует ли указанный canonical source;
- актуальны ли decision, pattern или bug root cause;
- не является ли session-запись только результатом sync, ingest, lint,
  planning или завершения задачи.

## Шаг 3. Подготовить Отчёт Пользователю

Сгруппировать кандидатов по рекомендациям:

- `keep`;
- `merge`;
- `replace-reference`;
- `delete`;
- `review`.

Для `merge`, `replace-reference` и `delete` назвать конкретные paths и причины.

## Шаг 4. Остановиться До Подтверждения

Не удалять, не перемещать и не объединять файлы без отдельного подтверждения
пользователя. После подтверждения выполнить отдельную implementation-задачу,
очистить `file-map.md` и проверить ссылки.

## Ограничения

- Не изменять файлы как часть аудита.
- Не считать возраст достаточным основанием для удаления decision, pattern или
  bugfix.
- Не использовать `Superseded by` вместо удаления явного шума.
- Не сохранять каждый audit report как новую memory/session запись.
```

- [ ] **Step 2: Переписать обязательные критерии memory write**

В `AGENTS.md` заменить текущий абзац `Significant work means...` и правило
repository-change на:

```markdown
Create or update agent memory only when both conditions hold:

1. The knowledge is likely to remain useful for at least a week.
2. Existing code, design, plan, runbook, or wiki does not already preserve it,
   or the memory adds an important explanation of why.

Store decisions with consequences, non-obvious bug root causes, stable
patterns, non-obvious file relationships, and unique operational constraints.
Do not store task completion, changed-file lists, test logs, sync/ingest/lint
results, or summaries of existing plans and wiki nodes. Update an existing
entry instead of creating a duplicate. Use `sessions/` only for unfinished
handoff or a unique result that fits no decision, pattern, bugfix, or wiki
node.
```

В weekly workflow добавить:

```markdown
5. Run `/audit-memory`; present cleanup candidates and wait for confirmation
   before deleting or merging anything.
```

Repository-change правило заменить:

```markdown
Invoke `/ingest repository-change` only when completed work contains new
durable technical knowledge that needs to be reflected in `Code_wiki`.
Repository Change Ingest itself identifies the target nodes, chooses create
or update, changes the nodes, and updates the registry. If there is no new
durable technical knowledge, do not invoke it. Task size, plan completion,
commits, and successful tests are not triggers.
```

- [ ] **Step 3: Обновить authoritative memory protocol**

В `docs/agent-memory/protocol.md`:

- заменить `When To Write Memory` критериями из design;
- удалить specs/plans из безусловно обязательных triggers;
- добавить три pre-write вопроса;
- определить `sessions/` как exceptional;
- изменить `Superseding Memory`: полезная история остаётся с
  `Superseded by`, шум после подтверждения удаляется и остаётся в Git;
- добавить weekly `/audit-memory`.

Обязательный текст pre-write gate:

```markdown
Before creating a memory entry, answer:

1. What unique knowledge would be lost without this entry?
2. Why is a link to existing code, design, plan, runbook, or wiki insufficient?
3. In which future task should an agent retrieve this entry?

If the answers are not concrete, do not create the entry.
```

- [ ] **Step 4: Обновить существующую operating-rules decision**

В `docs/agent-memory/decisions/2026-05-30-agent-memory-operating-rules.md`
добавить related file:

```markdown
- `docs/superpowers/plans/2026-06-13-memory-knowledge-base-optimization.md`
```

И action:

```markdown
- 2026-06-13: Implementation plan зафиксировал read-only audit, бюджеты
  `20 sessions / 90 days / 200 lines / 24 KiB`, exceptional `sessions/` и
  пользовательский gate перед cleanup.
```

- [ ] **Step 5: Обновить README и pipeline runbooks**

В `docs/agent-memory/README.md` заменить описание `sessions/`:

```markdown
- `sessions/` - exceptional unfinished handoff or unique outcomes that fit no
  decision, pattern, bugfix, or wiki node; not a task log.
```

Добавить команду аудита:

```powershell
python scripts/audit-memory.py --root . --format markdown
```

В `scripts/README.md` добавить раздел:

```markdown
## `audit-memory.py`

Read-only аудит agent memory: broken references, noisy sessions, exact
duplicate summaries, age candidates, budgets и legacy repository-change
entries.

```powershell
python scripts/audit-memory.py --root . --format markdown
```

Findings являются отчётом для review и не приводят к автоматическому удалению.
```

В `.agents/skills/source-command-lint-wiki/SKILL.md` явно указать, что
`/lint-wiki` не классифицирует agent memory; для этого используется
`/audit-memory`.

В `.agents/skills/source-command-sync-vision/SKILL.md` изменить Step 5:
`project-state` хранит текущее состояние и следующий action, но не список
завершённых событий с прошлого sync.

В `docs/knowledge-pipeline/README.md` добавить weekly `/audit-memory` после
`/lint-wiki` и заменить старый unconditional repository-change trigger новым
двухвопросным gate.

- [ ] **Step 6: Проверить отсутствие старых обязательных формулировок**

Run:

```powershell
rg -n "After the full implementation plan|После полного завершения реализации плана|durable plan/spec|summaries of significant completed work" AGENTS.md docs/agent-memory docs/knowledge-pipeline .agents/skills scripts/README.md
```

Expected: совпадений в активных правилах нет. Исторические memory entries могут
содержать старый текст до Task 6, где они помечаются superseded.

- [ ] **Step 7: Запустить tests**

Run:

```powershell
& $python -m unittest discover -s scripts\tests -v
```

Expected: все scripts tests проходят.

### Task 5: Ввести Новый Repository-Change Gate И Компактный Реестр

**Files:**
- Modify: `.agents/skills/source-command-ingest/SKILL.md`
- Modify: `Code_wiki/состояние_проекта/repository_change_ingest.md`
- Modify: `Code_wiki/состояние_проекта/_info.md`
- Modify: `Code_wiki/index.md`
- Modify: `memory/project-state.md`

- [ ] **Step 1: Переписать режим `repository-change` в ingest skill**

В `.agents/skills/source-command-ingest/SKILL.md` заменить вводный trigger и
порядок режима `repository-change`:

```markdown
## Режим `repository-change`

Вызывать режим только если завершённая работа содержит новое устойчивое
техническое знание, которое требуется отразить в `Code_wiki`.

До ingest определяется только наличие нового знания. Конкретные ноды и
операцию create/update определяет и выполняет сам `Repository Change Ingest`.
Если нового знания нет, завершить без изменений. Размер задачи, завершение
plan, commit, успешные tests и изменения только index/state не являются
trigger.

Порядок:

1. Определить новое устойчивое знание и его источники.
2. Проверить `git status --short` и точечный diff только для подтверждения
   нового знания.
3. Изучить релевантную область `Code_wiki` и определить create/update.
4. Создать или содержательно обновить выбранные ноды.
5. Добавить в активный реестр одну строку на каждую изменённую `Code_wiki`
   ноду: дата, wikilink, причина, проверяемый source.
6. Обновить `Code_wiki/index.md` только если появилась новая важная нода.
7. Обновить `memory/project-state.md` только если изменилось живое состояние
   или следующий action.
8. Запустить `python scripts/lint-wiki.py --root .`.
```

Добавить ограничения:

```markdown
- Не создавать запись только о выполнении plan/task/tests.
- Не перечислять code files и verification logs в реестре.
- Не создавать index/state-only строку реестра.
- Не изменять legacy history до подтверждённой cleanup-задачи.
```

- [ ] **Step 2: Добавить компактный активный реестр без удаления legacy**

В `Code_wiki/состояние_проекта/repository_change_ingest.md`:

1. изменить заголовок на `# Реестр Изменений Нод Code_wiki`;
2. заменить вводное описание;
3. перед текущим `## Записи` вставить:

```markdown
## Активный Реестр

Одна строка соответствует содержательному созданию или обновлению одной
`Code_wiki` ноды. Изменения только index/state, task completion, commits и test
logs не регистрируются.

| Дата | Нода | Причина | Источник |
| --- | --- | --- | --- |
| 2026-06-13 | [[состояние_проекта/_info]] | Раздел состояния переведён с task log на реестр содержательных изменений нод. | `docs/superpowers/specs/2026-06-13-memory-knowledge-base-optimization-design.md` |

## Исторические записи, ожидающие ревизии

Блоки ниже сохранены без удаления до пользовательского подтверждения отчёта
`/audit-memory`. Новые repository-change записи сюда не добавляются.
```

Текущий `## Записи` удалить как лишний промежуточный heading, но все 19
`### ...` blocks оставить без смыслового изменения.

- [ ] **Step 3: Обновить навигацию Code_wiki**

В `Code_wiki/состояние_проекта/_info.md` заменить:

```markdown
Здесь хранится текущее техническое состояние проекта, журнал первичных
repository snapshot'ов и компактный реестр содержательных изменений нод.
```

И:

```markdown
- [[repository_change_ingest]] - компактный реестр созданных и содержательно
  обновлённых `Code_wiki` нод; legacy task-log ожидает подтверждённой ревизии.
```

В `Code_wiki/index.md` заменить описание link на:

```markdown
- [[состояние_проекта/repository_change_ingest]] - компактный реестр
  содержательных изменений технических нод.
```

- [ ] **Step 4: Сократить repository-change поля live state**

В `memory/project-state.md` заменить строку последнего repository-change на
текущее actionable состояние:

```markdown
- Repository-change gate: активен новый режим «target `Code_wiki` node + новое
  устойчивое знание»; legacy task-log ожидает пользовательской ревизии.
```

В разделе изменений удалить завершённые implementation details, которые не
определяют следующий action. Не менять продуктовые факты и открытые вопросы.

- [ ] **Step 5: Проверить новый формат и сохранность legacy blocks**

Run:

```powershell
$legacyCount = (Select-String -Path 'Code_wiki/состояние_проекта/repository_change_ingest.md' -Pattern '^### ' | Measure-Object).Count
if ($legacyCount -ne 19) { throw "Expected 19 preserved legacy entries, got $legacyCount" }
rg -n "^## Активный Реестр$|^## Исторические записи, ожидающие ревизии$|^\| 2026-06-13 " 'Code_wiki/состояние_проекта/repository_change_ingest.md'
```

Expected: legacy count остаётся `19`; активный table содержит одну строку на
изменённую `_info` ноду.

- [ ] **Step 6: Запустить audit**

Run:

```powershell
& $python scripts/audit-memory.py --root . --today 2026-06-13 --format text
```

Expected: report содержит `legacy_registry_entry` для каждого из 19 блоков и
`registry_budget_exceeded`; exit code `0`.

### Task 6: Синхронизировать Quality Docs И Durable Decisions

**Files:**
- Modify: `Code_wiki/сборка/ci_and_quality.md`
- Modify: `Code_wiki/правила_и_стиль/testing_strategy.md`
- Modify: `Code_wiki/состояние_проекта/repository_change_ingest.md`
- Modify: `docs/agent-memory/decisions/2026-05-30-agent-driven-repository-change-ingest.md`
- Modify: `docs/agent-memory/file-map.md`

- [ ] **Step 1: Добавить memory audit в локальные проверки**

В `Code_wiki/сборка/ci_and_quality.md` и
`Code_wiki/правила_и_стиль/testing_strategy.md` рядом с wiki checks добавить:

```powershell
python scripts/audit-memory.py --root . --format text
```

Пояснить:

```markdown
`audit-memory.py` всегда read-only. Findings требуют review, но не являются
test failure и не разрешают автоматическое удаление.
```

- [ ] **Step 2: Добавить по одной строке активного реестра на изменённую ноду**

В таблицу `## Активный Реестр` добавить:

```markdown
| 2026-06-13 | [[сборка/ci_and_quality]] | В локальные quality checks добавлен read-only memory audit. | `docs/superpowers/specs/2026-06-13-memory-knowledge-base-optimization-design.md` |
| 2026-06-13 | [[правила_и_стиль/testing_strategy]] | Testing strategy разделила wiki lint, memory guard и lifecycle audit. | `docs/superpowers/specs/2026-06-13-memory-knowledge-base-optimization-design.md` |
```

- [ ] **Step 3: Пометить старый repository-change trigger superseded**

В начало
`docs/agent-memory/decisions/2026-05-30-agent-driven-repository-change-ingest.md`
после `Type` добавить:

```markdown
Superseded by: docs/agent-memory/decisions/2026-05-30-agent-memory-operating-rules.md
```

В Summary добавить:

```markdown
Историческое решение сохраняет отказ от pre-commit automation, но trigger
«после каждого полного plan или крупной задачи» заменён правилом
«конкретная `Code_wiki` нода + новое устойчивое знание».
```

- [ ] **Step 4: Очистить и дополнить file map**

В `docs/agent-memory/file-map.md`:

- добавить:

```markdown
- agent memory lifecycle audit: `scripts/memory_audit.py`, `scripts/audit-memory.py`, `scripts/tests/test_memory_audit.py`, `.agents/skills/source-command-audit-memory/SKILL.md`
```

- обновить repository-change workflow строкой с новым gate;
- удалить отдельные session links на plan/implementation, если canonical
  design/plan/code paths уже перечислены в той же строке;
- не удалять ссылки на файлы до подтверждённой cleanup-задачи.

- [ ] **Step 5: Запустить memory guard на staged fixture**

Так как production CLI читает staged paths, проверить unit tests:

```powershell
& $python -m unittest scripts.tests.test_check_memory_needed -v
& $python -m unittest scripts.tests.test_memory_audit -v
```

Expected: оба test modules проходят.

### Task 7: Выполнить Полную Проверку И Сформировать Cleanup Candidates

**Files:**
- No repository edits expected

- [ ] **Step 1: Запустить полный scripts test suite**

Run:

```powershell
& $python -m unittest discover -s scripts\tests -v
```

Expected: все tests проходят, включая:

- обычный plan/spec не требует memory update;
- operating-rule changes требуют memory context;
- broken references, noisy sessions, duplicate summaries, age и budgets
  обнаруживаются;
- audit output детерминирован и read-only.

- [ ] **Step 2: Запустить memory audit дважды и сравнить output**

Run:

```powershell
$first = & $python scripts/audit-memory.py --root . --today 2026-06-13 --format markdown
$second = & $python scripts/audit-memory.py --root . --today 2026-06-13 --format markdown
if (($first -join "`n") -ne ($second -join "`n")) { throw 'Audit output is not deterministic' }
$first
```

Expected:

- report перечисляет текущие session и legacy registry candidates;
- присутствуют recommendations `review`, `replace-reference`, `delete` или
  `merge` по применимым heuristics;
- `registry_budget_exceeded` сохраняется до подтверждённой cleanup-задачи;
- команда возвращает exit code `0`.

- [ ] **Step 3: Подтвердить read-only поведение**

Run:

```powershell
$before = git status --short
& $python scripts/audit-memory.py --root . --today 2026-06-13 --format text | Out-Null
$after = git status --short
if (($before -join "`n") -ne ($after -join "`n")) { throw 'Audit modified repository files' }
```

Expected: status до и после одинаков.

- [ ] **Step 4: Запустить wiki lint и зафиксировать известный baseline**

Run:

```powershell
& $python scripts/lint-wiki.py --root .
```

Expected: только 12 известных `missing_frontmatter` в неизменяемых
`RAW_inputs/`, связанных с `FU-2026-06-01-004`. Новых issues в изменённых
wiki-файлах нет.

- [ ] **Step 5: Запустить финальные consistency checks**

Run:

```powershell
git diff --check
rg -n "T(BD)|T(ODO)|F(IXME)" scripts/memory_audit.py scripts/audit-memory.py .agents/skills/source-command-audit-memory/SKILL.md
rg -n "После полного завершения реализации плана|After the full implementation plan" AGENTS.md docs/knowledge-pipeline .agents/skills/source-command-ingest
```

Expected:

- `git diff --check` проходит;
- placeholders отсутствуют;
- старый unconditional repository-change trigger отсутствует в активных
  rules.

- [ ] **Step 6: Представить пользователю отчёт и остановиться**

В финальном отчёте перечислить:

- количество active memory entries;
- количество candidates по каждой recommendation;
- 19 legacy repository-change blocks;
- broken references;
- session budget warning;
- конкретные proposed delete/merge/replace-reference paths.

Не удалять и не объединять файлы. Запросить подтверждение конкретного набора
действий. Следующая работа начинается с отдельного cleanup plan.

## После Пользовательского Подтверждения

Отдельный cleanup plan должен:

1. Зафиксировать подтверждённый список paths и legacy blocks.
2. Удалить или объединить только подтверждённые элементы.
3. Очистить `docs/agent-memory/file-map.md` и прямые ссылки.
4. Удалить раздел legacy history из
   `Code_wiki/состояние_проекта/repository_change_ingest.md`, оставив только
   компактный реестр.
5. Повторить `unittest`, `/audit-memory`, `/lint-wiki` и `git diff --check`.
6. Подтвердить отсутствие broken references и
   `registry_budget_exceeded`.
