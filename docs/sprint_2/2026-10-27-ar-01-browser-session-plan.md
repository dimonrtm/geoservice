# AR-01: план реализации сессии браузера

> **Для агента-исполнителя:** обязательный skill — `superpowers:subagent-driven-development` либо `superpowers:executing-plans`, согласно выбранному пользователем способу исполнения. Выполнять задачи последовательно, отмечая только проверенные пункты. Правило репозитория запрещает агенту `git add`, `git commit`, `git push`; изменения остаются unstaged.

**Цель:** устранить гонку восстановления вкладок и обеспечить немедленный серверный отзыв всех токенов текущей браузерной сессии при успешном выходе.

**Архитектура:** стабильная родительская `BrowserAuthSession` объединяет ротируемые refresh credentials, access JWT и WebSocket tickets. PostgreSQL определяет действительность сессии; frontend упорядочивает auth-запросы через Web Locks и синхронизирует вкладки через marker, BroadcastChannel и независимую status-проверку.

**Стек:** Python 3.12, FastAPI, SQLAlchemy/asyncpg, PostgreSQL/PostGIS, Alembic; Vue 3, Pinia, TypeScript, Axios, Vitest; существующий Playwright из `infra/m4`.

**Спецификация:** [принятый дизайн](2026-10-27-ar-01-browser-session-design.md). Пользователь одобрил его 2026-10-27 ответом «Принимаю» и затем поручил реализацию плана. Все восемь задач выполнены и проверены; результаты отражены в checklist ниже.

**Состояние на 2026-10-28:** все восемь задач, общий review и точечный re-review исправлений завершены без открытых замечаний. [Отчёт](2026-10-27-ar-01-browser-session-implementation-report.md) раскрывает результаты и ограничения; [итог ревью](2026-10-27-ar-01-browser-session-final-review.md) сохранён отдельно. Изменения unstaged, Git-операции остаются пользователю.

## Общие ограничения

- Одна авторизация для вкладок одного origin/profile; другие браузеры, профили и устройства не отзываются по user id.
- После commit logout новые проверки access/refresh/ticket данного sid отклоняются немедленно. Уже допущенная операция может завершиться.
- UI остальных работающих вкладок показывает login за ≤5 секунд: status timeout 1500 ms, пауза между status-запросами ≤1000 ms, не более одного status-запроса на вкладку.
- Ожидание auth lock — 30000 ms; существующий HTTP timeout auth-запросов — 30000 ms. Не делать принудительный захват lock после timeout.
- Logout не пишет/не удаляет cookie. Он отзывает sid; недействительный cookie остаётся до нового login/expiry.
- При недоставленном logout вход сохраняется: «Не удалось выйти, попробуйте ещё раз». При неопределённом исходе: «Не удалось подтвердить выход» и status reconciliation, без автоматического повторного logout.
- Web Locks обязателен в поддерживаемом HTTPS/localhost контексте. При его недоступности не отправлять некоординированный refresh. Отсутствие BroadcastChannel не отменяет marker/status fallback.
- Access/refresh secrets не сохраняются в localStorage, логах, скриншотах сетевых заголовков или evidence.
- Мобильные устройства, блокировка WorkOrder, глобальный logout, grace period для refresh replay, AR-02 и общий рефакторинг workOrders вне объёма.
- Старые JWT без sid и tickets перестают действовать после миграции; нужен повторный вход. Бизнес-данные и история команд сохраняются.
- Текст документации/сообщений — русский. UTF-8/LF, `.cmd`/`.bat` — CRLF. Не менять посторонние файлы форматированием.

## Фокус проверки

1. Истёкший access JWT при активном родителе: status остаётся `active`, рабочий endpoint даёт 401; нельзя объявлять общий logout — задачи 3, 6.
2. Старый logout ответ после нового login: ни новый sid, ни cookie не повреждаются — задачи 2, 6, 8.
3. Инициатор закрыт между commit и marker: соседи находят `ended`; старый status `active` не увеличивает срок сверх 5 секунд — задачи 5, 8.
4. Login того же user id создаёт новый sid: поздний ответ/401 старого sid не меняет новую сессию и recovery — задачи 3, 6.
5. Отказ БД/хранилища и недоставленный logout: не выдавать доступ без проверки и не уничтожать рабочее состояние из-за ложного logout — задачи 3, 5, 7.

## Порядок и команды

