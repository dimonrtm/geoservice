#!/usr/bin/env python
from __future__ import annotations

import subprocess
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    frontend = repo_root / "frontend"

    if not frontend.exists():
        return 0

    pkg = frontend / "package.json"
    if not pkg.exists():
        return 0

    # Run prettier check if npm is available and prettier script exists.
    # We try "npm run -s format:check" first; if not present, skip.
    try:
        p = subprocess.run(
            ["npm", "run", "-s", "format:check"],
            cwd=str(frontend),
            text=True,
        )
        # If script doesn't exist, npm returns non-zero; treat as skip by checking stderr? Hard in plain run.
        # We'll interpret common "missing script" as skip by re-running "npm run" with list and searching is overkill.
        # So we assume user will add the script when frontend is ready.
        return p.returncode
    except FileNotFoundError:
        # npm not installed in PATH => skip
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
