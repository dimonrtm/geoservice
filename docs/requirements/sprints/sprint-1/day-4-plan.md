# День 4: seed demo-пользователей и воспроизводимый login через Docker Compose

## Цель дня

- Сделать локальный и demo-сценарий входа воспроизводимым без `dev-login`.
- Добавить idempotent seed demo-пользователей для `email + password`.
- Встроить seed-поток в compose/startup так, чтобы пользователи появлялись после `alembic upgrade`.
- Обновить документацию запуска и demo-flow под новый backend login path.

## Результат дня

- Локально через `docker compose` создаются предсказуемые demo-пользователи.
- Пользователь может войти через `POST /api/v1/auth/login` без зависимости от `POST /api/v1/auth/dev-login`.
- Seed выполняется идемпотентно и не создаёт дубликаты пользователей.
- Если demo-пользователь уже существует, seed приводит его к ожидаемому demo baseline по роли и `password_hash`.
- Seed не зависит от `postgis/init`, а запускается только после появления таблицы `users`.
- Документация содержит явные demo-credentials и шаги проверки login flow.

## Входная база Day 4

- Day 2 подготовил:
  - security-валидацию `JWT_SECRET`
  - auth-схемы
  - password utility на `passlib[bcrypt]`
- Day 3 подготовил:
  - рабочий backend `POST /api/v1/auth/login`
  - нормализованный `GET /api/v1/auth/me`
  - production auth path через `users.password_hash`
- Текущий `docker-compose` поднимает PostGIS и backend, а backend уже делает `alembic upgrade head` перед запуском приложения.

## Ключевое решение

- Seed demo-пользователей нужно делать на backend-стороне после `alembic upgrade`, а не через `infra/docker/postgis/init`.
- Причина:
  - `postgis/init` выполняется при инициализации контейнера Postgres;
  - таблица `users` создаётся Alembic-миграцией позже;
  - значит raw SQL seed в `postgis/init` не является надёжной точкой для demo users.

## Задачи

1. Добавить backend seed-механику для demo-пользователей после миграций.
2. Сделать seed идемпотентным:
   - если пользователь уже существует, не создавать дубликат;
   - если пользователь существует без `password_hash`, обновлять hash и роль до ожидаемого demo-состояния.
3. Использовать существующий `hash_password(...)` для записи `password_hash`.
4. Зафиксировать минимальный набор demo-пользователей:
   - `editor@example.com` / `editor-password` / `editor`
   - `viewer@example.com` / `viewer-password` / `viewer`
5. Не добавлять отдельный UI flow для выбора demo users; Day 4 закрывает только backend/demo bootstrap.
6. Встроить запуск seed в backend startup после `alembic upgrade`.
7. Не поддерживать параллельно второй механизм seed для Day 4.
8. Обновить `README.md` и релевантные sprint/docs материалы так, чтобы demo login можно было воспроизвести по шагам.

## Решение по реализации

### Основной вариант

- Добавить backend seed script/module, который:
  - открывает DB session;
  - ищет пользователей по email;
  - создаёт или обновляет их в соответствии с demo baseline;
  - использует `hash_password(...)`;
  - завершает работу без ошибок при повторном запуске.

### Точка запуска

- Предпочтительный путь: вызывать seed после `alembic upgrade head` и до `uvicorn main:app` в backend compose command.
- Причина:
  - использует уже существующий backend startup path;
  - не требует дополнительного compose service для Day 4;
  - проще для локального demo “одной командой”.

### Почему не через `postgis/init`

- Там ещё нет таблицы `users`.
- Это создаёт хрупкую зависимость от порядка инициализации Postgres и Alembic.

## Demo baseline

### Seed users

- `editor@example.com`
  - password: `editor-password`
  - role: `editor`
- `viewer@example.com`
  - password: `viewer-password`
  - role: `viewer`

### Правила seed

- Email является естественным ключом demo baseline.
- Повторный seed не должен создавать вторую запись.
- Если у пользователя уже есть запись с тем же email, Day 4 должен приводить её к ожидаемому demo-состоянию:
  - обновлять `password_hash`;
  - обновлять роль;
  - не оставлять частично dev-login-конфигурацию.

## Ограничения дня

- Без frontend login screen.
- Без realtime.
- Без integration-suite уровня Sprint 1.
- Без истории, аналитики и `Project`.
- Без полноценного user management UI или admin CRUD по пользователям.
- Без дополнительных auth env vars, если они не нужны строго для demo seed.

## Проверки

### Seed checks

- Повторный запуск seed не создаёт дубликаты.
- После seed в БД существуют:
  - один `editor@example.com`
  - один `viewer@example.com`
- У обоих пользователей заполнен `password_hash`.
- Роли соответствуют demo baseline.

### Login checks

- `POST /api/v1/auth/login` успешен для `editor@example.com / editor-password`.
- `POST /api/v1/auth/login` успешен для `viewer@example.com / viewer-password`.
- `GET /api/v1/auth/me` возвращает корректный `user` после login.
- Локальный сценарий входа проходит без `POST /api/v1/auth/dev-login`.

### Compose checks

- `docker compose up` поднимает backend в состоянии, пригодном для login demo.
- Seed выполняется после миграций и не ломает startup.
- Повторный restart backend не ломает состояние demo users.

### Docs checks

- В `README.md` или связанной документации есть:
  - шаги запуска;
  - demo credentials;
  - краткий способ проверить login и `/me`.

## Demo-сценарий дня

1. Запустить сервисы через `docker compose`.
2. Дождаться выполнения миграций и seed.
3. Выполнить `POST /api/v1/auth/login` для `editor@example.com`.
4. Получить `access_token`.
5. Выполнить `GET /api/v1/auth/me` с этим токеном.
6. Повторить login для `viewer@example.com`.
7. Убедиться, что `dev-login` для этого сценария не требуется.

## Definition of Done для Дня 4

- Demo-пользователи создаются автоматически в локальном compose-сценарии.
- Login через `email + password` воспроизводим без ручного наполнения БД.
- Seed идемпотентен.
- Seed, при необходимости, приводит существующих demo-пользователей к ожидаемому baseline по роли и паролю.
- `README.md` и sprint-документация отражают новый demo login flow.
- Day 4 не смешивает demo seed с frontend login или realtime-задачами следующих дней.

## Assumptions

- План дня 4 должен повторять стиль `day-1-plan.md`, `day-2-plan.md` и `day-3-plan.md`.
- Для demo baseline достаточно двух пользователей: `editor` и `viewer`.
- Пароли demo-пользователей допустимо хранить только в документации и в seed input как plaintext, но в БД они попадают только в виде hash.
- Для Day 4 приоритетнее воспроизводимость локального demo, чем универсальная enterprise-конфигурация seed-механизма.