Это один сквозной протокол с зависимыми backend/frontend частями. Задачи 1–8 выполняются по порядку; до завершения совместимого обновления отдельные части не выкатываются.

Backend команды ниже запускаются из `apps/backend` в проектной Python-среде. Если локальной среды нет, использовать тот же dev image, что CI, не случайный системный Python. Из корня:

```powershell
docker build --target dev -t geoservice-ar01-backend-dev apps/backend
docker run --rm --entrypoint python geoservice-ar01-backend-dev -m pytest utility_service/use_cases/tests/test_auth_session_service.py
```

Образ содержит snapshot исходников: после изменений для проверки пересобрать его либо использовать проверенный mount текущего checkout. Не проверять старый образ как будто он содержит новые изменения. Настройки тестовой среды — по существующим fixture/settings, без вывода секретов.

DB-проверки запускаются из корня через `infra/db-tests.cmd` в выделенном `geoservice-db-tests` с tmpfs. Скрипт удаляет только этот тестовый Compose project, не demo volumes. Точечные DB-тесты можно запускать через тот же compose/service с `RUN_DB_TESTS=1` и `TEST_DATABASE_URL`; не подставлять рабочую БД. Ожидаемый итог — тесты выполнены, не skipped.

Frontend команды — из `apps/frontend`. Имена ниже указывают новые файлы, которые соответствующая задача должна создать, а не уже существующие тесты.

В списках файлов префикс `.../` означает строго `apps/backend/utility_service/`, если явно не сказано «в той же PostgreSQL-папке». В задаче 1 `.../models` и `.../alembic` означают `apps/backend/utility_service/infrastructure/postgresql/models` и `apps/backend/utility_service/infrastructure/postgresql/alembic`. Соседние имена без префикса относятся к последней полностью названной папке соответствующего списка.

## 1. Родительская сессия и миграция истории credentials

**Файлы:**

- Создать `apps/backend/utility_service/infrastructure/postgresql/models/browser_auth_session.py`.
- Создать `apps/backend/utility_service/infrastructure/postgresql/repositories/browser_auth_session_repository.py`.
- Изменить `.../models/auth_session.py`, `.../models/websocket_ticket.py`, `.../alembic/env.py` в той же PostgreSQL-папке.
- Создать `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/e9f1a2b3c4d5_browser_auth_sessions.py`; перед записью проверить уникальность revision и определить единственный актуальный parent через `alembic heads`.
- Создать `apps/backend/tests/integration_tests/test_browser_auth_session_migration.py` и `test_browser_auth_session_repository.py`.

**Интерфейсы:** модель `BrowserAuthSession(id: UUID, user_id: UUID, created_at: datetime, expires_at: datetime, revoked_at: datetime | None)`. Repository: `create_session(*, user_id: UUID, expires_at: datetime) -> BrowserAuthSession`, `get_session(session_id: UUID, *, for_update: bool = False) -> BrowserAuthSession | None`, `revoke_session(session_id: UUID, *, now: datetime) -> None`, `extend_session(session_id: UUID, *, expires_at: datetime) -> None`. Транзакцией управляет сервис.

- [x] Добавить RED-проверки `test_upgrade_ends_legacy_credentials_and_preserves_business_rows`, `test_new_credentials_require_matching_parent`, `test_parent_lock_serializes_competing_writers`, `test_downgrade_does_not_reactivate_legacy_credentials`. Assert: legacy parents отозваны, все старые token/ticket rows связаны с недействительным родителем, FK/индексы существуют, контрольные business rows неизменны.
- [x] Запустить новые DB-тесты в изоляции и подтвердить падение из-за отсутствующей схемы/контракта, а не ошибки настройки БД.
- [x] Реализовать модели, repository и миграцию: `auth_sessions.browser_session_id`, `websocket_tickets.browser_session_id`, FK/индексы, backfill недействительных родителей, NOT NULL новых связей. Учесть legacy tickets без refresh row: создать отдельный отозванный родитель по их владельцу. Не связывать активные сессии разных браузеров по user id.
- [x] Повторить целевые DB-тесты на чистой схеме и upgrade со старой ревизии; проверить metadata registration и единственную Alembic head. Downgrade не обнуляет существующий `revoked_at`; активные credentials новой схемы также не должны стать действительными в старой схеме.

**Готовность:** структура и миграция проверены настоящей БД; код auth пока не объявляется совместимым с новой схемой.

## 2. Issue/rotation/logout одного sid

