import os
from pathlib import Path
import sys

from alembic import command
from alembic.config import Config
import pytest


os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
)
os.environ.setdefault("DEV_MODE", "true")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")

APP_ROOT = Path(__file__).resolve().parent

if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from tests.db_test_isolation import (  # noqa: E402
    DatabaseTestIsolationError,
    configure_db_test_environment,
)


def pytest_configure(config: pytest.Config) -> None:
    try:
        configured_url = configure_db_test_environment(os.environ)
    except DatabaseTestIsolationError as exc:
        raise pytest.UsageError(str(exc)) from exc

    if configured_url is None:
        return

    alembic_config = Config(str(APP_ROOT / "alembic.ini"))
    command.upgrade(alembic_config, "head")
