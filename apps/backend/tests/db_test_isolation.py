from collections.abc import MutableMapping

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


class DatabaseTestIsolationError(RuntimeError):
    pass


def configure_db_test_environment(
    environ: MutableMapping[str, str],
) -> str | None:
    if environ.get("RUN_DB_TESTS") != "1":
        return None

    test_url_value = environ.get("TEST_DATABASE_URL")
    if not test_url_value:
        raise DatabaseTestIsolationError("RUN_DB_TESTS=1 requires TEST_DATABASE_URL.")

    try:
        test_url = make_url(test_url_value)
    except ArgumentError as exc:
        raise DatabaseTestIsolationError("TEST_DATABASE_URL is malformed.") from exc

    if not test_url.drivername.startswith("postgresql"):
        raise DatabaseTestIsolationError("TEST_DATABASE_URL must use PostgreSQL.")
    if not test_url.database or not test_url.database.endswith("_test"):
        raise DatabaseTestIsolationError("TEST_DATABASE_URL database name must end with '_test'.")

    application_url_value = environ.get("DATABASE_URL")
    if application_url_value:
        try:
            application_url = make_url(application_url_value)
        except ArgumentError as exc:
            raise DatabaseTestIsolationError("DATABASE_URL is malformed.") from exc
        if application_url == test_url:
            raise DatabaseTestIsolationError("TEST_DATABASE_URL must differ from DATABASE_URL.")

    environ["DATABASE_URL"] = test_url_value
    return test_url_value