**Файлы:** изменить `apps/backend/utility_service/use_cases/services/auth_session_service.py`, `.../use_cases/schemas/auth/issued_auth_session_out.py`, `.../use_cases/schemas/auth/refreshed_auth_session_out.py`, `.../infrastructure/postgresql/repositories/auth_session_repository.py`, `.../use_cases/deps.py`; расширить существующие `.../use_cases/tests/test_auth_session_service.py`, `.../infrastructure/tests/test_auth_session_repository.py`; создать `apps/backend/tests/integration_tests/test_browser_auth_session_races.py`.

**Интерфейсы:**

- `IssuedAuthSessionOut` дополнить `session_id: UUID`; наследник `RefreshedAuthSessionOut` сохраняет user.
- `issue_session(user: AuthUserDTO, previous_token: str | None = None) -> IssuedAuthSessionOut`.
- `refresh_session(token: str | None, expected_session_id: UUID | None = None) -> RefreshedAuthSessionOut`.
- `revoke_browser_session(session_id: UUID) -> None` — вызывается только после проверки proof из задачи 3, идемпотентно отзывает родителя.
- Repository lookup hash для proof/logout может возвращать историю, но refresh принимает только активное одноразовое поколение.

- [x] Добавить RED-тесты: `test_refresh_keeps_sid_and_rejects_old_token`, `test_login_replaces_only_cookie_session`, `test_failed_password_does_not_revoke_session`, `test_refresh_rejects_expected_sid_mismatch`, `test_refresh_and_logout_never_leave_active_descendant`. Assert: разные браузеры одного user имеют разные sid; после отзыва parent ни одно поколение не активно по правилам сервиса.
- [x] Запустить `python -m pytest utility_service/use_cases/tests/test_auth_session_service.py utility_service/infrastructure/tests/test_auth_session_repository.py` и отдельно новый DB race suite; зафиксировать ожидаемый RED.
- [x] Реализовать порядок parent lock → повторная проверка → credential update/insert; продление TTL родителя только при успешной ротации. Новый login отзывает доступный прежний cookie sid и создаёт новый атомарно. Не использовать detached ORM snapshot как проверку активности после ожидания lock.
- [x] Реализовать тесты настоящих двух DB-транзакций с барьерами, а не sleep: refresh/refresh даёт один успех; refresh/logout в обоих порядках не оставляет действующую сессию после logout; sid другого браузера остаётся действительным.
- [x] Повторить целевые проверки до PASS, убедиться в rollback при ошибке пользователя/создания нового credential и отсутствии продления отозванного parent.

## 3. Access JWT, proof и API status/logout

**Файлы:**

- Создать `apps/backend/utility_service/use_cases/dtos/authenticated_session.py` с `AuthenticatedSession(user: AuthUserDTO, session_id: UUID)` и экспортом в существующем dtos package.
- Создать `apps/backend/utility_service/use_cases/services/auth_session_access_service.py` для актуальных проверок родителя и proof; не раздувать route-функции.
- Создать `apps/backend/utility_service/use_cases/schemas/auth/browser_session_in.py` и `browser_session_out.py` для `BrowserSessionIn(session_id: UUID)` и status/logout responses.
- Изменить `apps/backend/utility_service/web_api/api/auth.py`, `.../use_cases/schemas/auth/auth_success_out.py`, `.../use_cases/deps.py`.
- Изменить `.../web_api/tests/test_auth_api.py`, `test_auth_access.py`, `test_auth_typing_contract.py`, `auth_user_factory.py`; создать `.../use_cases/tests/test_auth_session_access_service.py` и `apps/backend/tests/integration_tests/test_browser_auth_session_access.py`.

**Интерфейсы:** `create_access_token(user_id: str, role: str, session_id: UUID) -> str`; `get_auth_context(...) -> AuthenticatedSession`; существующий `get_current_user(...) -> AuthUserDTO` делегирует context и сохраняет интерфейс ролей. `AuthSuccessOut.session_id: UUID`. `POST /auth/logout` body `BrowserSessionIn`, ответ `{ok: true, session_id}`; `POST /auth/session/status` тот же body, ответ `{session_id, state: "active" | "ended"}`. Refresh получает optional `X-Expected-Session-Id`; отсутствие допустимо только для определения начальной сессии, наличие всегда сверяется сервером.

