"""Host-side restart proof shared by CI and the local smoke runbook (stdlib only)."""

import argparse
import json
from pathlib import Path
import subprocess
import time
from uuid import UUID


def wait_for_restart(before, inspect, *, sleep=lambda: time.sleep(2), attempts=60):
    for attempt in range(attempts):
        started, health = inspect()
        if started and started != before and health == "healthy":
            return started
        if attempt + 1 < attempts:
            sleep()
    raise RuntimeError("Backend restart/readiness timeout")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("compose", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    prefix = args.compose[1:] if args.compose[:1] == ["--"] else args.compose
    if not prefix or prefix[:2] != ["docker", "compose"]:
        parser.error("После -- ожидается docker compose с параметрами окружения")
    UUID(args.run_id)
    manifest = {"runId": args.run_id, "status": "running"}

    def run(command):
        return subprocess.check_output(command, text=True, timeout=60).strip()

    def inspect(container):
        value = json.loads(run(["docker", "inspect", "--format", "{{json .State}}", container]))
        return value["StartedAt"], value.get("Health", {}).get("Status", "unknown")

    try:
        api = run([*prefix, "ps", "-q", "utility_service"])
        db = run([*prefix, "ps", "-q", "postgis"])
        if not api or not db:
            raise RuntimeError("Missing smoke containers")
        manifest["startedBefore"] = inspect(api)[0]
        manifest["databaseStartedBefore"] = inspect(db)[0]
        run([*prefix, "restart", "utility_service"])
        manifest["startedAfter"] = wait_for_restart(manifest["startedBefore"], lambda: inspect(api))
        run(
            [
                *prefix,
                "exec",
                "-T",
                "utility_service",
                "python",
                "-c",
                "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5)",
            ]
        )
        manifest["databaseStartedAfter"] = inspect(db)[0]
        if manifest["databaseStartedAfter"] != manifest["databaseStartedBefore"]:
            raise RuntimeError("Database restarted during API smoke")
        manifest["status"] = "passed"
        return 0
    except (RuntimeError, subprocess.SubprocessError, ValueError, KeyError) as exc:
        manifest.update(status="failed", errorType=type(exc).__name__)
        return 1
    finally:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_bytes((json.dumps(manifest, indent=2) + "\n").encode("utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
