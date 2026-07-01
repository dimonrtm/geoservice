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
