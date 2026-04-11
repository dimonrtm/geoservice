# Спринт 1 на 14 дней: закрытие MVP-gap’ов по realtime, auth и integration tests

## Summary

- По коду проект уже имеет рабочие `JWT`, роли `viewer/editor`, защищённые CRUD-эндпойнты, tile-cache и клиентские хуки для локального обновления карты, но у него нет production-login, WebSocket realtime и integration-покрытия.
- Цель спринта 1: сделать воспроизводимый demo-сценарий “два клиента редактируют один слой”, где вход идёт не через `dev-login`, изменения прилетают почти сразу, а auth/protected CRUD защищены интеграционными тестами и CI.
- Вне scope этого спринта: create-flow новой feature через UI, frontend-редактирование всех geometry types, history/audit, аналитика, сущность `Project`.

## Публичные контракты и архитектурные решения

- Добавить `POST /api/v1/auth/login` с `email + password`, ответом `access_token`, `token_type`, `user{id,email,role}`.
- Оставить `GET /api/v1/auth/me`, но нормализовать его под тот же пользовательский контракт, чтобы frontend мог восстанавливать сессию.
- Оставить `POST /api/v1/auth/dev-login` только при `DEV_MODE=true`; dev-панель не удалять, а ограничить dev-сценарием.
- WebSocket сделать через `WS /api/v1/ws/layers/{layer_id}?token=<jwt>`; подписка идёт на один слой на соединение.
- События WebSocket фиксировать в формате:
  - `feature_created` и `feature_updated`: полный `feature` + `layerId` + `eventId` + `occurredAt`
  - `feature_deleted`: `featureId` + `layerId` + `eventId` + `occurredAt`
- Публикацию realtime-событий делать после успешного коммита CRUD-операции в backend service-слое через отдельный publisher/connection manager.
- В production-режиме запретить запуск backend с дефолтным `JWT_SECRET`; refresh token в спринт 1 не включать.
- Для demo/local окружения добавить явный seed-поток предсозданных пользователей с email/password, чтобы login был воспроизводим через `docker-compose`.

## План по дням

1. День 1: зафиксировать contracts спринта 1. Описать login/WS/event payload, reconnect-поведение, out-of-scope спринта и DoD в `docs/`.
2. День 2: усилить backend auth-конфигурацию. Добавить валидацию `JWT_SECRET`, подготовить login-схемы, сервис проверки пароля и политику разделения `dev-login` и normal login.
3. День 3: реализовать backend login flow. Добавить поиск пользователя с `password_hash`, проверку пароля, выдачу JWT, нормализованный `/me`, негативные ответы `401`.
4. День 4: добавить seed demo-пользователей для compose/demo-сценария и обновить запуск, чтобы локально можно было войти без `dev-login`.
5. День 5: внедрить frontend login flow. Отрисовывать login-экран при отсутствии токена, хранить пользователя в auth-store, оставить dev-auth panel только под `VITE_ENABLE_DEV_AUTH`.
6. День 6: подготовить backend realtime-ядро. Добавить websocket-router, JWT-аутентификацию сокета, connection manager по `layer_id`, lifecycle-хуки на connect/disconnect.
7. День 7: встроить публикацию realtime-событий в create/update/delete feature и гарантировать, что событие уходит только после успешного коммита.
8. День 8: реализовать frontend WebSocket client для активного слоя, обработку reconnect/backoff и принудительный `reloadFeatures(..., force=true)` после восстановления соединения.
9. День 9: связать входящие WS-события с существующим tile-cache. Для `create/update` использовать `upsert + invalidate/reload`, для `delete` — `remove + sync`, без полной перезагрузки приложения.
10. День 10: покрыть frontend unit-тестами auth-store/login-flow и обработчик realtime-событий, включая идемпотентность повторной доставки.
11. День 11: добавить backend integration-тесты на auth. Проверить успешный login, неверный пароль, `401` без токена, `403` для `viewer` на mutate-операциях.
12. День 12: добавить backend integration-тесты на protected CRUD и realtime. Проверить `editor` create/update/delete, публикацию `feature_created|updated|deleted`, базовый сценарий двух клиентов.
13. День 13: встроить integration-suite в CI, обновить compose/demo-документацию, прогнать demo-checklist и устранить регрессии.
14. День 14: стабилизация и приёмка. Финальный проход по DoD, smoke demo “A редактирует, B видит, B получает `409` на устаревшей версии”, фиксация известных ограничений и handoff-заметок для спринта 2.

## Test Plan

- Backend integration:
  - login success/fail
  - `401` на protected routes без токена
  - `403` для `viewer` на `POST/PATCH/DELETE`
  - `editor` может выполнить create/update/delete
  - websocket-клиент получает `feature_created`, `feature_updated`, `feature_deleted`
- Frontend automated:
  - auth-store сохраняет/сбрасывает токен и пользователя
  - login screen переключает приложение в карту после успешного входа
  - realtime-обработчик не ломается на повторной доставке события
  - reconnect инициирует повторную синхронизацию активного слоя
- Acceptance/demo:
  - два клиента входят по email/password
  - клиент B видит изменение клиента A за `1–2 секунды`
  - конфликт версии по-прежнему даёт `409` и не теряет данные
  - CI остаётся зелёным без добавления e2e-браузерного контура в этом спринте

## Assumptions

- Зафиксирован целевой auth-flow: `email + password`, без внешнего SSO.
- Seed-пользователи нужны только для demo/local воспроизводимости; полноценный user-management не входит в спринт 1.
- Спринт планируется как один последовательный поток реализации без параллельной команды.
- Оценка опирается на код-ревью текущего репозитория и документы `docs/`; локальный полный прогон существующих тестов в этой среде не был надёжно подтверждён.
