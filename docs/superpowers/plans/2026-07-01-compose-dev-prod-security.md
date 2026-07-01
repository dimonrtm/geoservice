# Compose Dev/Prod Security Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Git commit checkpoints in this repository are informational: do not run `git add` or `git commit` unless the user explicitly asks for commits.

**Goal:** Разделить production-safe compose baseline и явный demo/dev запуск, убрать `/api/v1/auth/dev-login`, сохранить demo login через `/api/v1/auth/login`.

**Architecture:** `infra/docker-compose.yml` становится безопасным baseline с `target: prod`, `DEV_MODE=false` и required env placeholders. Demo/dev поведение живет в `infra/docker-compose.demo.yml` и `infra/demo.env`, потому что Docker Compose интерполирует required-переменные базового файла до merge overlay-файлов. Backend auth surface сокращается до password login и `/me`.

**Tech Stack:** Docker Compose, FastAPI, Pydantic Settings, pytest, GitHub Actions, Vue/Vite docs references.

---

## Scope Check

Spec охватывает один связанный subsystem: runtime/auth startup boundary. Работу не нужно дробить на отдельные specs, потому что каждый task ниже дает проверяемый инкремент внутри одной цели: убрать небезопасный default path и сохранить demo workflow.

## File Structure

- Modify: `apps/backend/utility_service/web_api/api/auth.py`
  - Удаляет import `DevLoginIn` и conditional route `/dev-login`.
- Modify: `apps/backend/utility_service/use_cases/services/auth_service.py`
  - Удаляет `get_dev_user()` и import `DevLoginIn`; оставляет только password login и user lookup.
- Delete: `apps/backend/utility_service/use_cases/schemas/auth/dev_login_in.py`
  - Устаревшая schema для удаляемого endpoint.
- Modify: `apps/backend/utility_service/web_api/tests/test_auth_api.py`
  - Добавляет contract test, что `/api/v1/auth/dev-login` не зарегистрирован.
- Modify: `apps/backend/utility_service/use_cases/tests/test_auth_service.py`
  - Добавляет guard test, что `AuthService` не содержит passwordless dev-user path.
- Modify: `apps/backend/utility_service/utils/tests/test_settings.py`
  - Переименовывает dev-mode test так, чтобы он больше не подразумевал dev-login.
- Create: `apps/backend/scripts/start_api.sh`
  - Production-safe startup command: только запуск API, без migrations и seed.
- Modify: `apps/backend/tests/test_compose_startup_contract.py`
  - Разделяет contract для demo startup script и production API script.
- Create: `apps/backend/tests/test_compose_security_contract.py`
  - Text-level regression tests для compose/env split без зависимости от PyYAML.
- Modify: `infra/docker-compose.yml`
  - Production-safe baseline, required env placeholders, `target: prod`, no demo seed command.
- Create: `infra/docker-compose.demo.yml`
  - Явный demo/dev layer: dev target, ports, frontend-dev, demo startup command.
- Create: `infra/demo.env`
  - Public demo-only env values for local/CI demo compose interpolation.
- Delete: `infra/docker-compose.override.yml`
  - Убирает auto-loaded override, чтобы `docker compose` не получал скрытый dev layer.
- Modify: `infra/.env.example`
  - Production/local private env template без реальных секретов.
- Modify: `infra/dev-up.cmd`
  - Запускает demo compose явно.
- Modify: `infra/ci-up.cmd`
  - Запускает demo compose явно.
- Modify: `scripts/dev.cmd`
  - Делает root helper для demo startup или оставляет короткий redirect в `infra`.
- Modify: `.github/workflows/ci.yml`
  - Переводит smoke на demo compose и добавляет production-safe compose config guards.
- Modify: `README.md`
  - Разделяет demo quick start и production-safe baseline.
- Modify: `docs/project-description.md`
  - Убирает устаревшее описание dev-login.
- Modify: `apps/frontend/README.md`
  - Убирает `VITE_ENABLE_DEV_AUTH`, если frontend больше не имеет dev auth panel.
