# Изоляция DB-тестов от demo-БД — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Перенести весь набор `RUN_DB_TESTS=1` в отдельный disposable PostgreSQL/PostGIS и сделать ошибочный запуск против demo-БД fail-closed до первого SQL-запроса.

**Architecture:** Standalone Compose-проект `geoservice-db-tests` поднимает только `postgis_test` на `tmpfs` и одноразовый `backend_db_tests`. Pytest bootstrap валидирует `TEST_DATABASE_URL`, переключает процесс с application `DATABASE_URL` на test-БД, применяет Alembic и только затем начинает collection; CI сравнивает read-only fingerprint demo-БД до и после isolated run.

**Tech Stack:** Python 3.12, pytest, SQLAlchemy URL API, Alembic, PostgreSQL 16, PostGIS 3.4, Docker Compose, Windows Batch, GitHub Actions.

## Global Constraints

- Весь `RUN_DB_TESTS=1`, включая migration- и concurrency-тесты, выполняется только в отдельной БД `geo_test`.
- `postgis_test` не публикует ports, не подключается к `infra_default`, не использует named volume и хранит PostgreSQL data directory в `tmpfs`.
- `TEST_DATABASE_URL` обязателен, должен использовать PostgreSQL-compatible scheme, указывать на БД с суффиксом `_test` и не совпадать с исходным `DATABASE_URL`.
- URL переключается до Alembic, collection и любого SQL-доступа.
- `infra/db-tests.cmd` зависит от Docker Compose, но не от host Python.
- `infra/dev-up.cmd`, production startup и текущая demo-БД не изменяют поведение; отсутствующая `EditVersion` не восстанавливается.
- Ошибки guard не печатают пароль или полный URL.
- Не выполнять `git add`, `git commit` или `git push`; каждый task заканчивается unstaged reviewer checkpoint.

---

## File Structure

- Create: `apps/backend/tests/db_test_isolation.py` — чистая проверка и безопасное переключение environment для DB-тестов.
- Create: `apps/backend/tests/test_db_test_isolation.py` — unit/subprocess regression tests fail-closed поведения.
- Modify: `apps/backend/conftest.py` — ранний pytest bootstrap и Alembic upgrade только после успешного guard.
- Create: `infra/docker-compose.test.yml` — standalone disposable PostGIS и backend DB test runner.
- Create: `infra/db-tests.cmd` — Windows lifecycle test Compose-проекта с сохранением exit code.
- Modify: `apps/backend/tests/test_compose_security_contract.py` — contract test физической Compose-изоляции.
- Modify: `apps/backend/tests/test_compose_startup_contract.py` — contract test Windows entrypoint и независимости `dev-up.cmd`.
- Create: `apps/backend/tests/test_ci_db_test_isolation_contract.py` — запрет старого CI-вызова и обязательный demo fingerprint.
- Modify: `.github/workflows/ci.yml` — единый isolated DB-run и сравнение fingerprint.
- Modify: `README.md` — безопасная локальная команда DB-тестов и fail-closed правило.
- Modify: `docs/agent-memory/bugfixes/2026-06-28-ci-smoke-401-seed-cleanup.md` — исправить устаревшее правило о destructive cleanup в общей demo-БД.
- Modify: `docs/agent-memory/file-map.md` — добавить новые точки входа DB test isolation.

---

### Task 1: Fail-closed URL guard и ранний Alembic bootstrap

**Files:**
- Create: `apps/backend/tests/db_test_isolation.py`
- Create: `apps/backend/tests/test_db_test_isolation.py`
- Modify: `apps/backend/conftest.py`

**Interfaces:**
- Produces: `DatabaseTestIsolationError(RuntimeError)`.
- Produces: `configure_db_test_environment(environ: MutableMapping[str, str]) -> str | None`.
- Consumes: `RUN_DB_TESTS`, `DATABASE_URL`, `TEST_DATABASE_URL`.
- Postcondition: при успешном DB-mode `environ["DATABASE_URL"]` содержит validated `TEST_DATABASE_URL`.

- [ ] **Step 1: Написать failing unit tests URL guard**

Добавить проверки:

```python
def test_non_db_run_does_not_change_database_url() -> None:
    environ = {"DATABASE_URL": "postgresql+asyncpg://u:p@demo/geo"}
    assert configure_db_test_environment(environ) is None
    assert environ["DATABASE_URL"].endswith("/geo")


def test_db_run_requires_test_database_url() -> None:
    environ = {
        "RUN_DB_TESTS": "1",
        "DATABASE_URL": "postgresql+asyncpg://u:secret@demo/geo",
    }
    with pytest.raises(DatabaseTestIsolationError, match="TEST_DATABASE_URL is required"):
        configure_db_test_environment(environ)


@pytest.mark.parametrize(
    "test_url, message",
    [
        ("postgresql+asyncpg://u:p@demo/geo", "must differ"),
        ("postgresql+asyncpg://u:p@test/geo", "must end with '_test'"),
        ("sqlite:///geo_test", "PostgreSQL"),
    ],
)
def test_db_run_rejects_unsafe_test_url(test_url: str, message: str) -> None:
    environ = {
        "RUN_DB_TESTS": "1",
        "DATABASE_URL": "postgresql+asyncpg://u:p@demo/geo",
        "TEST_DATABASE_URL": test_url,
    }
    with pytest.raises(DatabaseTestIsolationError, match=message):
        configure_db_test_environment(environ)


def test_db_run_switches_database_url_after_validation() -> None:
    test_url = "postgresql+asyncpg://u:p@postgis_test/geo_test"
    environ = {
        "RUN_DB_TESTS": "1",
        "DATABASE_URL": "postgresql+asyncpg://u:p@demo/geo",
        "TEST_DATABASE_URL": test_url,
    }
    assert configure_db_test_environment(environ) == test_url
    assert environ["DATABASE_URL"] == test_url
```

Добавить отдельную проверку, что сообщение для malformed URL не содержит
`secret-password` или исходный URL целиком.

- [ ] **Step 2: Запустить tests и подтвердить RED**

Run из `apps/backend`:

```powershell
python -m pytest tests/test_db_test_isolation.py -q
```

Expected: FAIL при import отсутствующего `tests.db_test_isolation`.

- [ ] **Step 3: Реализовать минимальный pure guard**

Использовать `sqlalchemy.engine.make_url`; сравнивать нормализованные `URL`, а в
ошибках упоминать только environment variable и безопасное имя базы:

```python
class DatabaseTestIsolationError(RuntimeError):
    pass


def configure_db_test_environment(
    environ: MutableMapping[str, str],
) -> str | None:
    if environ.get("RUN_DB_TESTS") != "1":
        return None
    test_url_value = environ.get("TEST_DATABASE_URL")
    if not test_url_value:
        raise DatabaseTestIsolationError(
            "RUN_DB_TESTS=1 requires TEST_DATABASE_URL."
        )
    try:
        test_url = make_url(test_url_value)
    except ArgumentError as exc:
        raise DatabaseTestIsolationError("TEST_DATABASE_URL is malformed.") from exc
    if not test_url.drivername.startswith("postgresql"):
        raise DatabaseTestIsolationError("TEST_DATABASE_URL must use PostgreSQL.")
    if not test_url.database or not test_url.database.endswith("_test"):
        raise DatabaseTestIsolationError(
            "TEST_DATABASE_URL database name must end with '_test'."
        )
    application_url_value = environ.get("DATABASE_URL")
    if application_url_value:
        try:
            application_url = make_url(application_url_value)
        except ArgumentError as exc:
            raise DatabaseTestIsolationError("DATABASE_URL is malformed.") from exc
        if application_url == test_url:
            raise DatabaseTestIsolationError(
                "TEST_DATABASE_URL must differ from DATABASE_URL."
            )
    environ["DATABASE_URL"] = test_url_value
    return test_url_value
```

- [ ] **Step 4: Подключить guard и Alembic к pytest bootstrap**

В `apps/backend/conftest.py` после определения `APP_ROOT` добавить hook:

```python
def pytest_configure(config) -> None:
    try:
        configured_url = configure_db_test_environment(os.environ)
    except DatabaseTestIsolationError as exc:
        raise pytest.UsageError(str(exc)) from exc
    if configured_url is None:
        return
    alembic_config = Config(str(APP_ROOT / "alembic.ini"))
    command.upgrade(alembic_config, "head")
```

Imports `pytest`, `alembic.command`, `alembic.config.Config` и guard module не
должны инициировать SQL сами по себе. `command.upgrade` вызывается строго после
переключения `DATABASE_URL`.

