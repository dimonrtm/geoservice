from pathlib import Path

import pytest


def find_repo_root(start: Path) -> Path | None:
    for candidate in (start, *start.parents):
        if (candidate / ".github" / "workflows" / "ci.yml").exists():
            return candidate
    return None


REPO_ROOT = find_repo_root(Path(__file__).resolve())
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml" if REPO_ROOT is not None else None

pytestmark = pytest.mark.skipif(
    CI_WORKFLOW is None,
    reason="Repository CI workflow is not available in the backend-only Docker image.",
)


def test_ci_runs_db_tests_in_isolated_compose_and_checks_demo_fingerprint() -> None:
    assert CI_WORKFLOW is not None
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "exec -T utility_service env RUN_DB_TESTS=1" not in workflow
    assert "docker-compose.test.yml" in workflow
    assert "geoservice-db-tests" in workflow
    assert "--exit-code-from backend_db_tests" in workflow
    assert "DEMO_FINGERPRINT_BEFORE" in workflow
    assert "DEMO_FINGERPRINT_AFTER" in workflow
    assert 'if [ "$DEMO_FINGERPRINT_BEFORE" != "$DEMO_FINGERPRINT_AFTER" ]' in workflow


def test_ci_always_removes_isolated_db_test_project() -> None:
    assert CI_WORKFLOW is not None
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    cleanup_start = workflow.index("- name: Shutdown isolated DB test compose")
    cleanup = workflow[cleanup_start:]

    assert "if: always()" in cleanup
    assert "geoservice-db-tests" in cleanup
    assert "docker-compose.test.yml" in cleanup
    assert "down -v --remove-orphans" in cleanup