- [x] Добавить RED-тесты `test_all_access_tokens_rejected_after_logout_commit`, `test_expired_jwt_can_only_read_own_status`, `test_status_requires_proof`, `test_legacy_jwt_without_sid_is_rejected`, `test_status_database_error_is_not_ended`. Assert: expired JWT + active parent → status `active`, business API 401; неверная подпись, неверный sid/sub, неправильный алгоритм не принимаются нигде.
- [x] Добавить RED-тест `test_logout_has_no_set_cookie_and_cannot_revoke_other_sid`; повторный logout отозванного sid допускается только с надлежащим proof. Cookie другого sid не делает операцию разрешённой.
- [x] Запустить `python -m pytest utility_service/web_api/tests/test_auth_api.py utility_service/web_api/tests/test_auth_access.py utility_service/web_api/tests/test_auth_typing_contract.py utility_service/use_cases/tests/test_auth_session_access_service.py` и подтвердить RED.
- [x] Реализовать подписанный sid и auth context. Чтение активности — свежая короткая DB-транзакция без positive cache; не оставлять auth autobegin открытым перед бизнес-`session.begin()`. Роль/активность пользователя остаются текущими серверными данными.
- [x] Реализовать status proof: JWT exp можно игнорировать только в status decoder при корректной подписи, sid/sub и формате; cookie proof проверяется по hash и принадлежности sid. Для logout — неистёкший access JWT либо известный refresh hash в пределах срока родителя; sid без proof не разрешает отзыв. Не использовать `/me` как доказательство отзыва.
- [x] Logout выполняет parent revoke и возвращает результат после commit без Set-Cookie. Status не меняет БД/TTL/cookie и не выдаёт credentials. Ошибка БД — отказ сервиса, не 401/`ended`.
- [x] Обновить все вызывающие `create_access_token` и тестовые fixtures через поиск `rg -n 'create_access_token|jwt.encode' apps/backend`: они создают действующий parent, не bypass. Тестировать запросы после commit logout, изоляцию соседнего sid и отсутствие `transaction already begun` на реальном защищённом use case.
- [x] Повторить целевые unit/API/DB tests до PASS; старый JWT с ещё будущим exp обязательно отклоняется после commit.

## 4. WebSocket admission и отзыв соединений sid

**Файлы:** изменить `apps/backend/utility_service/use_cases/services/websocket_ticket_service.py`, `realtime_connection_manager.py`, `.../infrastructure/postgresql/repositories/websocket_ticket_repository.py`, `.../web_api/api/ws_layers.py`, `.../utils/websocket_ticket_auth.py`, `.../use_cases/deps.py`; расширить существующие ticket/WS tests и создать `apps/backend/tests/integration_tests/test_browser_auth_websocket_revocation.py`.

**Интерфейсы:** `issue_ticket(user: AuthUserDTO, layer_id: UUID, session_id: UUID) -> WebSocketTicketOut`; `WebSocketUserContext.session_id: UUID`; manager `disconnect_session(session_id: UUID) -> None`. Проверка активности sid для connect/send использует короткий read задачи 3, переданный через dependency, а не открытый request AsyncSession после окончания HTTP.

- [x] Добавить RED-тесты `test_revoked_session_ticket_cannot_connect`, `test_logout_between_consume_and_connect_is_rechecked`, `test_disconnect_session_preserves_other_browser`, `test_revoked_session_receives_no_new_admitted_event`. Assert: другой sid того же user остаётся подключён; истечение одного ticket и отзыв parent проверяются раздельно.
- [x] Запустить `python -m pytest utility_service/use_cases/tests/test_websocket_ticket_service.py utility_service/infrastructure/tests/test_websocket_ticket_repository.py utility_service/web_api/tests/test_ws_layers.py` и новый DB suite; подтвердить RED.
- [x] Привязать ticket к sid, сохранить single-use consume и проверки layer/role/user. Перепроверить parent перед admission; описать в тесте точку допуска относительно commit logout.
- [x] После commit logout отключать соединения sid текущего manager; закрытие с ошибкой не откатывает отзыв и не задерживает его результат бесконечно. Перед допуском новой отправки проверять parent, при неактивности/ошибке проверки не отправлять данные. Уже допущенная отправка не объявляется отменённой.
- [x] Повторить проверки; убедиться, что auth не зависит от включённого `LEGACY_GIS_API_ENABLED`. В runbook задачи 8 явно сохранить single-worker границу активного закрытия, не заявлять новый межпроцессный broker.

