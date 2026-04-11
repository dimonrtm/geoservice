# День 2: усиление backend auth-конфигурации

## Цель дня

- Сделать `JWT_SECRET` обязательным вне dev-режима.
- Подготовить backend к `email + password` login.
- Зафиксировать единый способ проверки пароля.
- Явно развести `dev-login` и production login на уровне конфигурации и кода.
- Подготовить базу для Day 3 без реализации полного login flow.

## Результат дня

- В `settings` зафиксировано правило: backend не стартует в non-dev режиме с пустым или дефолтным `JWT_SECRET`.
- Есть backend-схемы для будущих `POST /api/v1/auth/login` и нормализованного `GET /api/v1/auth/me`.
- Выбран и зафиксирован единый парольный механизм: `passlib[bcrypt]`.
- Есть отдельный backend utility/service для `verify_password(...)` и `hash_password(...)`.
- Явно определена граница: `POST /api/v1/auth/dev-login` остаётся только для `DEV_MODE=true`, production login не зависит от dev-механики.
- Документация и Sprint 1 contract baseline не смешивают `dev-login` с рабочим auth flow.

## Задачи

1. Проверить текущую конфигурацию `JWT_SECRET` и зафиксировать риск дефолтного значения `CHANGE_ME_IN_ENV`.
2. Добавить правило валидации settings: если `DEV_MODE=false`, то `JWT_SECRET` должен быть непустым и не равным `CHANGE_ME_IN_ENV`.
3. Не вводить новые обязательные auth env vars в Day 2, кроме использования уже существующего `JWT_SECRET`.
4. Подготовить Pydantic-схему входа для `POST /api/v1/auth/login`:
   - `email`
   - `password`
5. Подготовить общую Pydantic-схему ответа пользователя:
   - `user.id`
   - `user.email`
   - `user.role`
6. Подготовить общую Pydantic-схему auth-ответа:
   - `access_token`
   - `token_type`
   - `user`
7. Добавить password utility/service с `hash_password(...)` и `verify_password(...)` на `passlib[bcrypt]`.
8. Зафиксировать, что `AuthService` в Day 2 только получает инфраструктуру для normal login, а сам login endpoint и orchestration остаются задачей Day 3.
9. Явно отделить `get_dev_user(...)` от будущего production login path:
   - `dev-login` не переиспользуется как backend-реализация обычного login;
   - normal login будет работать через поиск пользователя по email и проверку `password_hash`.
10. Обновить docs формулировками о границе между `dev-login` и production auth.

## Конфигурационные правила

### `DEV_MODE=true`

- `POST /api/v1/auth/dev-login` может быть включён.
- `JWT_SECRET` может оставаться локальным dev-секретом, но не должен использоваться как production guidance.

### `DEV_MODE=false`

- backend обязан падать на старте при пустом `JWT_SECRET`;
- backend обязан падать на старте при `JWT_SECRET=CHANGE_ME_IN_ENV`;
- normal login остаётся единственным рабочим auth flow.

### Прочие правила

- `ACCESS_TOKEN_TTL_MIN` и `JWT_ALG` в Day 2 не меняются по контракту.
- Day 2 не меняет JWT payload: остаются `sub`, `role`, `iat`, `exp`.

## Подготовленные интерфейсы

### Login input schema

- `email: string`
- `password: string`

### Auth user schema

- `id: string`
- `email: string`
- `role: "viewer" | "editor"`

### Auth success schema

- `access_token: string`
- `token_type: "bearer"`
- `user: AuthUser`

### Password utility interface

- `hash_password(plain_password: str) -> str`
- `verify_password(plain_password: str, password_hash: str | None) -> bool`

## Решения по реализации

- Парольный механизм: `passlib[bcrypt]`.
- Хранение пароля:
  - в БД продолжает использоваться поле `users.password_hash`;
  - plaintext пароль нигде не хранится.
- При `password_hash is None` проверка пароля должна возвращать `False`, а не падать исключением.
- Day 2 не добавляет seed пользователей и не мигрирует данные; это остаётся задачей Day 4.
- Day 2 не реализует сам `POST /api/v1/auth/login`; он только готовит инфраструктуру для Day 3.
- `dev-login` остаётся отдельным dev-only механизмом и не используется как часть production auth pipeline.

## Проверки

### Позитивная проверка

- settings загружаются при `DEV_MODE=true` и локальном секрете.

### Негативные проверки

- settings падают при `DEV_MODE=false` и `JWT_SECRET=CHANGE_ME_IN_ENV`;
- settings падают при `DEV_MODE=false` и пустом `JWT_SECRET`.

### Unit checks

- `hash_password(...)` возвращает непустой hash;
- `verify_password(...)` возвращает `True` для правильной пары;
- `verify_password(...)` возвращает `False` для неверного пароля;
- `verify_password(...)` возвращает `False`, если `password_hash is None`.

### Contract checks

- схемы login/auth согласованы с уже зафиксированными в [sprint-1-plan.md](/C:/Repositories/geoservice/docs/requirements/sprints/sprint-1/sprint-1-plan.md) контрактами;
- Day 2 не добавляет новых публичных auth endpoint'ов.

## Definition of Done для Дня 2

- В backend зафиксирована безопасная граница для `JWT_SECRET`.
- Подготовлены все backend-схемы, нужные для Day 3 login flow.
- В коде есть единый utility/service для hash/verify пароля.
- `dev-login` и production login разведены концептуально и на уровне архитектуры.
- Документация Sprint 1 не допускает трактовку `dev-login` как production-ready auth.
