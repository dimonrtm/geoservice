# Frontend

Frontend GeoService собран на `Vue 3 + TypeScript + Vite`.

Основные зоны кода:

- `src/components` — UI-компоненты страницы и карты;
- `src/composables` — orchestration-логика карты и загрузки данных;
- `src/map` — map/render helper-ы и геометрические преобразования;
- `src/api` — HTTP-клиент и вызовы backend API;
- `src/stores` — Pinia stores;
- `src/config` — frontend feature flags и конфигурация.

## Команды

- `npm run dev`
- `npm run lint`
- `npm run typecheck`
- `npm run format:check`
- `npm run build`

## Переменные окружения

- `VITE_API_BASE_URL` — базовый URL backend API.

При локальном `npm run dev` Vite читает `.env` и `.env.local`, включая
mode-specific варианты. Эти файлы не нужно удалять перед Docker-сборкой.

Docker targets `dev` и `prod` используют `apps/frontend/.dockerignore`:
локальные `node_modules`, env-файлы (включая `.env.example`), результаты сборки
и служебные артефакты не попадают в общий сборочный слой. Зависимости
устанавливаются внутри Linux-образа.

Для Docker dev настройки передаются явно при запуске. В
`infra/docker-compose.demo.yml` уже задан
`VITE_API_BASE_URL=http://localhost:8000`. Production использует origin сайта:
nginx передаёт `/api/v1/` backend. Изменение environment готового nginx-контейнера
не изменяет собранный JavaScript; production build args для API не предусмотрены.

CI проверяет изоляцию реальной сборкой с искусственными локальными файлами.
Команды локального запуска и ограничения — в
[runbook INF-03](../../docs/sprint_2/2026-11-01-inf-03-frontend-build-runbook.md).