## 5. Координатор вкладок и status-наблюдение

**Файлы:** создать `apps/frontend/src/auth/browserSessionCoordinator.ts`, `browserSessionCoordinator.test.ts`, `browserSessionMonitor.ts`, `browserSessionMonitor.test.ts`, `browserSessionTypes.ts`; изменить `apps/frontend/src/api/auth.ts`, `auth.test.ts`, `api/http.ts` в объёме typed metadata.

**Интерфейсы:**

- `BrowserSessionMarker = {version: 1; revision: number; sessionId: string; state: "active" | "ended"}`; ключ localStorage `geoservice.auth.session.v1`, channel `geoservice.auth.session.v1`, lock `geoservice.auth.cookie.v1`.
- `runAuthOperation<T>(operation: "login" | "refresh" | "logout", expectedRevision: number | null, action: () => Promise<T>): Promise<T>`: lock timeout 30000 ms, перед callback повторная проверка намерения; при изменении ревизии возвращать typed superseded result/error без HTTP.
- `readSessionMarker(): BrowserSessionMarker | null`, `writeSessionMarker(marker: BrowserSessionMarker): void` — запись только внутри auth lock; parser отвергает неизвестную версию/некорректные поля.
- `fetchSessionStatus(sessionId: string, accessToken?: string): Promise<{session_id: string; state: "active" | "ended"}>`: 1500 ms, caller-managed auth errors, явный старый bearer не перезаписывается interceptor текущим токеном.
- `startSessionMonitor(getContext: () => {sessionId: string; accessToken: string} | null, onEnded: (sessionId: string) => void): () => void`; пауза ≤1000 ms, single in-flight, disposal отменяет дальнейшие callbacks.

- [x] Добавить RED-тесты `serializes_cookie_mutations_across_clients`, `queued_restore_is_skipped_after_logout`, `lock_timeout_never_steals`, `marker_contains_no_secrets`, `missing_broadcast_uses_status`, `stale_status_cannot_end_new_session`.
- [x] Добавить временной тест `old_active_response_does_not_break_five_second_logout`: старый запрос завершён в пределах 1500 ms после отзыва, пауза ≤1000 ms, следующий ended ≤1500 ms, UI callback укладывается в остаток 1000 ms. `active` не отменяет уже известный ended.
- [x] Запустить `npm test -- src/auth/browserSessionCoordinator.test.ts src/auth/browserSessionMonitor.test.ts src/api/auth.test.ts`; подтвердить RED на отсутствующем поведении, не только missing import.
- [x] Реализовать координацию через browser Web Locks, инъецируемые browser ports/clock для тестов. Защита localStorage read/write сама по себе не заменяет атомарный lock. Два fake клиента используют общий lock/storage, но разные listener/store instances.
- [x] Реализовать status monitor и события storage/BroadcastChannel/pageshow/visibility. После resume сначала проверка, затем допуск действий. Недоступный status не означает ended; отсутствие Web Locks/общего storage даёт явную ошибку и не отправляет cookie mutation. Отсутствие BroadcastChannel не блокирует fallback.
- [x] Повторить целевые тесты, добавить задержанные/повреждённые marker, отказ storage и cleanup listeners; убедиться, что нет polling после logout/dispose и нет накопления параллельных запросов.

## 6. Подключение auth store, App и HTTP guards

**Файлы:** изменить `apps/frontend/src/stores/auth.ts`, `apps/frontend/src/api/http.ts`, `apps/frontend/src/api/auth.ts`, `apps/frontend/src/App.vue`, `apps/frontend/src/errors/apiErrorPresentations.ts`; расширить `auth.test.ts`, `auth.epoch.test.ts`, `api/http.test.ts`, `api/auth.restore.integration.test.ts`, `App.restore.test.ts`; создать `apps/frontend/src/stores/auth.multitab.test.ts`.

**Интерфейсы:** auth state получает `sessionId: string | null`; `setAuth(token: string, user: AuthUser, options: SetAuthOptions)` получает обязательный `SetAuthOptions.sessionId: string` и сохраняет существующий optional `preserveWorkOrderStateOnInitialUser`. Все callers/fixtures обновляются. `sessionEpoch` меняется при замене sid даже для того же user. `logout(): Promise<boolean>` возвращает true только при подтверждённом ended, иначе false с сообщением. API login/refresh responses содержат `session_id`; logout адресует ожидаемый sid.

