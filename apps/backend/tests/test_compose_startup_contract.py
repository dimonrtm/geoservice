from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parents[1]
DEMO_STARTUP_STEPS = (
    "alembic upgrade head",
    "python -m seeds.runners.seed_demo_users",
    "python -m seeds.runners.seed_utility_dataset",
    "python -m seeds.runners.seed_work_orders",
    "python -m seeds.runners.upgrade_demo_fixture",
)


def script_text(relative_path: str) -> str:
    return (BACKEND_ROOT / relative_path).read_text(encoding="utf-8")


def test_demo_startup_script_runs_all_fixture_steps_before_api() -> None:
    text = script_text("scripts/start_utility_service.sh")
    positions = [text.index(step) for step in DEMO_STARTUP_STEPS]

    assert positions == sorted(positions)
    assert positions[-1] < text.index("uvicorn utility_service.web_api.main:app")


def test_production_api_startup_script_does_not_run_migrations_or_demo_seed() -> None:
    text = script_text("scripts/start_api.sh")

    assert "uvicorn utility_service.web_api.main:app" in text
    assert "alembic" not in text
    assert "alembic upgrade head" not in text
    assert "python -m seeds." not in text
    for step in DEMO_STARTUP_STEPS:
        assert step not in text


def test_dev_up_cmd_does_not_require_host_python_or_delete_volumes() -> None:
    text = (REPO_ROOT / "infra" / "dev-up.cmd").read_text(encoding="utf-8").lower()

    assert "python" not in text
    assert "down -v" not in text
    assert "down --volumes" not in text


def test_db_tests_cmd_owns_only_dedicated_test_compose_project() -> None:
    text = (REPO_ROOT / "infra" / "db-tests.cmd").read_text(encoding="utf-8").lower()

    assert "python" not in text
    assert "geoservice-db-tests" in text
    assert "docker-compose.test.yml" in text
    assert "--abort-on-container-exit" in text
    assert "--exit-code-from backend_db_tests" in text
    assert "down -v --remove-orphans" in text
    assert "docker-compose.demo.yml" not in text
    assert "dev-up.cmd" not in text
