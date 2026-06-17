from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
STARTUP_SEEDS = (
    "python -m seeds.runners.seed_demo_users",
    "python -m seeds.runners.seed_utility_dataset",
    "python -m seeds.runners.seed_work_orders",
)


def test_utility_service_startup_script_runs_all_seed_runners_before_api() -> None:
    script_text = (BACKEND_ROOT / "scripts" / "start_utility_service.sh").read_text(
        encoding="utf-8"
    )
    positions = [script_text.index(seed) for seed in STARTUP_SEEDS]

    assert positions == sorted(positions)
    assert positions[-1] < script_text.index("uvicorn utility_service.web_api.main:app")
