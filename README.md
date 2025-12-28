# Описание
MVP GeoService: загрузка GeoJSON, хранение и отображение геоданных на карте, базовое совместное редактирование. Backend: Python/FastAPI + PostGIS. Frontend: TypeScript/Vue + MapLibre.

## Требования
Node, Python, Docker Desktop/WSL2

## Быстрый старт (Dev)

## Конфигурация (.env)

## Структура репозитория
apps/
  backend/
    app/
      api/
      services/
      repositories/
      core/
      models/
    tests/
    pyproject.toml
    README.md
  frontend/
    src/
      ui/
      state/
      maplayer/
      apiclient/
      assets/
      styles/
    index.html
    package.json
    vite.config.ts
infra/
  docker/
    postgis/
      init/
  docker-compose.yml
  .env.example
docs/
  user-stories/
  adr/
packages/
  shared/
    schemas/

## Скрипты и команды