- Modify: `Code_wiki/dev_setup/local_development.md`
  - Новая demo команда и demo env.
- Modify: `Code_wiki/deployment/docker_compose.md`
  - Production-safe baseline vs demo layer.
- Modify: `Code_wiki/архитектура/backend.md`
  - Удаляет утверждение, что `/api/v1/auth/dev-login` регистрируется при `DEV_MODE`.
- Modify: `Code_wiki/архитектура/api_and_realtime.md`
  - Auth API содержит только `/login` и `/me`.

## Implementation Note: Compose Interpolation

Нельзя рассчитывать, что `infra/docker-compose.demo.yml` переопределит required-переменные из `infra/docker-compose.yml`: Compose интерполирует `${VAR:?message}` в каждом файле до merge. Поэтому demo-команда использует `--env-file demo.env`, где лежат явно public demo-only значения. Production-safe baseline при этом остается required-by-default.

---

### Task 1: Удалить Backend Dev-Login Surface

**Files:**
- Modify: `apps/backend/utility_service/web_api/tests/test_auth_api.py`
- Modify: `apps/backend/utility_service/use_cases/tests/test_auth_service.py`
- Modify: `apps/backend/utility_service/utils/tests/test_settings.py`
- Modify: `apps/backend/utility_service/web_api/api/auth.py`
- Modify: `apps/backend/utility_service/use_cases/services/auth_service.py`
- Delete: `apps/backend/utility_service/use_cases/schemas/auth/dev_login_in.py`

- [ ] **Step 1: Write failing API route test**

Append this test to `apps/backend/utility_service/web_api/tests/test_auth_api.py`:

```python
def test_dev_login_route_is_not_registered() -> None:
    auth_service = AsyncMock()

    response = TestClient(build_auth_app(auth_service)).post(
        "/api/v1/auth/dev-login",
        json={"email": "new@example.local", "role": "editor"},
    )

    assert response.status_code == 404
    assert not auth_service.mock_calls
```

- [ ] **Step 2: Write failing service guard test**

Append this test to `apps/backend/utility_service/use_cases/tests/test_auth_service.py`:

```python
def test_auth_service_has_no_passwordless_dev_user_path() -> None:
    assert not hasattr(AuthService, "get_dev_user")
```

- [ ] **Step 3: Update settings test name and assertion language**

In `apps/backend/utility_service/utils/tests/test_settings.py`, replace
`test_settings_allow_dev_mode_with_local_secret` with this test:

```python
def test_settings_allow_dev_mode_with_explicit_local_runtime_marker() -> None:
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
        DEV_MODE=True,
        JWT_SECRET="CHANGE_ME_IN_ENV",
    )

    assert settings.dev_auth_enabled is True
```

This keeps current settings behavior but removes the implication that `DEV_MODE`
means a dev-login route exists.

- [ ] **Step 4: Run backend auth tests and verify red**

Run from `apps/backend`:

```powershell
pytest utility_service/web_api/tests/test_auth_api.py::test_dev_login_route_is_not_registered utility_service/use_cases/tests/test_auth_service.py::test_auth_service_has_no_passwordless_dev_user_path utility_service/utils/tests/test_settings.py -q
```

Expected before implementation:

```text
FAILED ... test_dev_login_route_is_not_registered ... assert 200 == 404
FAILED ... test_auth_service_has_no_passwordless_dev_user_path ... assert not True
```

- [ ] **Step 5: Remove dev-login route and schema import**

In `apps/backend/utility_service/web_api/api/auth.py`, remove this import:

```python
from utility_service.use_cases.schemas.auth.dev_login_in import DevLoginIn
```

Remove this route block entirely:

```python
if settings.dev_auth_enabled:

    @auth_router.post("/dev-login")
    async def dev_login(
        body: DevLoginIn, auth_service: AuthService = Depends(get_auth_service)
    ) -> dict[str, Any]:
        user = await auth_service.get_dev_user(body)
        token = create_access_token(str(user.id), _role_value(user))
        return {"access_token": token, "token_type": "bearer"}
```

