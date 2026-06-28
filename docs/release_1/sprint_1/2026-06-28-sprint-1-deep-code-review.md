# Глубокое ревью кода Спринта 1

Дата: 2026-06-28

## Объем Ревью

Ревью выполнено для текущего Спринта 1 Utility Workflow: `Login -> Мои наряды -> Create/Open EditVersion -> Edit Workspace`. Функции persisted editing, validation, reconcile, review/post и audit не считались дефектами только из-за отсутствия, потому что они вынесены за границу Спринта 1.

Проверенные зоны:

- backend auth, RBAC, workflow API, WebSocket auth, services/repositories, Alembic migrations, seed/smoke;
- frontend auth/session, `Мои наряды`, workspace map, API contracts/stores, UX/UI states;
- CI/Docker/test gates и воспроизводимость локальных проверок.

## Проверки

| Команда | Итог |
|---|---|
| `docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "pytest"` | `169 passed, 37 skipped, 1 warning` |
| `docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "ruff check ."` | `All checks passed!` |
| `docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "black --check ."` | `185 files would be left unchanged` |
| `npm run typecheck` в `apps/frontend` | passed |
| `npm test` в `apps/frontend` | `13 passed`, `48 passed` |
| `npm run lint` в `apps/frontend` | passed |
| `npm run format:check` в `apps/frontend` | passed |
| `npm run build` в `apps/frontend` | passed, но Vite предупредил о chunk `1,167.86 kB`, gzip `332.16 kB` |

Ограничение локального запуска: обычный `python` в среде указывает на WindowsApps stub, а bundled Python не содержит `pytest`. Backend gate воспроизводится через Docker `dev` image; это соответствует текущему CI.

## Краткий Вывод

Автоматические проверки зеленые, но есть несколько важных ручных находок. Самые рискованные: возможная утечка старого workspace между пользователями в одной вкладке, гонка при открытии `EditVersion`, dev-login/default-secret профиль, хранение и передача JWT в местах с повышенным риском утечки. Главные UX/UI проблемы: тяжелая карта грузится до выбора наряда, экран workspace дает мало рабочей информации кроме карты, состояния ошибок/загрузки не дружат с accessibility и structured error contract.

## Находки

### P1. Старый workspace может остаться в памяти после logout и попасть в UI следующего пользователя

Категории: bug, security, UX/UI

Где:

- `apps/frontend/src/stores/auth.ts:102` - `logout()` очищает только auth token/user;
- `apps/frontend/src/stores/workOrders.ts:75` - `loadAssigned()` не сбрасывает старые `items`, selection и workspace перед новой загрузкой;
- `apps/frontend/src/components/EditorWorkOrdersView.vue:128` - карта рендерит `workOrders.activeWorkspace`, если он остался в store.

Что может случиться:

1. Editor A открывает workspace.
2. Пользователь выходит.
3. Editor B входит в той же SPA-сессии без hard reload.
4. `EditorWorkOrdersView` запускает `loadAssigned()`, sidebar показывает loading, но старый `activeWorkspace` может оставаться доступным до завершения новой загрузки.

Риск: визуальная утечка чужого workspace в той же вкладке, особенно при demo-переключении `alexey.editor` / `bolat.editor`.

Варианты исправления:

- Добавить в `workOrders` action `reset()` и вызывать его при `auth.logout()` и при смене `auth.user.id`.
- В `loadAssigned()` до API-запроса очищать `items`, `selectedWorkOrderId`, `openedWorkOrderId`, `openedEditVersionId`, `workspace`, `lastFittedWorkspaceKey`.
- Хранить в `workOrders` `ownerUserId`; если текущий auth user не совпадает, getters должны возвращать `null`.
- Добавить frontend test: открыть workspace, выполнить logout/login другим user id, проверить что `activeWorkspace === null` до и после `loadAssigned()`.

### P1. Гонка при idempotent open `EditVersion` может превратиться в 500

Категории: bug, reliability

Где:

- `apps/backend/utility_service/use_cases/services/edit_version_service.py:51` - сервис сначала читает существующую open version;
- `apps/backend/utility_service/use_cases/services/edit_version_service.py:78` - затем создает новую;
- `apps/backend/utility_service/infrastructure/postgresql/models/work_order/edit_version.py:45` и `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/f2b3c4d5e6a7_sprint1_schema_boundaries.py:297` - уникальный индекс запрещает две open versions на work order.

Что может случиться:

