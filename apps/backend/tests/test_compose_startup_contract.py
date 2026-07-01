from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
STARTUP_SEEDS = (
    "python -m seeds.runners.seed_demo_users",
    "python -m seeds.runners.seed_utility_dataset",
    "python -m seeds.runners.seed_work_orders",
)


def script_text(relative_path: str) -> str:
    return (BACKEND_ROOT / relative_path).read_text(encoding="utf-8")


def test_demo_startup_script_runs_all_seed_runners_before_api() -> None:
    text = script_text("scripts/start_utility_service.sh")
    positions = [text.index(seed) for seed in STARTUP_SEEDS]

    assert positions == sorted(positions)
    assert positions[-1] < text.index("uvicorn utility_service.web_api.main:app")


def test_production_api_startup_script_does_not_run_migrations_or_demo_seed() -> None:
    text = script_text("scripts/start_api.sh")

    assert "uvicorn utility_service.web_api.main:app" in text
    assert "alembic" not in text
    assert "alembic upgrade head" not in text
    assert "python -m seeds." not in text
    for seed in STARTUP_SEEDS:
        assert seed not in text
