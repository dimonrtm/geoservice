---
title: Docker Compose Deployment
type: runbook
status: active
created: 2026-05-30
updated: 2026-11-07
source: repository-change:2026-11-07
tags: [deployment, docker-compose, postgis]
---

# Docker Compose Deployment

Репозиторий содержит Dockerfile для backend/frontend и Compose-конфигурацию в `infra/`.
Backend runtime-сервис называется `utility_service`; контейнер также имеет
`container_name: utility_service`.

## Backend Image

`apps/backend/Dockerfile` использует multi-stage:

- `base` на `python:3.12-slim`, устанавливает `gcc` и `libpq-dev`;
- `deps` устанавливает `apps/backend/requirements.txt`;
- `dev` добавляет `ruff`, `black`, `pytest` и копирует приложение;
- `prod` копирует приложение без дополнительных dev-команд.

Build context для backend: `apps/backend`.

## Frontend Image

`apps/frontend/Dockerfile` использует:

- Node 20 Alpine для install/build;
- `dev` target для `npm run dev -- --host 0.0.0.0 --port 5173`;
- `build` target для `npm run build`;
- nginx 1.27 Alpine для production static hosting.

## Compose Services

`infra/docker-compose.yml` описывает `postgis`, `migrate`, `utility_service`,
`frontend-prod` и volume `geo_pgdata`.

Production-like baseline предполагает clean PostgreSQL/PostGIS DB перед первым
`alembic upgrade head`. Старые локальные `geo_pgdata`/`infra_geo_pgdata`
volumes, созданные до переписывания destructive demo migrations, являются
disposable dev state и пересоздаются через demo/dev `down -v`; production-safe
startup не выполняет автоматический repair таких volumes.

Важные детали:

- `postgis` имеет healthcheck через `pg_isready`.
- `migrate` собирается из `../apps/backend/` и запускает `alembic upgrade head`.
- `infra/docker-compose.yml` является production-safe baseline: `utility_service`
  собирается из backend target `prod`, получает `DEV_MODE=false`, требует
  `JWT_SECRET` и DB env через `${VAR:?message}` и запускает
  `bash scripts/start_api.sh` без demo seed chain.
- `infra/docker-compose.demo.yml` является явным demo/dev layer. Он используется
  вместе с `--env-file demo.env`, переопределяет backend target на `dev`, открывает
  порты `5432`, `8000`, `5173`, подключает `frontend-dev` и запускает
  `bash scripts/start_utility_service.sh`.
- `utility_service` healthcheck дергает `http://localhost:8000/health`.
- `frontend-dev` и `frontend-prod` зависят от healthy `utility_service`.

`infra/docker-compose.full.yml` на snapshot дату пустой.

## Общий production origin для API и WebSocket

`apps/frontend/nginx.conf` подключается только в production stage Dockerfile.
nginx обслуживает статику и передаёт `/api/v1/...` внутреннему
`utility_service:8000`, сохраняя URI/query, auth/cookie и backend status.
Для WebSocket включены HTTP/1.1 и Upgrade/Connection; read timeout — 300 секунд.
API responses не кэшируются, upstream retry выключен. API access log содержит
путь без query string, поскольку ticket передаётся в URL.

`apps/frontend/src/api/baseUrl.ts` задаёт общий адрес HTTP и WebSocket. Без
`VITE_API_BASE_URL` production использует origin страницы; dev сохраняет
localhost:8000. Пустое значение означает origin страницы, относительное
разрешается относительно него. WebSocket использует тот же base с WS(S).
Сайт поддерживается в корне адреса; frontend под префиксом не является
согласованным сценарием.

Внешний компонент завершает HTTPS/WSS и передаёт запросы frontend nginx.
Base API сохраняет `DEV_MODE=false` и Secure cookie; отдельный публичный API port
не требуется. После пересоздания backend с новым IP frontend нужно перезапустить:
upstream разрешается при старте nginx. Это не сервис обнаружения backend.

Frontend context фильтруется apps/frontend/.dockerignore для всех targets:
локальные node_modules, .env/.env.*, dist и служебные артефакты исключаются.
Зависимости устанавливаются в Linux-образе. Локальный npm run dev продолжает
читать env; Docker dev получает VITE_API_BASE_URL явно из demo Compose.
Production использует существующий same-origin fallback для API.
Изоляция локальных файлов не означает побайтовую идентичность образов в разные
дни. Dev Compose не подтверждает production routing.

Проверка общего слоя и итоговой статики описана в [[../сборка/ci_and_quality]] и
[runbook INF-03](../../docs/sprint_2/2026-11-01-inf-03-frontend-build-runbook.md).
Исправление прежнего ограничения: FU-2026-11-01-001.

## Название приложения при сборке

`VITE_APP_NAME` — публичная настройка названия во вкладке, на форме входа и
в подсказке выхода. Production Compose передаёт её через `build.args` в
`ARG VITE_APP_NAME` build stage; demo Compose — в environment dev-сервера.
После изменения production требуется пересборка и замена образа, dev —
перезапуск Vite или пересоздание контейнера. Runtime environment nginx не
переименовывает готовую статику.

Vite один раз применяет trim и fallback `GeoService`. HTML title экранируется
как текст через post `transformIndexHtml`, клиент получает то же значение
через `__APP_NAME__` и `src/config/app.ts`. Язык документа всегда `ru`.
Настройка не меняет технические storage keys, API или роли. Исходники
`build/appBranding.ts` и его тест явно исключены из общего ignore `build/`.

Расхождение со старым описанием «без новых build args» устранено этим
уточнением: оно отражало состояние до добавления названия, а не запрет на
параметры сборки. Изоляция `.env` в Docker context сохранена.
Источники: `apps/frontend/vite.config.ts`, `apps/frontend/Dockerfile`,
`infra/docker-compose.yml`, `infra/docker-compose.demo.yml` и
[runbook FE-04](../../docs/sprint_2/2026-11-07-fe-04-document-language-runbook.md).

Локальный runner `docs/sprint_2/verify-inf-02.ps1` проверяет настоящий production
bundle и API в отдельном project с disposable БД, выполняет браузерный
Save/readback/Revert и отдельную legacy WebSocket-фазу. Legacy API выключен
по умолчанию; включение в проверке не меняет эту политику. Проверка на localhost
с Secure cookie не подтверждает TLS внешнего deployment. Детали —
[runbook](../../docs/sprint_2/2026-10-26-inf-02-production-api-routing-runbook.md).

## Связанные Ноды

- [[../dev_setup/local_development]]
- [[../сборка/ci_and_quality]]
- [[../архитектура/backend]]