Keep `/login` and `/me` unchanged.

- [ ] **Step 6: Remove passwordless service path**

In `apps/backend/utility_service/use_cases/services/auth_service.py`, remove this import:

```python
from utility_service.use_cases.schemas.auth.dev_login_in import DevLoginIn
```

Remove this method from `AuthService`:

```python
async def get_dev_user(self, body: DevLoginIn) -> User:
    async with self.session.begin():
        user = await self.user_repository.get_by_email(body.email)
        if not user:
            user = await self.user_repository.create_user(
                email=body.email, role=body.role, password_hash=None
            )
        return user
```

- [ ] **Step 7: Delete obsolete schema file**

Delete `apps/backend/utility_service/use_cases/schemas/auth/dev_login_in.py`.

- [ ] **Step 8: Run focused backend auth tests and verify green**

Run from `apps/backend`:

```powershell
pytest utility_service/web_api/tests/test_auth_api.py utility_service/use_cases/tests/test_auth_service.py utility_service/utils/tests/test_settings.py -q
```

Expected:

```text
... passed
```

- [ ] **Step 9: Commit checkpoint**

Do not run this unless the user explicitly asked for commits:

```bash
git add apps/backend/utility_service/web_api/api/auth.py apps/backend/utility_service/web_api/tests/test_auth_api.py apps/backend/utility_service/use_cases/services/auth_service.py apps/backend/utility_service/use_cases/tests/test_auth_service.py apps/backend/utility_service/utils/tests/test_settings.py apps/backend/utility_service/use_cases/schemas/auth/dev_login_in.py
git commit -m "fix: remove dev login endpoint"
```

---

### Task 2: Разделить Startup Scripts И Contract Tests

**Files:**
- Create: `apps/backend/scripts/start_api.sh`
- Modify: `apps/backend/tests/test_compose_startup_contract.py`

- [ ] **Step 1: Write failing startup contract tests**

Replace `apps/backend/tests/test_compose_startup_contract.py` with:

```python
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
    assert "alembic upgrade head" not in text
    for seed in STARTUP_SEEDS:
        assert seed not in text
```

- [ ] **Step 2: Run startup contract tests and verify red**

Run from `apps/backend`:

```powershell
pytest tests/test_compose_startup_contract.py -q
```

Expected before implementation:

```text
FAILED ... FileNotFoundError ... scripts/start_api.sh
```

- [ ] **Step 3: Create production API startup script**

Create `apps/backend/scripts/start_api.sh`:

```sh
set -euo pipefail

uvicorn utility_service.web_api.main:app --host 0.0.0.0 --port 8000
```

- [ ] **Step 4: Run startup contract tests and verify green**

Run from `apps/backend`:

```powershell
pytest tests/test_compose_startup_contract.py -q
```

Expected:

```text
2 passed
```

- [ ] **Step 5: Commit checkpoint**

Do not run this unless the user explicitly asked for commits:

```bash
git add apps/backend/scripts/start_api.sh apps/backend/tests/test_compose_startup_contract.py
git commit -m "fix: split demo and api startup scripts"
```

---

### Task 3: Add Compose Security Contract Tests

**Files:**
- Create: `apps/backend/tests/test_compose_security_contract.py`

- [ ] **Step 1: Write failing compose contract tests**

Create `apps/backend/tests/test_compose_security_contract.py`:

```python
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INFRA_ROOT = REPO_ROOT / "infra"


def read_infra_file(filename: str) -> str:
    return (INFRA_ROOT / filename).read_text(encoding="utf-8")


def test_base_compose_uses_required_production_safe_env() -> None:
    compose = read_infra_file("docker-compose.yml")

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
    assert 'DEV_MODE: "true"' not in compose
    assert "DEV_MODE: ${DEV_MODE-true}" not in compose
    assert "target: prod" in compose
    assert "bash scripts/start_api.sh" in compose
    assert "bash scripts/start_utility_service.sh" not in compose


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
```

