# День 8: frontend WebSocket client, применение realtime-событий и reconnect для активного слоя

## Summary

Целевой файл плана: `docs/requirements/sprints/sprint-1/day-8-plan.md`.

Day 8 должен добавить во frontend WebSocket client для подписки на realtime-события активного слоя, сразу применять входящие `feature_created|updated|deleted` к карте, встроить reconnect/backoff с лимитом попыток и выполнять принудительную синхронизацию `reloadFeatures(..., force=true)` только после успешного восстановления соединения. Вне Day 8 остаются дальнейшее укрепление cache orchestration на краевых случаях, расширенные unit-тесты идемпотентности и integration-сценарий двух клиентов.

## Цель дня

- Подключать frontend к `WS /api/v1/ws/layers/{layer_id}?token=<jwt>` для текущего активного слоя.
- Сразу отражать входящие realtime-события на карте через существующие map callbacks.
- Автоматически переподключаться при разрыве соединения, но с ограниченным числом попыток.
- После успешного reconnect выполнять принудительную синхронизацию активного слоя через `reloadFeatures(layer, { force: true })`.
- Останавливать reconnect при websocket auth-проблеме и передавать управление обычному auth/logout flow приложения.
- Не ломать текущий login flow, карту, tile-cache и ручное редактирование feature.

## Входная база Day 8

- Backend уже умеет:
  - принимать websocket-подключение на `WS /api/v1/ws/layers/{layer_id}?token=<jwt>`
  - отправлять техническое событие `connected`
  - публиковать `feature_created`, `feature_updated`, `feature_deleted`
- Frontend уже имеет:
  - [auth store](/C:/Repositories/geoservice/apps/frontend/src/stores/auth.ts) с токеном и пользователем
  - [MapView.vue](/C:/Repositories/geoservice/apps/frontend/src/components/MapView.vue), где живёт активный слой и карта
  - [useFeatureLoading.ts](/C:/Repositories/geoservice/apps/frontend/src/composables/map/useFeatureLoading.ts), где уже есть:
    - `reloadFeatures(layer, options)`
    - `applyCreatedFeature(...)`
    - `applyPatchedFeature(...)`
    - `applyDeletedFeature(...)`
    - `stopPendingFeatureWork()`
  - [useFeatureTileCache.ts](/C:/Repositories/geoservice/apps/frontend/src/composables/map/useFeatureTileCache.ts) для cache/update/invalidate логики
- Сейчас во frontend нет:
  - WebSocket client
  - realtime event contract types
  - reconnect/backoff orchestration
  - отдельного realtime status badge

## Результат дня

- При открытии слоя frontend открывает websocket-подписку на этот `layer_id`.
- При смене слоя предыдущее websocket-соединение закрывается, новое открывается для нового слоя.
- При logout или размонтировании карты websocket корректно закрывается.
- Входящие `feature_created`, `feature_updated`, `feature_deleted` сразу применяются к карте.
- При разрыве соединения frontend запускает reconnect с backoff и лимитом попыток.
- После успешного reconnect frontend вызывает `reloadFeatures(activeLayer, { force: true })`.
- Первичное успешное подключение не вызывает принудительный reload.
- При auth-проблеме websocket перестаёт пытаться переподключаться и отдаёт управление обычному auth/logout flow.
- Техническое сообщение `connected` используется как сигнал успешного соединения и успешного восстановления подписки.
- Пользователь видит отдельный небольшой badge рядом с картой со статусом realtime.

## Ключевое решение

- Day 8 не должен встраивать websocket-логику прямо в `App.vue` или `auth-store`.
- Realtime-клиент должен жить рядом с картой и активным слоем, потому что подписка зависит именно от `activeLayerId`, а не от общей авторизации приложения.
- Для текущей структуры проекта достаточно выделить отдельный composable, например:
  - `useLayerRealtime(...)`
- Этот composable должен:
  - знать текущий `token`
  - знать текущий `activeLayer`
  - открывать и закрывать websocket
  - отслеживать reconnect/backoff
  - применять входящие события через callbacks карты
  - вызывать callback на успешный reconnect
  - уметь прекращать reconnect после лимита попыток или auth-ошибки
- Day 8 уже должен связывать входящие realtime-события с текущими map callbacks, а не ограничиваться только поддержанием соединения.

## Задачи

1. Добавить frontend-типы realtime-событий Sprint 1.
2. Описать техническое сообщение `connected` как отдельный websocket message type.
3. Создать composable для websocket-подписки активного слоя.
4. Подключить composable в [MapView.vue](/C:/Repositories/geoservice/apps/frontend/src/components/MapView.vue).
5. Открывать websocket только если:
   - пользователь авторизован
   - есть `auth.token`
   - есть активный слой