- [x] Добавить RED-тесты `same_user_new_sid_invalidates_old_requests`, `two_restores_do_not_clear_each_other`, `failed_logout_keeps_auth`, `late_old_logout_never_clears_new_login`, `expired_access_401_is_not_global_logout`, `status_of_old_sid_cannot_mutate_current_actor`.
- [x] Запустить `npm test -- src/stores/auth.multitab.test.ts src/stores/auth.test.ts src/stores/auth.epoch.test.ts src/api/http.test.ts src/api/auth.restore.integration.test.ts src/App.restore.test.ts`; подтвердить RED.
- [x] Подключить login/refresh/logout к координатору; выставлять caller-managed error handling для logout/status, чтобы interceptor не очищал store до разбора результата. FE-01 `restoreGeneration` сохранить, не подменять его shared revision или user id.
- [x] При успешном login/restore сверять ожидаемый sid и актуальность local generation; публиковать marker без секретов. Обычный refresh того же sid не сбрасывает рабочий контекст. При shared replacement-login вкладка прекращает использование старого sid и восстанавливает общий новый вход.
- [x] При подтверждённом logout опубликовать ended и очистить локальный вход; при timeout/network unknown проверить именно sid через status. Не трактовать expiry access JWT как успешный logout. Не исполнять автоматический отложенный logout после нового login.
- [x] Сохранить существующие экраны ожидания/retry; добавить сообщения согласованной ошибки выхода и неопределённого результата. Startup с ended marker не восстанавливает отозванную cookie; явный login создаёт новую ревизию. При пропущенном marker начальный refresh определяет sid на сервере.
- [x] Проверить late Set-Cookie случая после timeout: expected sid/response guard не позволяют установить чужой/отозванный аккаунт; повторный login при фактической потере credential допустим. Не объявлять generation guard защитой порядка HTTP cookie.
- [x] Повторить целевые проверки и `npm run typecheck`; новый sid виден во всех fixtures, старый bearer для status не заменяется текущим в request interceptor.

## 7. Подготовка выхода без преждевременной потери workspace

**Файлы:** изменить `apps/frontend/src/stores/workOrders.ts`, `workspaceRecovery.ts`, при необходимости `components/WorkspaceNavigationDialog.vue`; расширить `workOrders.navigation.test.ts`, `workspaceRecovery.test.ts`; создать `apps/frontend/src/stores/workOrders.logout.test.ts`.

**Интерфейсы:** `workspaceRecovery.prepareActorLogout(actorId: string): Promise<boolean>` проверяет/обеспечивает durable sent-intent без `access` suspension и без hideActor. Существующий `suspendActor` остаётся финальной обработкой доказанной потери доступа. `workOrders.prepareLogout(): Promise<boolean>` использует новую подготовку; `performNavigation` учитывает boolean `auth.logout()` из задачи 6.

- [x] Добавить RED-тесты `failed_logout_preserves_workspace_and_pending_identity`, `successful_logout_suspends_sent_intent`, `recovery_storage_error_prevents_managed_logout`, `explicit_discard_stays_discarded_after_logout_error`, `remote_browser_session_logout_does_not_autosave_dirty`.
- [x] Запустить `npm test -- src/stores/workOrders.logout.test.ts src/stores/workOrders.navigation.test.ts src/stores/workspaceRecovery.test.ts`; подтвердить RED текущей преждевременной suspension.
- [x] Разделить подготовку и финальный access-loss. Во время logout временно блокировать новые изменения инициатора без очистки draft; отказ запроса возвращает возможность работы. Сохранить существующие разрешения dirty/sent/stale до запроса.
- [x] После ended в соседних вкладках прекратить доступ без ожидания пользовательского подтверждения. Не сохранять dirty автоматически; frozen payload и CommandId отправленной команды не заменять и не считать её отменённой. Новый login не запускает новую mutation по старому намерению.
- [x] Повторить целевые тесты; отдельно открыть один WorkOrder двумя независимыми stores и подтвердить отсутствие новой межвкладочной блокировки.

## 8. Сквозная проверка, миграционный runbook и отчёт

**Файлы:** создать `docs/sprint_2/ar-01/smoke.mjs`, `docs/sprint_2/2026-10-27-ar-01-browser-session-runbook.md`, `docs/sprint_2/2026-10-27-ar-01-browser-session-implementation-report.md`; evidence в `docs/sprint_2/evidence/ar-01/`; по результатам изменить `docs/sprint_2/README.md`, `architecture-realtime-review.md`, `2026-10-26-deep-code-review.md`. API/DB fixtures из других suites изменяются только где нужен реальный sid.