- [ ] **Step 2: Run compose contract tests and verify red**

Run from `apps/backend`:

```powershell
pytest tests/test_compose_security_contract.py -q
```

Expected before implementation:

```text
FAILED ... test_base_compose_uses_required_production_safe_env
FAILED ... FileNotFoundError ... docker-compose.demo.yml
FAILED ... FileNotFoundError ... demo.env
FAILED ... docker-compose.override.yml exists
```

- [ ] **Step 3: Commit checkpoint**

Do not run this unless the user explicitly asked for commits:

```bash
git add apps/backend/tests/test_compose_security_contract.py
git commit -m "test: add compose security contracts"
```

---

### Task 4: Implement Production-Safe Compose And Demo Layer

**Files:**
- Modify: `infra/docker-compose.yml`
- Create: `infra/docker-compose.demo.yml`
- Create: `infra/demo.env`
- Delete: `infra/docker-compose.override.yml`
- Modify: `infra/.env.example`
- Modify: `infra/dev-up.cmd`
- Modify: `infra/ci-up.cmd`
- Modify: `scripts/dev.cmd`

- [ ] **Step 1: Replace base compose with production-safe baseline**

Replace `infra/docker-compose.yml` with:

```yaml
services:
  postgis:
    image: postgis/postgis:16-3.4
    container_name: geo-postgis
    environment:
      POSTGRES_DB: ${DB_NAME:?DB_NAME is required}
      POSTGRES_USER: ${DB_USER:?DB_USER is required}
      POSTGRES_PASSWORD: ${DB_PASSWORD:?DB_PASSWORD is required}
    volumes:
      - geo_pgdata:/var/lib/postgresql/data
      - ./docker/postgis/init:/docker-entrypoint-initdb.d/
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:?DB_USER is required} -d ${DB_NAME:?DB_NAME is required}"]
      interval: 5s
      timeout: 3s
      retries: 20
    restart: unless-stopped

  migrate:
    build:
      context: ../apps/backend/
      dockerfile: Dockerfile
      target: prod
    depends_on:
      postgis:
        condition: service_healthy
    environment:
      DATABASE_URL: ${DATABASE_URL:?DATABASE_URL is required}
    command: ["bash", "-lc", "set -euo pipefail; alembic upgrade head"]
    restart: no
    profiles: ["migrate"]

  utility_service:
    container_name: utility_service
    build:
      context: ../apps/backend/
      dockerfile: Dockerfile
      target: prod
    environment:
      DATABASE_URL: ${DATABASE_URL:?DATABASE_URL is required}
      DEV_MODE: "false"
      JWT_SECRET: ${JWT_SECRET:?JWT_SECRET is required}
      JWT_ALG: ${JWT_ALG:-HS256}
      ACCESS_TOKEN_TTL_MIN: ${ACCESS_TOKEN_TTL_MIN:-30}
      CORS_ORIGINS: ${CORS_ORIGINS:-http://localhost:8080,http://127.0.0.1:8080}
      HOST: 0.0.0.0
      PORT: 8000
    command:
      [
        "bash",
        "-lc",
        "bash scripts/start_api.sh"
      ]
    depends_on:
      postgis:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=2)\""]
      interval: 20s
      timeout: 3s
      retries: 10
      start_period: 10s
    restart: unless-stopped

  frontend-prod:
    build:
      context: ../apps/frontend/
      dockerfile: Dockerfile
      target: prod
    ports:
      - "8080:80"
    depends_on:
      utility_service:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "wget -qO- http://127.0.0.1/ >/dev/null || exit 1"]
      interval: 20s
      timeout: 3s
      retries: 10
      start_period: 10s
    restart: unless-stopped
    profiles: ["prod"]

volumes:
  geo_pgdata:
```

- [ ] **Step 2: Create explicit demo compose layer**