- [ ] **Step 5: Добавить subprocess regression test старого опасного запуска**

Запустить child pytest с `RUN_DB_TESTS=1`, application URL с hostname
`must-not-connect.invalid` и без `TEST_DATABASE_URL`. Assert:

- exit code ненулевой;
- output содержит `TEST_DATABASE_URL`;
- output не содержит `could not translate host`, `connection refused` или пароль.

- [ ] **Step 6: Подтвердить GREEN и отсутствие регрессий**

```powershell
python -m pytest tests/test_db_test_isolation.py -q
python -m pytest --collect-only -q
```

Expected: guard tests PASS; обычная collection не запускает Alembic.

- [ ] **Step 7: Reviewer checkpoint**

Проверить `git diff --check` для трёх файлов. Не stage/commit.

---

### Task 2: Disposable test Compose и Windows entrypoint

**Files:**
- Create: `infra/docker-compose.test.yml`
- Create: `infra/db-tests.cmd`
- Modify: `apps/backend/tests/test_compose_security_contract.py`
- Modify: `apps/backend/tests/test_compose_startup_contract.py`

**Interfaces:**
- Consumes: bootstrap Task 1 через `RUN_DB_TESTS=1` и `TEST_DATABASE_URL`.
- Produces: Compose services `postgis_test`, `backend_db_tests`.
- Produces: host entrypoint `infra/db-tests.cmd`.

- [ ] **Step 1: Написать failing Compose contract tests**

В security contract проверить:

```python
def test_db_test_compose_is_physically_isolated_and_disposable() -> None:
    compose = read_infra_file("docker-compose.test.yml")
    postgis_test = service_block(compose, "postgis_test")
    runner = service_block(compose, "backend_db_tests")

    assert "tmpfs:" in postgis_test
    assert "/var/lib/postgresql/data" in postgis_test
    assert "ports:" not in postgis_test
    assert "\nvolumes:" not in compose
    assert "geo_pgdata" not in compose
    assert "postgis_test:5432/geo_test" in runner
    assert 'RUN_DB_TESTS: "1"' in runner
    assert "postgis:" not in runner
    assert "infra_default" not in compose
```

В startup contract проверить, что `db-tests.cmd` содержит
`geoservice-db-tests`, только `docker-compose.test.yml`,
`--abort-on-container-exit`, `--exit-code-from backend_db_tests`, cleanup
`down -v`, не содержит `python`, `docker-compose.demo.yml` или вызов
`dev-up.cmd`. Существующий test `dev-up.cmd` должен продолжить запрещать
`down -v`.

- [ ] **Step 2: Запустить contract tests и подтвердить RED**

```powershell
python -m pytest tests/test_compose_security_contract.py tests/test_compose_startup_contract.py -q
```

Expected: FAIL, потому что test Compose и `.cmd` ещё отсутствуют.

- [ ] **Step 3: Создать standalone `docker-compose.test.yml`**

Минимальная структура:

```yaml
services:
  postgis_test:
    image: postgis/postgis:16-3.4
    environment:
      POSTGRES_DB: geo_test
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    tmpfs:
      - /var/lib/postgresql/data
    volumes:
      - ./docker/postgis/init:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d geo_test"]
      interval: 2s
      timeout: 3s
      retries: 30

  backend_db_tests:
    build:
      context: ../apps/backend/
      dockerfile: Dockerfile
      target: dev
    environment:
      RUN_DB_TESTS: "1"
      TEST_DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgis_test:5432/geo_test
      DEV_MODE: "true"
      JWT_SECRET: isolated-db-tests-secret-not-for-production
    depends_on:
      postgis_test:
        condition: service_healthy
    command: ["python", "-m", "pytest", "tests/integration_tests", "--tb=short"]
```

Top-level `volumes:` и external networks не добавлять.

- [ ] **Step 4: Создать robust `db-tests.cmd`**

Использовать `pushd "%~dp0"`, project name `geoservice-db-tests` и labels для
cleanup. Сохранить отдельно test и cleanup exit codes; при падении тестов вернуть
test exit code, при успешных тестах и упавшем cleanup вернуть cleanup exit code.
Команды cleanup обязаны указывать одновременно `-p geoservice-db-tests` и
`-f docker-compose.test.yml`, чтобы `down -v` не мог затронуть demo-проект.

