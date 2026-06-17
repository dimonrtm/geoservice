from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
STARTUP_SEEDS = (
    "python -m seeds.runners.seed_demo_users",
    "python -m seeds.runners.seed_utility_dataset",
    "python -m seeds.runners.seed_work_orders",
)


def _compose_text(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_utility_service_startup_runs_all_seed_runners_before_api() -> None:
    for compose_path in ("infra/docker-compose.yml", "infra/docker-compose.override.yml"):
        command_text = _compose_text(compose_path)
        positions = [command_text.index(seed) for seed in STARTUP_SEEDS]

        assert positions == sorted(positions), compose_path
        assert positions[-1] < command_text.index(
            "uvicorn utility_service.web_api.main:app"
        ), compose_path