Create `infra/docker-compose.demo.yml`:

```yaml
services:
  postgis:
    ports:
      - "5432:5432"

  utility_service:
    build:
      target: dev
    environment:
      DEV_MODE: "true"
      CORS_ORIGINS: http://localhost:5173,http://127.0.0.1:5173
    command:
      [
        "bash",
        "-lc",
        "bash scripts/start_utility_service.sh"
      ]
    ports:
      - "8000:8000"

  frontend-dev:
    build:
      context: ../apps/frontend/
      dockerfile: Dockerfile
      target: dev
    environment:
      - VITE_API_BASE_URL=http://localhost:8000
    ports:
      - "5173:5173"
    depends_on:
      utility_service:
        condition: service_healthy
    healthcheck:
      test:
        [
          "CMD-SHELL",
          "node -e \"const http=require('http');const req=http.get('http://127.0.0.1:5173',res=>process.exit(res.statusCode>=200&&res.statusCode<400?0:1));req.on('error',()=>process.exit(1));\""
        ]
      interval: 20s
      timeout: 3s
      retries: 10
      start_period: 30s
    restart: unless-stopped
    profiles: ["dev"]
```

- [ ] **Step 3: Create demo env file for compose interpolation**

Create `infra/demo.env`:

```dotenv
# DEMO ONLY. Public local values for GeoService demo/dev compose.
# Do not reuse these values for production or shared environments.

DB_NAME=geo
DB_USER=postgres
DB_PASSWORD=postgres
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgis:5432/geo

JWT_SECRET=local-demo-jwt-secret-not-for-production
JWT_ALG=HS256
ACCESS_TOKEN_TTL_MIN=30
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

- [ ] **Step 4: Delete auto-loaded override**

Delete `infra/docker-compose.override.yml`. This is intentional: a committed
override file is loaded automatically by `docker compose` and would make the
baseline less explicit.

- [ ] **Step 5: Replace production env example**

Replace `infra/.env.example` with:

```dotenv
# Copy to infra/.env for private local/runtime values.
# Do not commit infra/.env or any real secrets.

DB_NAME=geo
DB_USER=postgres
DB_PASSWORD=change-this-database-password
DATABASE_URL=postgresql+asyncpg://postgres:change-this-database-password@postgis:5432/geo

JWT_SECRET=replace-with-a-long-random-secret
JWT_ALG=HS256
ACCESS_TOKEN_TTL_MIN=30
CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080
```

- [ ] **Step 6: Update local demo command helpers**

Replace `infra/dev-up.cmd` with:

```bat
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml --profile dev down
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml --profile dev up -d --build
pause
```

Replace `infra/ci-up.cmd` with:

```bat
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml up -d --build postgis utility_service
```

Replace `scripts/dev.cmd` with:

```bat
@echo off
pushd "%~dp0..\infra"
call dev-up.cmd
popd
```

- [ ] **Step 7: Run compose contract tests and verify green**

Run from `apps/backend`:

```powershell
pytest tests/test_compose_security_contract.py tests/test_compose_startup_contract.py -q
```

Expected:

```text
6 passed
```

- [ ] **Step 8: Run Docker Compose config checks**

Run from `infra`.

Negative production-safe check:

```powershell
docker compose -f docker-compose.yml config
```

Expected without `.env` or shell env:

```text
JWT_SECRET is required
```

If local `infra/.env` exists, temporarily rename it manually before this check
and restore it after the check. Do not delete the file.

Positive production-safe check:

```powershell
$env:DB_NAME="geo"; $env:DB_USER="postgres"; $env:DB_PASSWORD="postgres"; $env:DATABASE_URL="postgresql+asyncpg://postgres:postgres@postgis:5432/geo"; $env:JWT_SECRET="test-only-secret-for-compose-config"; docker compose -f docker-compose.yml config --quiet
```

Expected:

```text
no output, exit code 0
```

Demo config check:

```powershell
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml --profile dev config --quiet
```

Expected:

```text
no output, exit code 0
```

- [ ] **Step 9: Commit checkpoint**

Do not run this unless the user explicitly asked for commits:

```bash
git add infra/docker-compose.yml infra/docker-compose.demo.yml infra/demo.env infra/.env.example infra/dev-up.cmd infra/ci-up.cmd scripts/dev.cmd infra/docker-compose.override.yml apps/backend/tests/test_compose_security_contract.py
git commit -m "fix: split demo and production compose defaults"
```

---

### Task 5: Update CI Smoke And Compose Guards

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Update compose smoke startup command**

In `.github/workflows/ci.yml`, in job `smoke_test`, replace every command shaped like:

```bash
docker compose -f docker-compose.yml ...
```

with:

```bash
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml ...
```

For example, the startup block becomes:

```yaml
      - name: Start postgis + utility_service (demo compose)
        working-directory: infra
        run: |
          docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml up -d --build postgis utility_service
          docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml ps
