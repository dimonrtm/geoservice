#!/usr/bin/env python3
"""No-dependency Markdown wiki linter for the project knowledge pipeline."""

from __future__ import annotations

import argparse
import dataclasses
import re
import sys
from pathlib import Path


WIKI_ROOTS = (
    "Vision_wiki",
    "Code_wiki",
    "RAW_inputs",
    "memory",
    "Общие_принципы",
    "docs/knowledge-pipeline",
)
REQUIRED_FRONTMATTER = (
    "title",
    "type",
    "status",
    "created",
    "updated",
    "source",
    "tags",
)
SOURCE_REQUIRED_TYPES = {
    "adr",
    "api-endpoint",
    "concept",
    "decision",
    "postmortem",
    "risk",
    "runbook",
    "service",
    "session",
}
SOURCE_OPTIONAL_TYPES = {"index", "method", "glossary", "state"}
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")


@dataclasses.dataclass(frozen=True)
class Issue:
    code: str
    path: Path
    message: str

    def __str__(self) -> str:
        return f"{self.code}: {self.path.as_posix()}: {self.message}"


def lint(root: Path | str) -> list[Issue]:
    root = Path(root)
    files = list(iter_markdown_files(root))
    file_index = build_file_index(root, files)
    issues: list[Issue] = []

    for file_path in files:
        relative = file_path.relative_to(root)
        text = file_path.read_text(encoding="utf-8")
        frontmatter, body = parse_frontmatter(text)

        if frontmatter is None:
            issues.append(
                Issue(
                    "missing_frontmatter",
                    relative,
                    "Markdown wiki node must start with YAML frontmatter.",
                )
            )
            continue

        missing = [key for key in REQUIRED_FRONTMATTER if key not in frontmatter]
        if missing:
            issues.append(
                Issue(
                    "invalid_frontmatter",
                    relative,
                    f"Missing keys: {', '.join(missing)}.",
                )
            )

        node_type = frontmatter.get("type", "")
        source = frontmatter.get("source")
        if source_required(node_type, relative) and source in {None, "", "null", "~"}:
            issues.append(
                Issue(
                    "missing_source",
                    relative,
                    "Non-index wiki nodes must reference a source.",
                )
            )

        if not body.strip():
            issues.append(Issue("empty_node", relative, "Markdown body is empty."))

        for link in WIKILINK_RE.findall(body):
            if not wikilink_exists(link.strip(), file_index):
                issues.append(
                    Issue(
                        "broken_wikilink", relative, f"Unresolved wikilink: [[{link}]]."
                    )
                )

    return issues


def iter_markdown_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for wiki_root in WIKI_ROOTS:
        base = root / wiki_root
        if not base.exists():
            continue
        files.extend(base.rglob("*.md"))
    index = root / "index.md"
    if index.exists():
        files.append(index)
    return sorted(set(files))


def build_file_index(root: Path, files: list[Path]) -> set[str]:
    index: set[str] = set()
    for file_path in files:
        relative = file_path.relative_to(root).as_posix()
        without_suffix = relative[:-3] if relative.endswith(".md") else relative
        index.add(without_suffix)
        index.add(file_path.stem)
        if file_path.name == "index.md":
            index.add(file_path.parent.relative_to(root).as_posix())
    return index


def parse_frontmatter(text: str) -> tuple[dict[str, str] | None, str]:
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 4)
    if end == -1:
        return None, text

    raw = text[4:end].strip("\n")
    body = text[end + len("\n---") :]
    frontmatter: dict[str, str] = {}
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        frontmatter[key.strip()] = value.strip()
    return frontmatter, body


def source_required(node_type: str, relative: Path) -> bool:
    if (
        len(relative.parts) >= 2
        and relative.parts[0] == "docs"
        and relative.parts[1] == "knowledge-pipeline"
    ):
        return False
    if "_templates" in relative.parts:
        return False
    if relative.name == "_info.md":
        return False
    if relative.name == "index.md":
        return False
    if node_type in SOURCE_OPTIONAL_TYPES:
        return False
    return node_type in SOURCE_REQUIRED_TYPES or relative.parts[0] in {
        "Vision_wiki",
        "Code_wiki",
    }


def wikilink_exists(link: str, file_index: set[str]) -> bool:
    normalized = link.replace("\\", "/").strip("/")
    candidates = {normalized}
    if normalized.endswith(".md"):
        candidates.add(normalized[:-3])
    if normalized.startswith("../"):
        candidates.add(normalized[3:])
    if "/" in normalized:
        candidates.add(normalized.split("/")[-1])
    return bool(candidates & file_index)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", default=".", help="Repository root. Defaults to current directory."
    )
    args = parser.parse_args(argv)

    issues = lint(Path(args.root).resolve())
    for issue in issues:
        print(issue)
    if issues:
        print(f"Wiki lint found {len(issues)} issue(s).")
        return 1
    print("Wiki lint passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
