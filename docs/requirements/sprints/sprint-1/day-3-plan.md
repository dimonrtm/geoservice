# День 3: реализация backend login flow

## Цель дня

- Реализовать рабочий backend login flow по `email + password`.
- Использовать инфраструктуру Day 2 без изменения публичных контрактов Sprint 1.
- Закрыть негативные `401` для `POST /api/v1/auth/login` и `GET /api/v1/auth/me`.
- Довести backend auth до состояния, в котором production login реально работает, а `dev-login` остаётся только dev-only механизмом.

## Результат дня

- Существует `POST /api/v1/auth/login`.
- Backend ищет пользователя по email и проверяет `password_hash`.
- Успешный login возвращает JWT и объект `user`.
- `GET /api/v1/auth/me` и `POST /api/v1/auth/login` согласованы по форме `user`.
- `dev-login` остаётся отдельным dev-only маршрутом.

## Входная база Day 3

- Подготовлены схемы:
  - `AuthLoginIn`
  - `AuthUserOut`
  - `AuthSuccessOut`
  - `AuthMeOut`
- Подготовлен password utility:
  - `hash_password(...)`
  - `verify_password(...)`
- Усилена backend-конфигурация через `Settings`.
- `GET /api/v1/auth/me` уже нормализован под `user { id, email, role }`.

## Задачи

1. Подключить `AuthLoginIn` и `AuthSuccessOut` в `api/auth.py`.
2. Добавить production login endpoint `POST /api/v1/auth/login`.
3. Реализовать в `AuthService` метод аутентификации через `email` и `password`.
4. Использовать `UserRepository.get_by_email(...)` как lookup для normal login.
5. Использовать `verify_password(...)` из `password_service`.
6. При невалидных credentials возвращать единый `401` без утечки причины.
7. Использовать существующий `create_access_token(...)` без изменения JWT payload.
8. Возвращать `AuthSuccessOut` с полями `access_token`, `token_type`, `user`.
9. Проверить, что `GET /api/v1/auth/me` остаётся совместимым с login response.
10. Не изменять `POST /api/v1/auth/dev-login`, кроме возможной чистки формулировок или импортов.

## Контракт реализации

### `POST /api/v1/auth/login`

- Request schema: `AuthLoginIn`
- Success response model: `AuthSuccessOut`
- Data flow:
  - `email`
  - `UserRepository.get_by_email(...)`
  - `verify_password(...)`
  - `create_access_token(...)`
  - `AuthSuccessOut`

### Правила ответа

- `200 OK`:
  - `access_token`
  - `token_type="bearer"`
  - `user { id, email, role }`
- `401 Unauthorized` с `detail="Invalid email or password"` при несуществующем email
- `401 Unauthorized` с тем же сообщением при неверном пароле
- `401 Unauthorized` с тем же сообщением при `password_hash is None`
- Login endpoint не раскрывает, существует ли пользователь.
- Для `GET /api/v1/auth/me` случай валидного JWT с отсутствующим пользователем в БД трактуется как `401 Invalid or expired token`, а не `404`.

## Решения по реализации

- Normal login использует только таблицу `users`.
- Пароль сравнивается только через `verify_password(...)`.
- Если `password_hash is None`, login завершается `401`.
- Для невалидных credentials не требуется отдельное доменное исключение; допустимо возвращать `HTTPException(401)` прямо из auth-слоя.
- `token_type` всегда `"bearer"`.
- Никаких refresh tokens, cookies и session storage на backend не добавлять.
- Никаких новых auth env vars и миграций в Day 3 не добавлять.

## Разделение границ

### Day 3 против Day 2

- Day 2 готовит инфраструктуру.
- Day 3 реализует login endpoint и backend orchestration.

### Day 3 против Day 4

- Day 3 не создаёт seed users.
- Day 4 делает demo/local воспроизводимость логина.

## Ограничения дня

- Без seed users.
- Без frontend изменений.
- Без realtime.
- Без истории, аналитики и `Project`.
- Без расширения ролей beyond `viewer/editor`.

## Проверки

### Service/unit tests

- `AuthService.authenticate_user(...)` возвращает `User` при валидной паре;
- выбрасывает контролируемую auth-ошибку при неверных credentials;
- возвращает `401 Invalid email or password` при `password_hash is None`;
- не переиспользует `get_dev_user(...)` для production path.
- Нормализация `/me` проверяется на уровне auth-логики и текущего route contract без обязательного route-level integration в рамках Day 3.

### Verification notes

- Перед финальной реализацией и проверкой нужно пересобрать `geoservice-backend:dev`, чтобы в образ попал `bcrypt==4.0.1`.
- Day 2 password tests должны быть зелёными после rebuild, иначе Day 3 блокируется на dependency-уровне.
- Route-level API/integration tests для `POST /api/v1/auth/login` и `GET /api/v1/auth/me` не являются обязательной частью Day 3 и могут быть добраны позже в рамках integration-этапа Sprint 1.

## Definition of Done для Дня 3

- Реализован `POST /api/v1/auth/login`.
- Backend умеет аутентифицировать пользователя по `email + password`.
- Успешный login выдаёт JWT по уже зафиксированному контракту Sprint 1.
- Негативные сценарии login возвращают контролируемый `401`.
- `GET /api/v1/auth/me` остаётся согласованным с login response.
- Случай `password_hash is None` обрабатывается как обычный `401 Invalid email or password`.
- Случай отсутствующего пользователя для `sub` из JWT обрабатывается как `401 Invalid or expired token`.
- `dev-login` не смешивается с production login path.
- Документация Sprint 1 при необходимости синхронизирована с уточнённой backend-последовательностью обработки login.
