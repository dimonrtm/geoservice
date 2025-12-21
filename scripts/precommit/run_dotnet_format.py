#!/usr/bin/env python
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> int:
    p = subprocess.run(cmd, cwd=str(cwd), text=True)
    return p.returncode


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    backend = repo_root / "backend"

    # If backend folder doesn't exist or has no .sln/.csproj, skip.
    if not backend.exists():
        return 0

    slns = list(backend.rglob("*.sln"))
    csprojs = list(backend.rglob("*.csproj"))

    if not slns and not csprojs:
        return 0

    # Prefer solution if present
    target = slns[0] if slns else csprojs[0]

    # dotnet must be installed in PATH
    # Use "dotnet format" in verify mode to avoid auto-modifying files unexpectedly.
    # Later you can switch to formatting mode.
    cmd = ["dotnet", "format", str(target), "--verify-no-changes"]
    rc = run(cmd, cwd=repo_root)
    if rc != 0:
        print("")
        print("ERROR: dotnet format check failed. Run formatting locally:")
        print(f"  dotnet format {target}")
        print("")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