- [ ] **Step 5: Подтвердить GREEN и валидный Compose config**

```powershell
python -m pytest tests/test_compose_security_contract.py tests/test_compose_startup_contract.py -q
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml config --quiet
```

Expected: PASS, Compose exit code 0.

- [ ] **Step 6: Reviewer checkpoint**

Проверить, что `git diff -- infra/dev-up.cmd apps/backend/scripts/start_api.sh`
пуст и новые файлы не имеют whitespace errors. Не stage/commit.

---

### Task 3: CI переключение и demo fingerprint

**Files:**
- Create: `apps/backend/tests/test_ci_db_test_isolation_contract.py`
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: `infra/docker-compose.test.yml` из Task 2.
- Produces: один isolated DB test step и read-only fingerprint comparison.

- [ ] **Step 1: Написать failing CI contract**

Тест читает `.github/workflows/ci.yml` и проверяет:

```python
assert "exec -T utility_service env RUN_DB_TESTS=1" not in workflow
assert "docker-compose.test.yml" in workflow
assert "geoservice-db-tests" in workflow
assert "--exit-code-from backend_db_tests" in workflow
assert "DEMO_FINGERPRINT_BEFORE" in workflow
assert "DEMO_FINGERPRINT_AFTER" in workflow
assert 'if [ "$DEMO_FINGERPRINT_BEFORE" != "$DEMO_FINGERPRINT_AFTER" ]' in workflow
```

Также проверить наличие `if: always()` cleanup test Compose-проекта.

- [ ] **Step 2: Запустить test и подтвердить RED**

```powershell
python -m pytest tests/test_ci_db_test_isolation_contract.py -q
```

Expected: FAIL на старом вызове `exec utility_service ... RUN_DB_TESTS=1`.

- [ ] **Step 3: Заменить CI DB step**

Перед isolated run получить read-only fingerprint через demo `postgis`:

```sql
SELECT 'work_order|' || w.id || '|' || w.status
FROM work_order.work_orders w WHERE w.code = 'WO-001'
UNION ALL
SELECT 'default_state|' || ds.id || '|' || ds.work_order_id
FROM utility_network.default_states ds
JOIN work_order.work_orders w ON w.id = ds.work_order_id
WHERE w.code = 'WO-001'
UNION ALL
SELECT 'edit_version|' || ev.id || '|' || ev.status
FROM work_order.edit_versions ev
JOIN work_order.work_orders w ON w.id = ev.work_order_id
WHERE w.code = 'WO-001'
ORDER BY 1;
```

Затем выполнить:

```bash
docker compose -p geoservice-db-tests -f docker-compose.test.yml up \
  --build --abort-on-container-exit --exit-code-from backend_db_tests
```

Сохранить exit code без преждевременного выхода shell, повторить fingerprint и
сначала проверить equality. При mismatch завершиться ошибкой независимо от
pytest status; иначе вернуть pytest status.

- [ ] **Step 4: Добавить unconditional CI cleanup**

Отдельный step с `if: always()`:

```bash
docker compose -p geoservice-db-tests -f docker-compose.test.yml \
  down -v --remove-orphans
```

Demo shutdown остаётся отдельным существующим шагом.

- [ ] **Step 5: Подтвердить GREEN и YAML contract**

```powershell
python -m pytest tests/test_ci_db_test_isolation_contract.py -q
python -m pytest tests/test_compose_security_contract.py tests/test_compose_startup_contract.py -q
```

Expected: PASS; опасный marker отсутствует.

- [ ] **Step 6: Reviewer checkpoint**

Проверить diff CI только на DB step/cleanup и отсутствие изменения API smoke.
Не stage/commit.

---

### Task 4: Реальный isolated DB-run и доказательство неизменности demo-БД

**Files:**
- Modify only if a test exposes a defect in Tasks 1-3; любое исправление сначала получает failing regression test.

**Interfaces:**
- Consumes: `infra/db-tests.cmd`, test Compose и bootstrap.
- Produces: verification evidence для полного `RUN_DB_TESTS=1`.

- [ ] **Step 1: Снять read-only fingerprint текущей demo-БД**

Через `docker exec geo-postgis psql -At` выполнить согласованный UNION query и
сохранить вывод вне репозитория. Не создавать `EditVersion` и не менять строки.

