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
REGISTRY_PATH = Path("Code_wiki/состояние_проекта/repository_change_ingest.md")
FIELD_RE = re.compile(r"^(Date|Type|Tags):\s*(.+)$", re.MULTILINE)
BACKTICK_PATH_RE = re.compile(r"`([^`\n]+)`")
SUPERSEDED_RE = re.compile(r"^Superseded by:\s*(\S+)\s*$", re.MULTILINE)
LEGACY_HEADING_RE = re.compile(r"^###\s+(.+)$", re.MULTILINE)
LEGACY_SECTION_RE = re.compile(
    r"^##\s+Исторические записи, ожидающие ревизии\s*$",
    re.IGNORECASE | re.MULTILINE,
)
NOISY_SESSION_MARKERS = (
    "sync-vision",
    "raw-ingest",
    "repository-snapshot",
    "implementation-plan",
)
CANONICAL_PREFIXES = (
    "docs/superpowers/plans/",
    "docs/superpowers/specs/",
    "docs/sprint_1/",
    "Vision_wiki/",
    "Code_wiki/",
    "RAW_inputs/",
)


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
        item.strip() for item in fields.get("Tags", "").split(",") if item.strip()
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
    normalized = value.strip().strip("`").replace("\\", "/")
    has_known_suffix = Path(normalized).suffix in {
        ".md",
        ".py",
        ".yml",
        ".yaml",
    }
    return (
        ("/" in normalized or has_known_suffix)
        and not normalized.startswith(("http://", "https://"))
        and re.match(r"^[A-Za-z]:/", normalized) is None
        and "*" not in normalized
        and not normalized.startswith("<")
    )


def reference_exists(root: Path, value: str) -> bool:
    normalized = value.strip().strip("`").replace("\\", "/").split("#", 1)[0].strip()
    return bool(normalized) and (root / normalized).exists()


def find_broken_references(
    root: Path, entries: tuple[MemoryEntry, ...]
) -> list[Finding]:
    findings: list[Finding] = []
    for entry in entries:
        references = list(entry.related_files)
        references.extend(SUPERSEDED_RE.findall(entry.text))
        for reference in sorted(set(references)):
            if looks_like_repo_path(reference) and not reference_exists(
                root, reference
            ):
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


def find_age_candidates(entries: tuple[MemoryEntry, ...], today: date) -> list[Finding]:
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
        markers = [marker for marker in NOISY_SESSION_MARKERS if marker in haystack]
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


def find_duplicate_summaries(entries: tuple[MemoryEntry, ...]) -> list[Finding]:
    grouped: dict[str, list[MemoryEntry]] = defaultdict(list)
    for entry in entries:
        if len(entry.summary) >= 80:
            grouped[entry.summary].append(entry)

    findings: list[Finding] = []
    for duplicate_entries in grouped.values():
        if len(duplicate_entries) < 2:
            continue
        ordered = sorted(
            duplicate_entries,
            key=lambda entry: entry.path.as_posix(),
        )
        canonical = ordered[0]
        for duplicate in ordered[1:]:
            findings.append(
                Finding(
                    code="duplicate_summary",
                    path=duplicate.path,
                    message=("Summary совпадает с " f"{canonical.path.as_posix()}."),
                    recommendation="merge",
                )
            )
    return findings


def find_budget_warnings(root: Path, entries: tuple[MemoryEntry, ...]) -> list[Finding]:
    findings: list[Finding] = []
    session_count = sum(entry.entry_type == "session" for entry in entries)
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
    marker = LEGACY_SECTION_RE.search(text)
    if marker is None:
        return []
    legacy_text = text[marker.end() :]
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
            message=("Live state содержит исторические поля: " + ", ".join(present)),
            recommendation="review",
        )
    ]


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
