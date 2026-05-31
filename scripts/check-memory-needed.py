#!/usr/bin/env python3
"""Warn when durable planning/rule changes are staged without agent memory."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


DURABLE_PREFIXES = (
    "AGENTS.md",
    "CONTRIBUTING.md",
    "docs/superpowers/plans/",
    "docs/superpowers/specs/",
    "docs/knowledge-pipeline/",
    ".agents/skills/",
)
MEMORY_PREFIX = "docs/agent-memory/"


def needs_memory_update(changed_paths: list[str], memory_paths: list[str]) -> bool:
    has_durable_change = any(is_durable_path(path) for path in changed_paths)
    has_memory_change = any(
        normalize(path).startswith(MEMORY_PREFIX) for path in memory_paths
    )
    return has_durable_change and not has_memory_change


def is_durable_path(path: str) -> bool:
    normalized = normalize(path)
    return any(
        normalized == prefix or normalized.startswith(prefix)
        for prefix in DURABLE_PREFIXES
    )


def normalize(path: str) -> str:
    return path.replace("\\", "/").strip()


def staged_paths(repo_root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=True,
    )
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--check", action="store_true", help="Check staged files.")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    paths = staged_paths(repo_root)
    memory_paths = [path for path in paths if normalize(path).startswith(MEMORY_PREFIX)]

    if needs_memory_update(paths, memory_paths):
        print(
            "Durable plan/spec/rule changes are staged without docs/agent-memory updates."
        )
        print(
            "Add or update a relevant memory entry, or document why memory is not needed."
        )
        return 1

    print("Memory update check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
