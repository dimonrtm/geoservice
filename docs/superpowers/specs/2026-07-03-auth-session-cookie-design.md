# Убрать долгоживущий access token из localStorage

Дата: 2026-07-03
Статус: design approved
Источник: security backlog по хранению `access_token` в `localStorage`

## Контекст

Текущий frontend хранит `access_token` и `auth_user` в `localStorage` через
`apps/frontend/src/stores/auth.ts`. Axios interceptor в
`apps/frontend/src/api/http.ts` берет token из Pinia и добавляет
`Authorization: Bearer ...` ко всем REST запросам. При старте приложение
вызывает `restoreSession()`, читает token из `localStorage` и проверяет его
через `GET /api/v1/auth/me`.

Backend в `apps/backend/utility_service/web_api/api/auth.py` выдает stateless
JWT access token с TTL из `ACCESS_TOKEN_TTL_MIN`, по умолчанию 30 минут.
Refresh/session endpoint сейчас нет. WebSocket realtime уже вынесен из JWT
query string в short-lived DB-backed ticket flow, поэтому в проекте есть
подходящий паттерн: raw credential возвращается только клиенту, а в БД хранится
только SHA-256 hash.

`localStorage` делает access token переживающим reload и restart браузера и
оставляет его доступным любому XSS в origin приложения. Цель изменения - убрать
долгоживущий access token из JS-хранилища, но сохранить удобство входа в
пределах рабочей смены.

## Цели

- Убрать `access_token` из `localStorage`.
- Хранить access token только in-memory в Pinia.
- Сохранить вход после reload/restart браузера на 8-12 часов рабочей смены.
- Использовать server-side session cookie с `HttpOnly` credential.
- Сохранить текущий Bearer-контракт REST API и WebSocket ticket flow.
- Сделать logout отзывом server-side session, а не только очисткой frontend
  state.

## Не Цели

- Не переводить все REST endpoints на cookie-auth вместо Bearer.
- Не добавлять полноценный OAuth/OIDC или SSO.
- Не добавлять refresh token в JSON response.
- Не хранить raw session token в БД.
- Не менять authorization rules для layers/features/work orders/realtime.
- Не делать silent refresh внутри общего axios response interceptor в первом
  slice.

## Выбранный Подход

Выбран DB-backed persistent session на 12 часов и короткий access JWT только в
памяти frontend.

Login создает opaque session token, backend кладет его в `HttpOnly` cookie, а в
БД сохраняет только hash. JSON response по-прежнему возвращает короткий
`access_token` и user DTO, чтобы существующие REST guards и frontend API
продолжили работать через `Authorization: Bearer ...`.

При reload frontend стартует без access token и вызывает
`POST /api/v1/auth/session/refresh` с cookie. Backend валидирует session,
ротирует session token, ставит новую cookie и возвращает новый access token +
user. Если cookie отсутствует, истекла или отозвана, frontend показывает login
без тревожного сообщения об ошибке.

## Альтернативы

### Signed Refresh JWT В HttpOnly Cookie

Этот вариант проще по backend-коду и не требует таблицы sessions, но хуже
управляет отзывом конкретной сессии и rotation. Если cookie будет
скомпрометирована, backend не сможет надежно инвалидировать отдельный refresh
credential без отдельного denylist.

### Полностью Cookie-Based Session Для REST

Этот вариант убирает access token из JavaScript полностью: все REST запросы
авторизуются cookie. Но тогда нужно проектировать CSRF защиту для state-changing
запросов, менять `get_current_user`, CORS credentials и тесты шире текущего
security slice.

## Backend Дизайн

### Модель И Миграция

Добавить таблицу `user.auth_sessions`:

- `id UUID primary key`;
- `session_token_hash varchar(64) not null unique`;
- `user_id UUID not null`;
- `expires_at timestamptz not null`;
- `revoked_at timestamptz null`;
- `rotated_at timestamptz null`;
- `last_used_at timestamptz null`;
- `created_at timestamptz not null default now()`.

Индексы:

- unique index/constraint по `session_token_hash`;
- index по `expires_at`;
- index по `user_id`.

Foreign key к `user.users.id` можно добавить, если текущие миграции стабильно
создают schema/table в нужном порядке; если локальный стиль auth моделей пока
не использует FK, лучше не вводить отдельное отличие только ради sessions.

### Repository И Service

`AuthSessionRepository` отвечает за операции хранения:

- create session hash;
- найти active session по hash с `revoked_at IS NULL` и `expires_at > now`;
- revoke session;
- rotate session atomically: отозвать старую session и создать новую в одной DB
  transaction;
- обновить `last_used_at`.

`AuthSessionService` отвечает за security semantics:

- генерирует raw session token через `secrets.token_urlsafe(32)` или сильнее;
- хеширует token через SHA-256, аналогично WebSocket tickets;
- применяет TTL 12 часов;
- формирует cookie параметры;
- валидирует активность пользователя при refresh.

### Auth API

`POST /api/v1/auth/login`

- Проверяет email/password через текущий `AuthService`.
- Создает server-side session.
- Ставит `Set-Cookie` с raw session token.
- Возвращает текущий `AuthSuccessOut`: `access_token`, `token_type`, `user`.

`POST /api/v1/auth/session/refresh`

- Читает session cookie.
- Если cookie отсутствует, истекла, отозвана или не найдена, возвращает
  structured `401 AUTH_REQUIRED`.
- Если session валидна, перечитывает пользователя, проверяет `is_active` и
  role.
- Ротирует session token.
- Ставит новый `Set-Cookie`.
- Возвращает новый `access_token`, `token_type`, `user`.

`POST /api/v1/auth/logout`

- Читает session cookie, если она есть.
- Отзывает найденную active session.
- Всегда очищает cookie.
- Возвращает success response даже при отсутствующей или уже отозванной
  session.

`GET /api/v1/auth/me`

- Остается Bearer-based и использует текущий `get_current_user`.

### Cookie И CORS

Cookie:

- name: `geoservice_session`;
- `HttpOnly`;
- `SameSite=Lax`;
- `Path=/api/v1/auth`;
- `Max-Age=43200`;
- `Secure=true` для production/HTTPS;
- dev setting должен позволять localhost без Secure.

`CORSMiddleware` должен разрешать credentials для configured frontend origins,
иначе browser не примет и не отправит session cookie. `allow_origins` остается
явным списком из settings; wildcard origins с credentials не используются.

Settings:

- `AUTH_SESSION_TTL_HOURS=12`;
- `AUTH_SESSION_COOKIE_NAME=geoservice_session`;
- `AUTH_SESSION_COOKIE_SECURE` или environment-aware secure flag;
- при необходимости `AUTH_SESSION_COOKIE_SAMESITE=lax`.

Access token TTL можно оставить текущим `ACCESS_TOKEN_TTL_MIN` на первом шаге.
Если хотим еще сильнее сократить риск in-memory token, отдельным follow-up можно
уменьшить его до 5-15 минут и добавить silent refresh по 401.

## Frontend Дизайн

`apps/frontend/src/stores/auth.ts` перестает читать и писать `access_token` в
`localStorage`. `token` и `user` становятся in-memory state. `auth_user` тоже
не сохраняется в `localStorage`, чтобы source of truth при старте был только
`/session/refresh`.

`loginWithPassword()`:

1. вызывает `login(email, password)`;
2. browser получает `HttpOnly` cookie из `Set-Cookie`;
3. store кладет `access_token` и user только в Pinia;
4. `isReady=true`.

`restoreSession()`:

1. не читает web storage;
2. вызывает `refreshSession()`;
3. при успехе кладет новый access token и user в Pinia;
4. при `401 AUTH_REQUIRED` очищает state и показывает login;
5. при временной ошибке без `401` сохраняет текущую retry UX модель с
   `sessionError`.

`logout()` становится async flow:

1. вызывает `logoutSession()` best-effort;
2. очищает Pinia state;
3. сбрасывает связанные stores при смене user id на null.

Если logout endpoint недоступен, frontend все равно должен очистить локальное
state, но ошибка может быть записана только в dev diagnostics, без показа
пользователю.

`apps/frontend/src/api/auth.ts` добавляет:

- `refreshSession()`;
- `logoutSession()`.

Эти requests должны отправляться с credentials. Это можно сделать либо через
`http.defaults.withCredentials = true`, либо через опцию
`{ withCredentials: true }` только для session endpoints. Для меньшего blast radius предпочтительнее
включить credentials только на auth session endpoints.

`apps/frontend/src/api/http.ts` сохраняет Bearer interceptor: все защищенные
REST endpoints и WebSocket ticket issue endpoint продолжают получать access
token из Pinia.

## Потоки

### Login

