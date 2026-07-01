from pathlib import Path


# tests/... is under apps/backend, so parents[3] is the repository root.
REPO_ROOT = Path(__file__).resolve().parents[3]
INFRA_ROOT = REPO_ROOT / "infra"


def read_infra_file(filename: str) -> str:
    return (INFRA_ROOT / filename).read_text(encoding="utf-8")


def service_block(compose: str, service_name: str) -> str:
    service_header = f"  {service_name}:"
    lines = compose.splitlines()
    start = None

    for index, line in enumerate(lines):
        if line == service_header:
            start = index
            break

    assert start is not None, f"service {service_name!r} not found"

    block_lines = [lines[start]]
    for line in lines[start + 1 :]:
        if line.startswith("  ") and not line.startswith("    ") and line.strip():
            break
        block_lines.append(line)

    return "\n".join(block_lines)


def test_base_compose_uses_required_production_safe_env() -> None:
    compose = read_infra_file("docker-compose.yml")
    utility_service = service_block(compose, "utility_service")

    required_markers = (
        "${DB_NAME:?",
        "${DB_USER:?",
        "${DB_PASSWORD:?",
        "${DATABASE_URL:?",
        "${JWT_SECRET:?",
    )
    for marker in required_markers:
        assert marker in compose

    assert "CHANGE_ME_IN_ENV" not in compose
    for forbidden in (
        'DEV_MODE: "true"',
        "DEV_MODE: true",
        "DEV_MODE=true",
        "${DEV_MODE-true}",
        "${DEV_MODE:-true}",
    ):
        assert forbidden not in compose

    assert "target: prod" in utility_service
    assert "target: dev" not in utility_service
    assert "bash scripts/start_api.sh" in utility_service
    assert "bash scripts/start_utility_service.sh" not in utility_service


def test_demo_compose_keeps_demo_startup_and_dev_target_explicit() -> None:
    demo = read_infra_file("docker-compose.demo.yml")

    assert "target: dev" in demo
    assert 'DEV_MODE: "true"' in demo
    assert "bash scripts/start_utility_service.sh" in demo
    assert "frontend-dev:" in demo
    assert '"8000:8000"' in demo
    assert '"5173:5173"' in demo


def test_demo_env_is_explicitly_demo_only() -> None:
    demo_env = read_infra_file("demo.env")

    assert "DEMO ONLY" in demo_env
    assert "JWT_SECRET=local-demo-jwt-secret-not-for-production" in demo_env
    assert "DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgis:5432/geo" in demo_env


def test_auto_loaded_override_file_is_not_present() -> None:
    assert not (INFRA_ROOT / "docker-compose.override.yml").exists()