6. Закрывать websocket при:
   - смене активного слоя
   - logout
   - размонтировании `MapView`
7. Добавить reconnect с backoff после `close` или сетевого разрыва.
8. После успешного reconnect и получения `connected` вызывать `reloadFeatures(layer, { force: true })`.
9. Сразу применять `feature_created`, `feature_updated`, `feature_deleted` к текущей карте через уже существующие map callbacks.
10. Не вызывать reconnect, если сокет был закрыт намеренно при смене слоя, logout или размонтировании.
11. Останавливать reconnect после исчерпания лимита попыток.
12. Останавливать reconnect при websocket auth-проблеме и передавать управление обычному auth/logout flow приложения.
13. Показать отдельный небольшой badge статуса realtime рядом с картой:
    - подключено
    - переподключение
    - повторная синхронизация после reconnect
    - переподключение остановлено
    - ошибка авторизации realtime

## Решение по реализации

### Контракт frontend realtime types

- Добавить новый frontend contract module, например:
  - `src/contracts/realtime.ts`
- В нём зафиксировать:
  - `RealtimeConnectedEvent`
  - `FeatureCreatedEvent`
  - `FeatureUpdatedEvent`
  - `FeatureDeletedEvent`
  - объединённый тип `LayerRealtimeEvent`
- Для `feature_created` и `feature_updated` использовать уже существующий `ApiFeature`.
- Для `feature_deleted` использовать:
  - `type`
  - `eventId`
  - `occurredAt`
  - `layerId`
  - `featureId`

### WebSocket composable

- Создать composable уровня карты, например:
  - `src/composables/map/useLayerRealtime.ts`
- Интерфейс composable должен покрывать:
  - `connectToLayer(layerId, token)`
  - `disconnect()`
  - `handleLayerChange(layer, token)`
  - `isConnected`
  - `isReconnecting`
  - `isSyncingAfterReconnect`
  - `hasStoppedReconnect`
  - `connectionError`
- Внутри composable:
  - строить URL websocket из `VITE_API_BASE_URL` или HTTP base URL
  - конвертировать `http/https` в `ws/wss`
  - открывать соединение только для одного активного слоя
  - хранить флаг intentional close, чтобы не запускать reconnect по собственному `disconnect()`
  - различать первичное подключение и успешный reconnect
  - различать обычный сетевой разрыв и auth-проблему websocket

### Reconnect/backoff

- Использовать простой backoff без внешней библиотеки.
- Достаточно последовательности вида:
  - 500 ms
  - 1000 ms
  - 2000 ms
  - 5000 ms max
- Reconnect должен быть ограничен по числу попыток.
- После достижения лимита composable переводит realtime в состояние `stopped` и больше не открывает новые сокеты автоматически.
- При успешном `connected`:
  - сбрасывать счётчик попыток
  - если это reconnect, запускать `reloadFeatures(layer, { force: true })`
  - если это первичное подключение, не выполнять forced reload
- Если активный слой изменился до завершения reconnect:
  - отменять старый reconnect-поток
  - открывать новый сокет уже для нового слоя
- Если закрытие связано с auth-проблемой websocket:
  - не запускать reconnect
  - фиксировать техническую ошибку realtime
  - передавать управление обычному auth/logout flow приложения

### Интеграция с `MapView`

- В [MapView.vue](/C:/Repositories/geoservice/apps/frontend/src/components/MapView.vue):
  - инициализировать realtime composable после загрузки карты и слоёв
  - при первичной успешной загрузке слоя открывать websocket для активного слоя
  - при `onChangeLayer()`:
    - сначала переключать слой
    - затем переподключать websocket к новому `layer.id`
  - при `onBeforeUnmount()` корректно закрывать websocket
- Статус realtime не смешивать с `labelText`.
- Показать его отдельным небольшим badge рядом с картой, чтобы не перегружать основной текст состояния редактора.

### Realtime status UI

- Badge должен покрывать как минимум состояния:
  - `Подключено`
  - `Переподключение`
  - `Синхронизация`
  - `Переподключение остановлено`
  - `Ошибка авторизации realtime`
- Badge остаётся локальным для `MapView` и не требует отдельного глобального store.

### Интеграция с `useFeatureLoading`

- Day 8 не должен перепридумывать tile-cache.
- Достаточно использовать уже готовые функции:
  - `applyCreatedFeature(...)`
  - `applyPatchedFeature(...)`
  - `applyDeletedFeature(...)`
  - `reloadFeatures(layer, { force: true })`
