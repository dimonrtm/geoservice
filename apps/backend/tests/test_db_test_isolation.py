import os
from pathlib import Path
import subprocess
import sys

import pytest

from tests.db_test_isolation import (
    DatabaseTestIsolationError,
    configure_db_test_environment,
)


BACKEND_ROOT = Path(__file__).resolve().parents[1]
APPLICATION_DATABASE_URL = "postgresql+asyncpg://app:password@postgis/geo"
SAFE_TEST_DATABASE_URL = "postgresql+asyncpg://tester:password@postgis_test/geo_test"


def test_non_db_run_does_not_change_database_url() -> None:
    environ = {"DATABASE_URL": APPLICATION_DATABASE_URL}

    assert configure_db_test_environment(environ) is None
    assert environ["DATABASE_URL"] == APPLICATION_DATABASE_URL


def test_db_run_requires_test_database_url() -> None:
    environ = {
        "RUN_DB_TESTS": "1",
        "DATABASE_URL": APPLICATION_DATABASE_URL,
    }

    with pytest.raises(
        DatabaseTestIsolationError,
        match="RUN_DB_TESTS=1 requires TEST_DATABASE_URL",
    ):
        configure_db_test_environment(environ)

    assert environ["DATABASE_URL"] == APPLICATION_DATABASE_URL


@pytest.mark.parametrize(
    ("application_url", "test_url", "message"),
    [
        (
            SAFE_TEST_DATABASE_URL,
            SAFE_TEST_DATABASE_URL,
            "must differ from DATABASE_URL",
        ),
        (
            APPLICATION_DATABASE_URL,
            "postgresql+asyncpg://tester:password@postgis_test/geo",
            "database name must end with '_test'",
        ),
        (APPLICATION_DATABASE_URL, "sqlite:///geo_test", "must use PostgreSQL"),
    ],
)
def test_db_run_rejects_unsafe_test_url(
    application_url: str,
    test_url: str,
    message: str,
) -> None:
    environ = {
        "RUN_DB_TESTS": "1",
        "DATABASE_URL": application_url,
        "TEST_DATABASE_URL": test_url,
    }

    with pytest.raises(DatabaseTestIsolationError, match=message):
        configure_db_test_environment(environ)

    assert environ["DATABASE_URL"] == application_url


def test_db_run_rejects_malformed_url_without_exposing_credentials() -> None:
    secret = "secret-password"
    environ = {
        "RUN_DB_TESTS": "1",
        "DATABASE_URL": APPLICATION_DATABASE_URL,
        "TEST_DATABASE_URL": f"not-a-url-{secret}",
    }

    with pytest.raises(DatabaseTestIsolationError) as captured:
        configure_db_test_environment(environ)

    message = str(captured.value)
    assert "TEST_DATABASE_URL is malformed" in message
    assert secret not in message
    assert environ["TEST_DATABASE_URL"] not in message
    assert environ["DATABASE_URL"] == APPLICATION_DATABASE_URL


def test_db_run_switches_database_url_after_validation() -> None:
    environ = {
        "RUN_DB_TESTS": "1",
        "DATABASE_URL": APPLICATION_DATABASE_URL,
        "TEST_DATABASE_URL": SAFE_TEST_DATABASE_URL,
    }

    assert configure_db_test_environment(environ) == SAFE_TEST_DATABASE_URL
    assert environ["DATABASE_URL"] == SAFE_TEST_DATABASE_URL


def test_pytest_bootstrap_rejects_missing_test_url_before_connection() -> None:
    secret = "must-not-leak"
    environ = os.environ.copy()
    environ["RUN_DB_TESTS"] = "1"
    environ["DATABASE_URL"] = f"postgresql+asyncpg://tester:{secret}@must-not-connect.invalid/geo"
    environ.pop("TEST_DATABASE_URL", None)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "utility_service/utils/tests/test_settings.py",
            "-q",
        ],
        cwd=BACKEND_ROOT,
        env=environ,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )

    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "TEST_DATABASE_URL" in output
    assert "could not translate host" not in output.lower()
    assert "connection refused" not in output.lower()
    assert secret not in output