1. Пользователь вводит email/password.
2. Backend проверяет пароль.
3. Backend создает `auth_sessions` row с hash session token.
4. Backend ставит `HttpOnly` cookie на 12 часов.
5. Backend возвращает access token + user.
6. Frontend хранит access token только in-memory.

### Reload Или Restart Браузера

1. Frontend стартует без token.
2. `restoreSession()` вызывает `/api/v1/auth/session/refresh` с cookie.
3. Backend валидирует и ротирует session.
4. Backend возвращает новый access token + user.
5. Frontend продолжает работу как authenticated user.

### Logout

1. Frontend вызывает `/api/v1/auth/logout` с cookie.
2. Backend отзывает active session, если нашел ее.
3. Backend очищает cookie.
4. Frontend чистит in-memory auth state и связанные stores.

### REST И Realtime

Обычные REST запросы продолжают идти с `Authorization: Bearer <access_token>`.
`POST /api/v1/ws/layers/{layer_id}/ticket` тоже остается Bearer-based. Сам
WebSocket flow с short-lived ticket не меняется.

## Обработка Ошибок

- Missing/expired/revoked session cookie на refresh возвращает structured
  `401 AUTH_REQUIRED`; frontend трактует это как обычное logged-out состояние.
- Временные ошибки refresh, например `503`, показывают существующий экран
  "не удалось восстановить сессию" с retry/logout actions.
- Logout идемпотентен: отсутствующая cookie или уже отозванная session не
  превращаются в пользовательскую ошибку.
- Любой REST `401` по-прежнему очищает frontend auth state.
- Inactive user на refresh возвращает `403 USER_INACTIVE`, frontend очищает
  state и показывает login/error по существующей модели auth errors.
- Повторное использование старой rotated cookie возвращает `401 AUTH_REQUIRED`.

## Тестирование

Backend:

- unit tests для генерации и SHA-256 hash session token;
- repository tests для active/expired/revoked lookup;
- service tests для create, refresh rotation, revoke/logout idempotency;
- API tests: login sets `Set-Cookie` и не возвращает refresh token в JSON;
- API tests: refresh rotates cookie и возвращает новый access token;
- API tests: missing/expired/revoked/rotated cookie возвращает structured
  `401 AUTH_REQUIRED`;
- API tests: logout clears cookie и отзывает session;
- security/CORS contract tests для `HttpOnly`, `SameSite`, `Path`, `Max-Age`,
  `Secure` по setting и `allow_credentials=True`.

Frontend:

- auth store tests: login не пишет `access_token` в `localStorage`;
- auth store tests: restore вызывает refresh endpoint, а не читает storage;
- auth store tests: `401` refresh переводит в logged-out без `sessionError`;
- auth store tests: временная ошибка refresh сохраняет retry UX;
- auth store tests: logout очищает state после best-effort backend logout;
- API tests: session endpoints отправляют credentials;
- HTTP interceptor tests: Bearer header строится из in-memory token.

Regression:

- существующие WebSocket ticket tests должны остаться Bearer-based и пройти без
  изменения realtime контракта.

## Риски И Последствия

- Нужно включить CORS credentials для auth session endpoints. При неверных
  origins browser не сохранит cookie, а session restore будет постоянно
  возвращать logged-out.
- `SameSite=Lax` подходит для same-site/local app flow. Если production
  frontend/backend будут на cross-site доменах, понадобится `SameSite=None` +
  `Secure=true` и более строгая CSRF оценка.
- Пока silent refresh по 401 вне scope, истекший in-memory access token в
  середине открытой вкладки приведет к logout. Это приемлемо для первого slice,
  потому что главная цель - убрать persistent access token из storage.
- Rotation делает украденную старую cookie бесполезной после refresh, но при
  реальном XSS во время активной вкладки attacker все еще может вызывать API от
  имени пользователя. Этот дизайн снижает persistence риска, но не заменяет XSS
  hardening.

## Критерии Приемки

- После login `localStorage.getItem("access_token")` не содержит token.
- После reload в течение 12 часов пользователь восстанавливается через
  `/api/v1/auth/session/refresh`.
- После logout refresh больше не восстанавливает пользователя.
- Backend не хранит raw session token в БД.
- `Set-Cookie` содержит `HttpOnly`, `SameSite`, `Path=/api/v1/auth` и
  12-часовой lifetime.
- REST и WebSocket ticket issue endpoints продолжают работать через Bearer
  access token.