```

The cleanup block becomes:

```yaml
      - name: Shutdown compose
        if: always()
        working-directory: infra
        run: docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml down -v
```

- [ ] **Step 2: Add production-safe compose config guard step**

Add this step before `Start postgis + utility_service (demo compose)`:

```yaml
      - name: Compose production-safe config guards
        working-directory: infra
        env:
          DB_NAME: geo
          DB_USER: postgres
          DB_PASSWORD: postgres
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgis:5432/geo
          JWT_SECRET: ci-compose-config-secret
        run: |
          docker compose -f docker-compose.yml config --quiet
          docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml --profile dev config --quiet
```

- [ ] **Step 3: Add negative required-env check**

Add this step before the positive config guard:

```yaml
      - name: Compose production-safe config rejects missing env
        working-directory: infra
        run: |
          if docker compose -f docker-compose.yml config >/tmp/base-compose.out 2>/tmp/base-compose.err; then
            echo "Expected production-safe compose config to fail without required env"
            cat /tmp/base-compose.out
            exit 1
          fi
          cat /tmp/base-compose.err
          grep -E "DB_NAME is required|DATABASE_URL is required|JWT_SECRET is required" /tmp/base-compose.err
```

- [ ] **Step 4: Run workflow text checks locally**

Run from repository root:

```powershell
rg -n "docker compose -f docker-compose.yml" .github\workflows\ci.yml
```

Expected:

```text
no output
```

Run:

```powershell
rg -n "docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml" .github\workflows\ci.yml
```

Expected: multiple matches in `smoke_test`.

- [ ] **Step 5: Commit checkpoint**

Do not run this unless the user explicitly asked for commits:

```bash
git add .github/workflows/ci.yml
git commit -m "ci: run smoke on explicit demo compose"
```

---

### Task 6: Update Documentation And Wiki

**Files:**
- Modify: `README.md`
- Modify: `docs/project-description.md`
- Modify: `apps/frontend/README.md`
- Modify: `Code_wiki/dev_setup/local_development.md`
- Modify: `Code_wiki/deployment/docker_compose.md`
- Modify: `Code_wiki/архитектура/backend.md`
- Modify: `Code_wiki/архитектура/api_and_realtime.md`

- [ ] **Step 1: Update README quick start**

In `README.md`, replace the current compose quick start command with:

```markdown
### Demo login через Docker Compose

Локальный demo/dev запуск выполняется явно через demo env и demo compose layer:

```bash
cd infra
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml --profile dev up --build
```
```

In the configuration section, replace bullets about `DEV_MODE` and
`VITE_ENABLE_DEV_AUTH` with:

```markdown
Важно:

- production-safe `infra/docker-compose.yml` требует `JWT_SECRET` и DB env через окружение или `infra/.env`;
- `infra/demo.env` содержит public demo-only значения для локального сценария;
- `DEV_MODE` больше не включает `/api/v1/auth/dev-login`;
- `VITE_API_BASE_URL` задаёт базовый URL API для frontend.
```

- [ ] **Step 2: Update project description**

In `docs/project-description.md`, replace the old dev-login flow sentence:

```markdown
1. пользователь получает токен через dev-login;
```

with:

```markdown
1. пользователь получает токен через `POST /api/v1/auth/login`;
```

- [ ] **Step 3: Update frontend README**

In `apps/frontend/README.md`, remove the line:

```markdown
- `VITE_ENABLE_DEV_AUTH` — показывает или скрывает dev auth panel
```

If the file has a frontend env list, make sure it contains:

```markdown
- `VITE_API_BASE_URL` — базовый URL backend API.
```

- [ ] **Step 4: Update local development Code_wiki node**

In `Code_wiki/dev_setup/local_development.md`, replace the dev compose command with:

```markdown
```powershell
cd infra
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml --profile dev up --build
```
```

In the variables section, state:

```markdown
`infra/demo.env` содержит public demo-only значения для локального запуска.
Production-safe `infra/docker-compose.yml` требует `DB_NAME`, `DB_USER`,
`DB_PASSWORD`, `DATABASE_URL` и `JWT_SECRET` через private `.env`, shell
environment или CI secrets.
```

- [ ] **Step 5: Update Docker Compose deployment Code_wiki node**

In `Code_wiki/deployment/docker_compose.md`, update Compose Services details so
it says:

```markdown
`infra/docker-compose.yml` является production-safe baseline: `utility_service`
собирается из backend target `prod`, получает `DEV_MODE=false`, требует
`JWT_SECRET` и DB env через `${VAR:?message}` и запускает
`bash scripts/start_api.sh` без demo seed chain.

`infra/docker-compose.demo.yml` является явным demo/dev layer. Он используется
вместе с `--env-file demo.env`, переопределяет backend target на `dev`, открывает
порты `5432`, `8000`, `5173`, подключает `frontend-dev` и запускает
`bash scripts/start_utility_service.sh`.
```

- [ ] **Step 6: Update backend architecture Code_wiki node**

In `Code_wiki/архитектура/backend.md`, replace the auth configuration block:

```markdown
- `/api/v1/auth/dev-login` регистрируется только при включенном `DEV_MODE`.
```

with:

```markdown
- `/api/v1/auth/dev-login` удален; пользовательский вход поддерживается через
  `/api/v1/auth/login` и `/api/v1/auth/me`.