Два параллельных `POST /api/v1/work-orders/{id}/edit-versions` оба увидят `existing is None`. Один commit пройдет, второй получит `IntegrityError` от `uq_edit_versions_open_work_order`. Сейчас этот путь не перехватывается как идемпотентный reopen и может уйти клиенту как 500.

Варианты исправления:

- Взять row lock на `WorkOrder` при open: `SELECT ... FOR UPDATE` до проверки статуса и existing version.
- Или использовать PostgreSQL upsert: `INSERT ... ON CONFLICT ON CONSTRAINT/INDEX DO NOTHING`, затем перечитать open version.
- Или ловить `IntegrityError`, откатывать вложенную транзакцию, перечитывать existing open version и возвращать `OpenEditVersionResult(created=False, ...)`.
- Добавить integration test с двумя конкурентными opens или repository-level test на simulated `IntegrityError`.

### P1. Dev-login и default JWT secret безопасны только пока окружение строго локальное

Категории: security, operational risk

Где:

- `infra/docker-compose.yml:38` - `DEV_MODE` по умолчанию `true`;
- `infra/docker-compose.yml:39` - `JWT_SECRET` по умолчанию `CHANGE_ME_IN_ENV`;
- `apps/backend/utility_service/utils/settings.py:27` - default secret разрешен при `DEV_MODE=true`;
- `apps/backend/utility_service/web_api/api/auth.py:110` - `/api/v1/auth/dev-login` подключается при dev mode;
- `apps/backend/utility_service/use_cases/services/auth_service.py:25` - `get_dev_user()` создает пользователя, если email новый.

Что может случиться:

Если compose-среда случайно опубликована за пределы локальной машины, любой клиент может создать dev-user с переданной ролью и получить JWT, подписанный предсказуемым секретом. Для локального demo это удобно, но граница слишком легко переносится в unsafe deployment.

Варианты исправления:

- Разнести `docker-compose.demo.yml` и production compose; в базовом compose не включать `DEV_MODE=true`.
- Ввести отдельный флаг `ALLOW_DEV_LOGIN=true`, без которого route не регистрируется даже при `DEV_MODE`.
- Запретить `CHANGE_ME_IN_ENV` при любом exposed binding, например когда `HOST=0.0.0.0`.
- В prod image не включать dev-login route через environment guard на старте.
- Добавить startup log/health warning: `devAuthEnabled=true`, но без вывода секретов.

### P1. JWT хранится в `localStorage` и передается в WebSocket query string

Категории: security

Где:

- `apps/frontend/src/stores/auth.ts:54` - token сохраняется в `localStorage`;
- `apps/frontend/src/composables/map/useLayerRealtime.ts:276` - token добавляется в URL query parameter;
- `apps/backend/utility_service/web_api/api/ws_layers.py:34` - backend читает token из query string;
- `apps/frontend/src/composables/map/useLayerRealtime.test.ts:112` - тест закрепляет наличие `token=...` в URL.

Риски:

- `localStorage` доступен любому XSS в приложении.
- Query token может попадать в browser/dev-proxy/server logs, diagnostic dumps и историю сетевых запросов.

Варианты исправления:

- Для HTTP auth перейти на `HttpOnly`, `Secure`, `SameSite` cookie либо хранить access token только в памяти.
- Для WebSocket использовать short-lived одноразовый ticket: HTTP endpoint выдает ticket на layer/workspace, WebSocket принимает `ticket`, а не JWT.
- Альтернатива для same-origin deployments: WebSocket auth через cookie.
- Если query token временно остается, сократить TTL, отключить логирование query string и добавить тест, что production logs не пишут URL с token.

### P2. Legacy layers/realtime остаются более широким read-channel, чем новый Utility Workflow

Категории: security, architecture

Где:

- `apps/backend/utility_service/web_api/api/layers.py:29` - read endpoints legacy layers требуют только `get_current_user`;
- `apps/backend/utility_service/web_api/api/websocket_auth.py:11` - realtime разрешен ролям `editor` и `reviewer`;
- `apps/backend/utility_service/web_api/tests/test_ws_layers.py:30` - тест закрепляет доступ WebSocket для `reviewer`.

Проблема:

Новые endpoints work-order/workspace правильно требуют `Editor` и assigned work order. Но legacy `/api/v1/layers` и `/api/v1/ws/layers/{layer_id}` остаются глобальным чтением слоя для любого авторизованного `Reviewer`/`Editor`. Это может обходить новую work-order модель доступа, если legacy API содержит реальные или похожие данные.

Варианты исправления:

- В utility mode закрыть legacy layer read для `Reviewer` и/или для всех ролей, кроме явно разрешенного compatibility flag.
- Добавить ACL на layer/workspace: layer read разрешен только если слой входит в work-order scope пользователя.
- Развести legacy GIS API и utility workflow API по feature flag и документации.
- Добавить regression tests: reviewer не может читать layer features/realtime, editor не может читать слой вне assigned AOI/work order.

### P2. Error contract не единый: часть ошибок не возвращает `code/message/correlationId`

Категории: bug, API contract, UX/UI

Где:

- `docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-api-contract-design.md:27` - каждый error response должен содержать `correlationId`;
- `apps/backend/utility_service/use_cases/services/auth_service.py:37` - invalid login бросает `HTTPException` с `detail`;
- `apps/backend/utility_service/web_api/api/exception_handlers.py:75` - legacy exceptions возвращают `{"error": ...}`;
- `apps/frontend/src/components/LoginScreen.vue:65` - UI ожидает `response.data.detail`;
- `apps/frontend/src/stores/workOrders.ts:94` и `apps/frontend/src/stores/workOrders.ts:140` - workflow errors схлопываются в generic message без `code`/`correlationId`.

Проблема:

Контракт Sprint 1 фиксирует structured errors, но login/legacy/workspace UI используют несколько форматов. Пользователь не видит correlation id, а frontend не может различать `WORK_ORDER_NOT_FOUND`, `WORK_ORDER_CONTEXT_INVALID`, `ROLE_NOT_ALLOWED` и временную сетевую ошибку.

Варианты исправления:

- Перевести invalid login на `AuthApiError(401, "INVALID_CREDENTIALS", ...)`.
- Добавить общий `ApiErrorOut` и handlers для `HTTPException`/legacy domain exceptions.
- На frontend добавить `parseApiError()` с поддержкой `code`, `message`, `correlationId`.
- В UI показывать короткое русское сообщение и технический `correlationId` в раскрываемой диагностике.

### Архитектурное примечание. Cross-context UUID links без FK являются решением bounded contexts

Категории: architecture decision, operational guardrail

Где:

- `apps/backend/utility_service/infrastructure/postgresql/models/work_order/work_order.py:76` - `assignee_user_id` без FK на `user.users`;
- `apps/backend/utility_service/infrastructure/postgresql/models/work_order/work_order.py:77` - `created_by_user_id` без FK;
- `apps/backend/utility_service/infrastructure/postgresql/models/work_order/edit_version.py:67` - `default_state_id` без FK;
- `apps/backend/utility_service/infrastructure/postgresql/models/work_order/edit_version.py:68` - `owner_user_id` без FK;
- `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/f2b3c4d5e6a7_sprint1_schema_boundaries.py:107` и `:277` - миграция создает эти UUID как plain columns.

Уточнение после ревью:

Это не баг и не code smell. В `Code_wiki/архитектура/data_model.md` уже зафиксировано, что cross-schema связи между будущими сервисными границами не закрепляются внешними ключами: идентификаторы пользователя, work order и сетевого baseline связываются через repositories/application layer. Это осознанное решение для разделения bounded contexts.

Остаточный риск:

При ручной правке БД, ошибке seed или будущей миграции можно получить orphan identifiers. Это не отменяет bounded-context решения, но требует явных operational checks.

Guardrails вместо исправления:

- Не добавлять cross-context FK как default-рекомендацию.
- Сохранить FK внутри owned aggregate/schema, например `work_order.work_orders.aoi_id -> work_order.aois.id`.
- Добавить read-only consistency check/preflight для demo seed и миграций: существование assignee user, creator user, owner user, active per-WorkOrder `DefaultState`, matching `baseNetworkRevision`.
- В runbook явно назвать такие проверки application-level integrity, а не database FK integrity.
- В тестах оставить сценарии `WORK_ORDER_CONTEXT_INVALID` для поврежденного контекста и добавить smoke/preflight на seed chain.

### P2. Миграции Sprint 1 содержат destructive rebuild и неполный downgrade

Категории: data loss risk, operations, code smell

Где:

- `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/f2b3c4d5e6a7_sprint1_schema_boundaries.py:23`-`:30` - upgrade удаляет старые/new tables через `DROP TABLE ... CASCADE`;
- `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/f2b3c4d5e6a7_sprint1_schema_boundaries.py:387` - downgrade тоже удаляет текущие tables;
- `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/c9d0e1f2a3b4_repair_work_order_aoi_scope.py:184` - downgrade пустой (`pass`).

Проблема:

Для локального demo rebuild допустим, но такие миграции опасны, если цепочка попадет на среду с ценными данными. Пустой downgrade также ломает уверенность в rollback strategy.

