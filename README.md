# GeoService

GeoService — экспериментальный MVP для работы с геоданными.

Сейчас проект умеет:

- хранить геообъекты в PostGIS;
- отдавать слои и объекты через FastAPI;
- отображать данные на карте через Vue + MapLibre;
- поддерживать базовое редактирование полигонов на клиенте.

## Стек

- Backend: Python, FastAPI, SQLAlchemy, Alembic, PostGIS
- Frontend: Vue 3, TypeScript, Pinia, Vite, MapLibre
- Infra: Docker Compose

## Структура репозитория

```text
apps/
  backend/
    app/
      alembic/
      api/
      core/
      db/
      domain/
      models/
      repositories/
      schemas/
      services/
      tests/
  frontend/
    src/
      api/
      assets/
      components/
      composables/
      config/
      map/
      parsing/
      stores/
docs/
  project-description.md
  requirements/
    action-plan.md
    requirements-compliance-audit.md
    sprints/
infra/
scripts/
```

## Быстрый старт

Основной локальный сценарий завязан на Docker Compose из `infra/`.

Что нужно:

- Python 3.12+
- Node 20+
- Docker Desktop / WSL2

Полезные точки входа:

- frontend scripts: [package.json](C:/Repositories/geoservice/apps/frontend/package.json)
- infra compose: [docker-compose.yml](C:/Repositories/geoservice/infra/docker-compose.yml)
- backend app entry: [main.py](C:/Repositories/geoservice/apps/backend/app/main.py)

### Demo login через Docker Compose

Backend при старте теперь делает:

1. `alembic upgrade head`
2. idempotent seed demo-пользователей
3. запуск `uvicorn`

Запуск:

```bash
cd infra
docker compose --profile dev up --build
```

Demo credentials:

- `editor@example.com` / `editor-password`
- `viewer@example.com` / `viewer-password`

Проверка login flow:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login -H "Content-Type: application/json" -d "{\"email\":\"editor@example.com\",\"password\":\"editor-password\"}"
```

После получения `access_token` можно проверить сессию:

```bash
curl http://localhost:8000/api/v1/auth/me -H "Authorization: Bearer <access_token>"
```

Повторный запуск backend не должен создавать дубликаты demo-пользователей: seed приводит записи к ожидаемому baseline по роли и паролю и не требует `dev-login` для локального demo-сценария.

## Конфигурация

Backend-конфигурация централизована в [settings.py](C:/Repositories/geoservice/apps/backend/app/core/settings.py).

Важно:

- `DEV_MODE` управляет доступностью dev-login на backend;
- `VITE_ENABLE_DEV_AUTH` управляет отображением dev auth panel на frontend;
- `VITE_API_BASE_URL` задаёт базовый URL API для frontend.

## Документация

В `docs/` сейчас лежат рабочие документы по анализу проекта и планированию:

- [project-description.md](C:/Repositories/geoservice/docs/project-description.md)
- [agent-memory](docs/agent-memory/README.md)
- [project knowledge wiki](C:/Repositories/geoservice/index.md)
- [knowledge pipeline runbook](C:/Repositories/geoservice/docs/knowledge-pipeline/README.md)
- [action-plan.md](C:/Repositories/geoservice/docs/requirements/action-plan.md)
- [requirements-compliance-audit.md](C:/Repositories/geoservice/docs/requirements/requirements-compliance-audit.md)
- [sprint-1-plan.md](C:/Repositories/geoservice/docs/requirements/sprints/sprint-1/sprint-1-plan.md)

## Project Knowledge Wiki

Knowledge wiki lives in `RAW_inputs/`, `Vision_wiki/`, `Code_wiki/`, `memory/`, and `Общие_принципы/`. Human-readable wiki content is written in Russian. Obsidian graph configuration is stored in `.obsidian/`.

Use `/ingest repository-snapshot` to add already existing unchanged repository knowledge to `Code_wiki`. After the full implementation plan or a major repository task is complete, the agent should run `/ingest repository-change` before the final report. Pre-commit does not run or check repository-change ingest.