- [ ] **Step 2: Запустить Windows entrypoint**

```powershell
infra\db-tests.cmd
```

Expected: Alembic применяется к `postgis_test/geo_test`, весь
`tests/integration_tests` проходит, test Compose удаляется.

- [ ] **Step 3: Проверить отсутствие test resources**

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml ps -a
docker volume ls --filter label=com.docker.compose.project=geoservice-db-tests
```

Expected: нет containers и volumes test-проекта.

- [ ] **Step 4: Повторить demo fingerprint**

Выполнить тот же read-only query. Expected: байт-в-байт совпадает с Step 1;
`WO-001` остаётся `assigned`, а count `EditVersion` остаётся 0.

- [ ] **Step 5: Проверить fail-closed старый вызов без SQL**

В одноразовом backend container запустить pytest с `RUN_DB_TESTS=1`, но без
`TEST_DATABASE_URL` и с недоступным application hostname. Expected: immediate
configuration error о `TEST_DATABASE_URL`, без connection error.

- [ ] **Step 6: Reviewer checkpoint**

Если реальный run выявил дефект, вернуться к RED-GREEN в соответствующем Task.
Не менять demo-БД для «починки» verification.

---

### Task 5: Документация, durable memory и полная проверка

**Files:**
- Modify: `README.md`
- Modify: `docs/agent-memory/bugfixes/2026-06-28-ci-smoke-401-seed-cleanup.md`
- Modify: `docs/agent-memory/file-map.md`

**Interfaces:**
- Consumes: окончательные команды и гарантии Tasks 1-4.
- Produces: безопасный runbook и исправленное долговременное правило.

- [ ] **Step 1: Обновить README**

Зафиксировать:

- локальный DB-run выполняется только через `infra\db-tests.cmd`;
- host Python не требуется;
- `RUN_DB_TESTS=1` с application/demo URL запрещён fail-closed guard;
- test data disposable, `dev-up.cmd` и `infra_geo_pgdata` не затрагиваются;
- текущая demo `EditVersion` автоматически не восстанавливается.

- [ ] **Step 2: Исправить существующую memory entry**

Не создавать дубликат. В существующей bugfix entry добавить второй root cause:
committed concurrency cleanup восстановил demo users и seed chain, но удалил
пользовательскую `EditVersion`. Новое устойчивое правило — destructive DB tests
работают только в dedicated disposable PostGIS; cleanup общей demo-БД больше не
считается допустимой изоляцией.

- [ ] **Step 3: Обновить file-map**

К существующей строке DB integration seed cleanup добавить:

```text
infra/docker-compose.test.yml, infra/db-tests.cmd,
apps/backend/tests/db_test_isolation.py
```

- [ ] **Step 4: Запустить documentation/memory checks**

```powershell
python scripts/check-memory-needed.py --check
git diff --check
rg -n -i "TBD|TODO|FIXME" README.md docs/agent-memory/bugfixes/2026-06-28-ci-smoke-401-seed-cleanup.md docs/superpowers/specs/2026-08-03-db-test-isolation-design.md
```

Host Python shim недоступен в текущем окружении; `check-memory-needed.py`
запустить внутри backend image с bind mount либо явно зафиксировать blocker.

- [ ] **Step 5: Полный backend regression**

В backend dev image с bind-mounted рабочим деревом:

```powershell
python -m pytest --tb=short
ruff check .
black --check .
```

Expected: все non-DB tests PASS, DB tests без `RUN_DB_TESTS=1` SKIP, ruff/black
PASS.

- [ ] **Step 6: Повторный isolated DB regression**

Повторить `infra\db-tests.cmd`, затем ещё раз подтвердить неизменность demo
fingerprint и отсутствие test resources.

- [ ] **Step 7: Финальный audit**

```powershell
git status --short
git diff --check
git diff --cached --name-only
git diff -- infra/dev-up.cmd apps/backend/scripts/start_api.sh
```

Expected: staged list пуст; protected files без diff; все изменения остаются
unstaged для пользовательского review.

- [ ] **Step 8: Reviewer checkpoint**

Сообщить итоговые test counts, Compose isolation proof, demo fingerprint equality
и единственные оставшиеся warnings/blockers. Не stage/commit/push.
