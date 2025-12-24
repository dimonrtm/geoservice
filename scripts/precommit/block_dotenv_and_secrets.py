#!/usr/bin/env python
from __future__ import annotations

import os
import re
import sys
from pathlib import Path


SECRET_RE = re.compile(r"(password|passwd|secret|api[_-]?key|token)\s*[:=]\s*\S{6,}", re.IGNORECASE)

SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp", ".gif",
    ".zip", ".gz", ".7z",
    ".exe", ".dll", ".pdb",
    ".pdf",
}

SKIP_FILES_EXACT = {".env.example"}  # allow template


def is_probably_binary(data: bytes) -> bool:
    # crude but effective
    return b"\x00" in data


def read_text_safely(path: Path, max_bytes: int = 200_000) -> str:
    data = path.read_bytes()[:max_bytes]
    if is_probably_binary(data):
        return ""
    return data.decode("utf-8", errors="ignore")


def fail(msg: str) -> int:
    print("")
    print(f"Error pre-commit: {msg}")
    print("")
    return 1


def main(argv: list[str]) -> int:
    # pre-commit passes the file list as args
    files = [Path(a) for a in argv[1:] if a and not a.startswith("-")]

    # If no files were passed (rare), do nothing
    if not files:
        return 0

    for f in files:
        rel = f.as_posix()

        # 1) Block .env and .env.* except .env.example
        if rel == ".env":
            return fail("Файл .env нельзя коммитить. Используй .env.example.")
        if rel.startswith(".env.") and rel != ".env.example":
            return fail(f"Файл {rel} нельзя коммитить. Оставь только .env.example как шаблон.")

    for f in files:
        rel = f.as_posix()
        name = f.name

        if name in SKIP_FILES_EXACT:
            continue

        ext = f.suffix.lower()
        if ext in SKIP_EXTENSIONS:
            continue

        # f may not exist in working tree for deleted files, etc.
        if not f.exists() or not f.is_file():
            continue

        text = read_text_safely(f)
        if not text:
            continue

        if SECRET_RE.search(text):
            return fail(
                f"Похоже, в файле {rel} есть секрет (password/secret/token/apiKey). "
                "Удали/замени значение и используй .env (который не коммитится)."
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