- Входящие realtime-события Day 8 уже должны быть напрямую связаны с этими функциями:
  - `feature_created` -> `applyCreatedFeature(...)`
  - `feature_updated` -> `applyPatchedFeature(...)`
  - `feature_deleted` -> `applyDeletedFeature(...)`
- Day 9 может дополнительно усиливать cache orchestration и edge cases, но Day 8 уже обязан применять входящие события к карте без полной перезагрузки страницы.

## Ограничения дня

- Без глобального realtime store.
- Без SSR-friendly обвязки и без отдельной event bus-подсистемы.
- Без сложной telemetry или logging-системы по websocket.
- Без cross-tab sync.
- Без replay missed events после reconnect.
- Без Redis-aware логики на клиенте.
- Без integration-suite на реальном браузере; это остаётся на более поздние дни.

## Проверки

### Realtime connection checks

- При наличии `auth.token` и активного слоя websocket успешно открывается.
- После получения `connected` состояние realtime считается рабочим.
- При первичном успешном `connected` forced reload не вызывается.
- При смене слоя старое соединение закрывается, новое открывается.
- При logout websocket закрывается и reconnect не продолжается.
- Входящие `feature_created`, `feature_updated`, `feature_deleted` сразу маршрутизируются в map callbacks.

### Reconnect checks

- При разрыве соединения запускается reconnect.
- При успешном reconnect вызывается `reloadFeatures(layer, { force: true })`.
- Повторные reconnect-попытки не создают несколько параллельных сокетов для одного слоя.
- Intentional close не запускает reconnect.
- Reconnect останавливается после достижения лимита попыток.
- Auth-проблема websocket останавливает reconnect и не уходит в бесконечные повторные подключения.

### UI checks

- Пользователь видит отдельный небольшой badge статуса realtime рядом с картой.
- Badge корректно отражает состояния:
  - подключено
  - переподключение
  - повторная синхронизация
  - переподключение остановлено
  - ошибка авторизации realtime
- Карта не ломается, если websocket временно недоступен.
- Ручное редактирование и сохранение feature продолжают работать как раньше.

### Test plan

- Unit tests на realtime contract guards/parsers.
- Unit tests на websocket composable:
  - connect
  - disconnect
  - reconnect after close
  - no reconnect after intentional close
  - stop reconnect after limit
  - stop reconnect on auth-related close
  - force reload only after successful reconnect
  - route incoming `feature_created`, `feature_updated`, `feature_deleted` в map callbacks
- Existing frontend tests должны оставаться зелёными.

## Demo-сценарий дня

1. Пользователь логинится и открывает карту.
2. Frontend загружает слои и открывает websocket на активный слой.
3. Backend отвечает техническим `connected`.
4. Пока соединение активно, входящие `feature_created`, `feature_updated`, `feature_deleted` сразу отражаются на карте.
5. Пользователь меняет слой.
6. Frontend закрывает старый сокет и открывает новый для нового `layer_id`.
7. Имитируется разрыв websocket-соединения.
8. Frontend запускает reconnect с backoff.
9. После восстановления соединения frontend вызывает `reloadFeatures(activeLayer, { force: true })`.
10. Если reconnect упирается в лимит попыток или auth-проблему, пользователь видит соответствующий статус badge, а приложение не уходит в бесконечный цикл подключений.

## Definition of Done для Дня 8

- Во frontend есть отдельный websocket client/composable для активного слоя.
- Подписка работает по контракту `WS /api/v1/ws/layers/{layer_id}?token=<jwt>`.
- При смене слоя и при unmount старые соединения корректно закрываются.
- Входящие realtime-события сразу применяются к карте через существующие map callbacks.
- При сетевом разрыве reconnect запускается автоматически, но ограничен по числу попыток.
- После успешного reconnect выполняется `reloadFeatures(..., { force: true })`.
- Первичное успешное подключение не вызывает forced reload.
- Auth-проблема websocket останавливает reconnect и не ломает обычный auth flow приложения.
- Пользователь видит отдельный badge статуса realtime рядом с картой.
- Day 8 не ломает auth flow, карту и текущий tile-cache.

## Assumptions

- Day 8 использует browser `WebSocket` без внешней библиотеки.
- Техническое сообщение `connected` остаётся допустимой частью backend/frontend handshake.
- Для Sprint 1 достаточно локальной reconnect-логики внутри `MapView`-сценария.
- Day 8 уже применяет входящие realtime-события к карте.
- Day 9 дополнительно укрепляет cache orchestration и edge cases, но не заменяет базовую realtime-связку, сделанную в Day 8.