```

- [ ] **Step 7: Update API contracts Code_wiki node**

In `Code_wiki/архитектура/api_and_realtime.md`, remove:

```markdown
- `POST /api/v1/auth/dev-login` доступен только при `DEV_MODE=true`.
```

The Auth API section should contain exactly these auth endpoint bullets:

```markdown
- `POST /api/v1/auth/login` принимает email/password и возвращает `access_token`, `token_type` и user DTO.
- `GET /api/v1/auth/me` возвращает текущего пользователя по Bearer token.
```

- [ ] **Step 8: Run documentation search**

Run from repository root:

```powershell
rg -n "dev-login|VITE_ENABLE_DEV_AUTH|POST /api/v1/auth/dev-login" README.md docs apps Code_wiki
```

Expected:

```text
Only historical sprint/review/spec/plan documents may match. Active README, Code_wiki architecture/runbook nodes, frontend README, and docs/project-description.md must not describe dev-login as an available workflow.
```

- [ ] **Step 9: Commit checkpoint**

Do not run this unless the user explicitly asked for commits:

```bash
git add README.md docs/project-description.md apps/frontend/README.md Code_wiki/dev_setup/local_development.md Code_wiki/deployment/docker_compose.md Code_wiki/архитектура/backend.md Code_wiki/архитектура/api_and_realtime.md
git commit -m "docs: document explicit demo compose startup"
```

---

### Task 7: Final Verification And Knowledge Hygiene

**Files:**
- Inspect: `docs/agent-memory/protocol.md`
- Inspect or update only if justified: `docs/agent-memory/file-map.md`
- No code changes unless verification reveals a concrete failure.

- [ ] **Step 1: Run backend focused tests**

Run from `apps/backend`:

```powershell
pytest utility_service/web_api/tests/test_auth_api.py utility_service/use_cases/tests/test_auth_service.py utility_service/utils/tests/test_settings.py tests/test_compose_startup_contract.py tests/test_compose_security_contract.py -q
```

Expected:

```text
all selected tests passed
```

- [ ] **Step 2: Run full backend test suite**

Run from `apps/backend`:

```powershell
pytest
```

Expected:

```text
all tests passed
```

- [ ] **Step 3: Run static checks if backend image/tools are available locally**

Run from `apps/backend`:

```powershell
ruff check .
black --check .
```

Expected:

```text
All checks passed
All done!
```

- [ ] **Step 4: Run compose config verification**

Run from `infra`:

```powershell
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml --profile dev config --quiet
```

Expected:

```text
no output, exit code 0
```

Run with production test env from PowerShell:

```powershell
$env:DB_NAME="geo"; $env:DB_USER="postgres"; $env:DB_PASSWORD="postgres"; $env:DATABASE_URL="postgresql+asyncpg://postgres:postgres@postgis:5432/geo"; $env:JWT_SECRET="test-only-secret-for-compose-config"; docker compose -f docker-compose.yml config --quiet
```

Expected:

```text
no output, exit code 0
```

- [ ] **Step 5: Optional live demo smoke**

Run this only when Docker is available and the user is comfortable with containers:

```powershell
cd infra
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml --profile dev up -d --build postgis utility_service
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml exec -T utility_service python tests/smoke/full_path_workspace_smoke.py
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml down -v
```

Expected:

```text
full path workspace smoke prints its success marker and exits 0
```

- [ ] **Step 6: Decide whether memory needs update**

Per `docs/agent-memory/protocol.md`, create/update memory only if the work
produces durable knowledge not already preserved by the design spec, plan,
Code_wiki, runbooks, or code. For this task, likely no new `docs/agent-memory`
entry is needed because the design spec and Code_wiki nodes preserve the
decision and file relationships.

If `docs/agent-memory/file-map.md` still points only to removed
`infra/docker-compose.override.yml` for local dev, update the existing Infra
line to include:

```markdown
- docker compose local dev: `infra/docker-compose.yml`, `infra/docker-compose.demo.yml`, `infra/demo.env`, `infra/dev-up.cmd`, `scripts/dev.cmd`
```

- [ ] **Step 7: Final git status summary**

Run from repository root:

```powershell
git status --short
```

Expected:

```text
Only files intentionally touched by this plan are listed.
```

- [ ] **Step 8: Commit checkpoint**

Do not run this unless the user explicitly asked for commits:

```bash
git add docs/agent-memory/file-map.md
git commit -m "docs: update compose memory file map"
```

Run this checkpoint only if `docs/agent-memory/file-map.md` was actually changed.

---

## Plan Self-Review

- Spec coverage:
  - Production-safe base compose: Tasks 3, 4, 5, 7.
  - Explicit demo/dev compose: Tasks 3, 4, 5, 6, 7.
  - Delete `/api/v1/auth/dev-login`: Task 1 and docs cleanup in Task 6.
  - Preserve demo login through `/api/v1/auth/login`: Tasks 4, 5, 6, 7.
  - Required env placeholders without real committed production secrets: Tasks 3, 4, 5.
  - CI smoke and config guards: Task 5.
  - Code_wiki and README updates in Russian: Task 6.
- Placeholder scan:
  - No placeholder markers or delayed-implementation instructions.
  - Each code-changing step includes concrete code or exact replacement text.
- Type/name consistency:
  - `AuthService.get_dev_user` is removed in tests and implementation.
  - `docker-compose.demo.yml`, `demo.env`, and `start_api.sh` names are consistent across tests, scripts, CI, and docs.
  - Compose command always uses `--env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml` for demo.