Варианты исправления:

- До production-like среды squash/rewrite миграции Sprint 1 в чистую non-destructive baseline.
- Если данные уже могут быть ценными, заменить `DROP TABLE` на проверяемую data migration с backup/preflight.
- Добавить миграционный runbook: какие миграции demo-only, какие production-safe.
- Для irreversible downgrade явно бросать `NotImplementedError` с объяснением, а не silent `pass`; лучше реализовать обратную миграцию или запретить rollback документированно.

### P2. Workspace API и карта загружают весь AOI одним payload/source

Категории: performance, scalability

Где:

- `apps/backend/utility_service/infrastructure/postgresql/repositories/work_order_repository.py:138` - выбираются feature ids через `ST_Intersects`;
- `apps/backend/utility_service/infrastructure/postgresql/repositories/work_order_repository.py:163` и `:196` - features/associations агрегируются в JSONB целиком;
- `apps/backend/utility_service/infrastructure/postgresql/models/work_order/edit_version_feature.py:107` - geometry column без отдельного spatial index;
- `apps/frontend/src/map/workspace-layers.ts:142` - весь `FeatureCollection` кладется в один MapLibre source.

Проблема:

На demo dataset 19 features/9 associations это нормально. Но при росте AOI workspace response и MapLibre source станут узким местом: один большой JSON, повторяющиеся subqueries, отсутствие bbox/tile pagination для workspace.

Варианты исправления:

- Добавить GiST index на `work_order.edit_version_features.geometry`, если workspace AOI будет включать сотни/тысячи объектов.
- Переписать aggregate query через CTE/materialized feature id set, чтобы не повторять spatial filter для features и associations.
- Ввести workspace tiles/bbox endpoint или lazy loading по viewport.
- Добавить summary endpoint: счетчики и bounds отдельно от feature payload.
- В frontend заменить единственный source на tile/source strategy или хотя бы chunked setData для больших payload.

### P2. Initial frontend bundle слишком крупный и грузит MapLibre до выбора наряда

Категории: performance, UX/UI

Где:

- `apps/frontend/src/App.vue:4` - `EditorWorkOrdersView` импортируется синхронно;
- `apps/frontend/src/components/EditorWorkOrdersView.vue:4` - `MapView` импортируется синхронно;
- `apps/frontend/src/components/MapView.vue:35` и `apps/frontend/src/composables/map/useMapInstance.ts:2` - MapLibre подключается в основной цепочке;
- `apps/frontend/src/components/EditorWorkOrdersView.vue:138` - даже empty state рендерит `MapView mode="empty"`.

Наблюдение проверки:

`npm run build` прошел, но Vite предупредил о minified chunk `1,167.86 kB`, gzip `332.16 kB`.

Проблема:

Login screen, Reviewer placeholder и пустое состояние до выбора work order платят стоимость MapLibre/WebGL. Это ухудшает первое открытие, особенно на слабом ноутбуке демо.

Варианты исправления:

- Использовать `defineAsyncComponent` для `EditorWorkOrdersView`, `ReviewerHome`, особенно `MapView`.
- В empty state показывать lightweight placeholder вместо MapLibre; карту монтировать после выбора/open workspace.
- В `vite.config.ts` выделить `maplibre-gl` в отдельный manual chunk.
- Добавить build budget в CI: предупреждать или падать при chunk выше согласованного порога.

### P3. UX workspace слишком "map-only" и не поддерживает рабочее принятие решения

Категории: UX/UI

Где:

- `apps/frontend/src/components/EditorWorkOrdersView.vue:127`-`:138` - основная область либо карта, либо empty map;
- `apps/frontend/src/components/MapView.vue:172` - вся мета-информация workspace упакована в одну строку badge.

Проблема:

Для первого workflow пользователь видит список нарядов и карту, но не получает устойчивой панели деталей выбранного наряда: AOI, base revision, counts, edit version id/status, что уже открыто, что делать дальше. Badge на карте становится длинной строкой и плохо сканируется.

Варианты исправления:

- Добавить compact details panel над/рядом с картой: `WO code`, title, status, AOI, base revision, counts, edit version.
- Разделить badge на короткий статус и отдельную диагностическую панель.
- Показывать явный read-only режим workspace: "Редактирование появится в следующем спринте" лучше в контекстной зоне, не как маркетинговый текст.
- Для selected but not opened state показывать preview/details и primary action, а не только empty map.

### P3. Loading/error/selection states недостаточно доступны

Категории: UX/UI, accessibility

Где:

- `apps/frontend/src/components/LoginScreen.vue:33` - error message без `role="alert"`/`aria-live`;
- `apps/frontend/src/components/EditorWorkOrdersView.vue:53` и `:57` - loading/error panel без `aria-live`/`aria-busy`;
- `apps/frontend/src/components/EditorWorkOrdersView.vue:77` - selected work order отмечается только CSS class;
- `apps/frontend/src/components/EditorWorkOrdersView.vue:93` и `:110` - error/open action не связываются с выбранным card через ARIA.

Проблема:

Клавиатурный и screen-reader пользователь хуже понимает, какой наряд выбран, идет ли загрузка, что изменилось после ошибки. Для демо это может быть не блокером, но быстро копится в UX debt.

Варианты исправления:

- Добавить `aria-current` или `aria-pressed` на selected work order button.
- Добавить `aria-live="polite"` для loading/success state и `role="alert"` для ошибок.
- Добавить `aria-busy` на panel/map container во время загрузки/open.
- Сохранять focus после retry/open и переводить focus на карту/details panel после успешного открытия.

### P3. UI controls мало сканируются как рабочий инструмент

Категории: UX/UI, code smell

Где:

- `apps/frontend/src/App.vue:68` - logout button только текстом;
- `apps/frontend/src/components/EditorWorkOrdersView.vue:45` - refresh button только текстом;
- `apps/frontend/src/components/MapView.vue:4`-`:13` - legacy editing toolbar использует plain select/buttons.

Проблема:

Для operational UI лучше работают компактные icon+tooltip controls, устойчивые размеры, явные disabled/loading states. Текущие кнопки функциональны, но выглядят как минимальный прототип.

Варианты исправления:

- Подключить существующую icon library или `lucide-vue-next` и заменить refresh/logout/primary actions на icon+text или icon buttons с tooltip.
- Зафиксировать min-width для primary buttons, чтобы loading text не дергал layout.
- Для map toolbar использовать иконки команд и compact segmented controls, когда editing mode вернется в scope.

### P3. Типы boundary местами слишком широкие

Категории: code smell, maintainability

Где:

- `apps/backend/utility_service/web_api/api/work_orders.py:30`, `:44`, `:74` - `user: Any`;
- `apps/backend/utility_service/web_api/api/utility_network.py:24` - dependency result typed as `Any`;
- `apps/backend/utility_service/use_cases/services/workspace_service.py:86` - `workspace_from_aggregate(self, aggregate: Any)`.

Проблема:

`Any` в API/use-case boundary скрывает реальные контракты auth user и aggregate row. Это делает refactor roles/access и workspace response менее безопасным.

Варианты исправления:

- Ввести `AuthenticatedUser` Protocol/dataclass с `id`, `email`, `role`, `is_active`.
- Типизировать `WorkspaceAggregateRow` в service вместо `Any`.
- Сдвинуть role/value helpers в единый auth policy module, чтобы не повторять `_role_value` и enum/string преобразования.

### P3. Backend test deps живут только в Docker dev image

Категории: developer experience, CI maintainability

Где:

- `apps/backend/requirements.txt` - нет `pytest`;
- `apps/backend/Dockerfile:18`-`:20` - `pytest`, `ruff`, `black` устанавливаются только в `dev` stage;
- `.github/workflows/ci.yml:70` - CI запускает `pytest` только внутри `utility_service:dev`.

Проблема:

Локальный запуск backend tests без Docker не воспроизводится из `requirements.txt`. В текущей среде bundled Python не содержит `pytest`, поэтому пришлось запускать Docker image. Это допустимо, но onboarding и быстрый feedback loop зависят от Docker Desktop.

Варианты исправления:

- Добавить `requirements-dev.txt` или `pyproject` extras/group с `pytest`, `ruff`, `black`.
- Обновить README/runbook: canonical local backend test command через Docker и альтернативный venv command.
- В CI дополнительно smoke-test prod image startup, потому что prod stage не содержит dev tools и не запускается тестами.

## Рекомендуемый Порядок Исправления

1. Сброс `workOrders` при logout/user change и тест на отсутствие stale workspace.
2. Idempotent/concurrent open `EditVersion`: row lock/upsert/catch `IntegrityError` и regression test.
3. Dev-login hardening и default secret policy.
4. WebSocket/auth token hardening.
5. Unified structured error handling + frontend `parseApiError`.
6. Lazy loading MapLibre и lightweight empty state.
7. Операционные проверки согласованности для cross-context UUID links без FK.
8. Workspace performance plan перед ростом dataset.