**Интерфейсы runner:** `node docs/sprint_2/ar-01/smoke.mjs --browser chrome|msedge|firefox --origin <isolated-origin> --output <evidence-dir>`. Использовать существующий `@playwright/test` через `infra/m4/package.json`. Для Chrome/Edge — соответствующие installed channels; для Firefox фиксировать фактический executable/version, не выдавать Chromium или иной выпуск за актуальный Firefox. При отсутствии нужного браузера оставить gate незакрытым, не подменять его.

- [x] Подготовить реальный изолированный frontend/backend/DB по подходу INF-02; не использовать рабочие demo volumes. Настроить задержки/потери ответов на тестовом proxy/runner, не добавлять production debug endpoints. Secrets находятся только в памяти runner.
- [x] Прогнать один общий context с двумя/несколькими pages: одновременный reload/restore, новый tab, закрытие инициатора, successful logout и предел 5 секунд, потерянный marker, старый active status. API ротация реальная, не route-fulfill mock.
- [x] Проверить два независимых contexts и отдельные browsers одного user: выход одного не затрагивает другой. Скопированные в память runner access JWT/refresh/ticket отозванного sid больше не дают доступ после commit; результаты сохранять только как boolean/status assertions.
- [x] Проверить недоставленный logout, commit с потерянным ответом, поздний старый logout после нового login, lost rotated token, resume вкладки, FE-01 retry screen и late responses. Один WorkOrder в двух вкладках открывается; существующий stale guard работает без новой блокировки.
- [x] Прогнать миграцию чистой/legacy БД и весь `infra/db-tests.cmd`; затем backend suite, lint/format и prod build по существующим CI-командам. Проверить, что DB tests выполнены, а не пропущены.
- [x] Выполнить frontend regression:

```powershell
npm test
npm run typecheck
npm run lint
npm run build
```

- [x] Проверить форматирование только изменённых frontend-файлов локальным Prettier; backend `black --check .`, `ruff check .`, `python -m pytest` в dev-среде. Из корня проверить prod build: `docker build --target prod -t geoservice-ar01-backend-prod apps/backend`. Исправления чужих исходных проблем не добавлять молча.
- [x] Записать runbook: однократный повторный login, совместное обновление frontend/backend, отсутствие rolling mixed auth, недействительная cookie после logout, status polling/нагрузка, single-worker граница активного WS close, процедура проверки sid без логирования secrets. CI не переписывать ради нового отчёта.
- [x] Записать фактические browser versions, timings, SQL race outcomes и ограничения в отчёт. Артефакты с токенами, cookie, паролями не сохранять. Отметить невыполненные gates честно; отсутствие браузера/БД не считается успешной приёмкой.
- [x] Выполнить `git diff --check`, проверить UTF-8/LF у tracked и untracked файлов. Сверить diff: нет WorkOrder lock, global logout, replay grace или обхода sid checks в tests.
- [x] После всех gates обновить статус AR-01 и регистр находок. Оценить новое долговечное знание для Code_wiki и только при наличии такого знания применить `/ingest repository-change`; не дублировать дизайн в agent memory. Оставить все изменения unstaged для пользователя.

## Самопроверка плана

- Схема/legacy migration — задача 1; single-use rotation и конкуренция — 2; access/status/logout proof — 3; ticket/WS — 4.
- Межвкладочная сериализация, сроки и отказ API — 5; sid/generation/HTTP/UI — 6; сохранность work intent — 7; реальные браузеры/DB/regression/deployment — 8.
- Все пять пунктов фокуса имеют явные тесты в соответствующих задачах. Непроверенные runtime-гарантии не объявляются подтверждёнными этим документом.
- Backend DTO использует `session_id: UUID`, JSON/frontend — UUID string `session_id`; state/marker frontend — `sessionId`. `sid` — claim JWT. Это разные уровни именования одного идентификатора, не разные identity.
- Проверка подписи JWT с expired exp разрешена только status endpoint; logout и рабочий доступ не наследуют это исключение.
- Все задачи имеют RED → реализация → GREEN. Миграция и интеграция не выкатываются по частям; agent Git writes запрещены. По поручению пользователя начато поэтапное исполнение с отдельными implementer/reviewer.
