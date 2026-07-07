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

Локальный demo/dev запуск выполняется явно через demo env и demo compose layer:

```bash
cd infra
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml --profile dev up --build
```

Перед первым запуском ветки с production-like migration baseline пересоздайте
старый disposable Postgres volume. Старые demo/dev volumes с уже примененными
Alembic revisions не являются поддерживаемым migration path:

```bash
cd infra
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml down -v
```

После этого запустите demo/dev compose снова. Команда удаляет локальные данные
Postgres и предназначена только для disposable demo/dev БД.

Если после смены demo env `utility_service` становится unhealthy, а в логах
есть `password authentication failed for user "postgres"`, локальный Docker
volume `infra_geo_pgdata` был создан с другим паролем. Для disposable demo DB
пересоздайте его командой выше и затем повторите запуск.

Demo credentials:

- `alexey.editor@example.local` / `alexey-editor-password`
- `bolat.editor@example.local` / `bolat-editor-password`
- `marina.reviewer@example.local` / `marina-reviewer-password`

`Editor` видит существующую основу карты и editor workspace. `Reviewer` видит
отдельную страницу роли без editor workspace; reviewer queue будет добавлена
в следующем спринте. Legacy credentials `viewer@example.com` удалены.

Проверка login flow:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login -H "Content-Type: application/json" -d "{\"email\":\"alexey.editor@example.local\",\"password\":\"alexey-editor-password\"}"
```

После получения `access_token` можно проверить сессию:

```bash
curl http://localhost:8000/api/v1/auth/me -H "Authorization: Bearer <access_token>"
```

Повторный запуск backend не должен создавать дубликаты demo-пользователей:
существующий `seed_demo_users.py` приводит записи к ожидаемому baseline по
стабильному ID, роли, паролю и active status и не требует `dev-login` для
локального demo-сценария.

## Конфигурация

Backend-конфигурация централизована в [settings.py](C:/Repositories/geoservice/apps/backend/app/core/settings.py).

Важно:

- production-safe `infra/docker-compose.yml` требует `JWT_SECRET` и DB env через окружение или `infra/.env`;
- `infra/demo.env` содержит public demo-only значения для локального сценария;
- `DEV_MODE` больше не включает `/api/v1/auth/dev-login`;
- `VITE_API_BASE_URL` задаёт базовый URL API для frontend.

## Документация

В `docs/` сейчас лежат рабочие документы по анализу проекта и планированию:

- [project-description.md](C:/Repositories/geoservice/docs/project-description.md)
- [agent-memory](docs/agent-memory/README.md)
- [project knowledge wiki](C:/Repositories/geoservice/index.md)
- [knowledge pipeline runbook](C:/Repositories/geoservice/docs/knowledge-pipeline/README.md)
- [action-plan.md](C:/Repositories/geoservice/docs/requirements/action-plan.md)
- [requirements-compliance-audit.md](C:/Repositories/geoservice/docs/requirements/requirements-compliance-audit.md)
- [Документы текущего Спринта 1](C:/Repositories/geoservice/docs/sprint_1/README.md)
- [Исторический generic-план Спринта 1](C:/Repositories/geoservice/docs/sprint_1/legacy-generic-plan/sprint-1-plan.md)

## Project Knowledge Wiki

Knowledge wiki lives in `RAW_inputs/`, `Vision_wiki/`, `Code_wiki/`, `memory/`, and `Общие_принципы/`. Human-readable wiki content is written in Russian. Obsidian graph configuration is stored in `.obsidian/`.

Use `/ingest repository-snapshot` to add already existing unchanged repository knowledge to `Code_wiki`. After the full implementation plan or a major repository task is complete, the agent should run `/ingest repository-change` before the final report. Pre-commit does not run or check repository-change ingest.
