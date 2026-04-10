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
  project-problems-and-solutions.md
  project-required-improvements.md
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

## Конфигурация

Backend-конфигурация централизована в [settings.py](C:/Repositories/geoservice/apps/backend/app/core/settings.py).

Важно:

- `DEV_MODE` управляет доступностью dev-login на backend;
- `VITE_ENABLE_DEV_AUTH` управляет отображением dev auth panel на frontend;
- `VITE_API_BASE_URL` задаёт базовый URL API для frontend.

## Документация

В `docs/` сейчас лежат рабочие документы по анализу проекта:

- [project-description.md](C:/Repositories/geoservice/docs/project-description.md)
- [project-problems-and-solutions.md](C:/Repositories/geoservice/docs/project-problems-and-solutions.md)
- [project-required-improvements.md](C:/Repositories/geoservice/docs/project-required-improvements.md)
