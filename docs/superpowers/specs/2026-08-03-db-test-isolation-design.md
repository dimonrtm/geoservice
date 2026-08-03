# Изоляция PostgreSQL/PostGIS integration-тестов от demo-БД

Дата: 2026-08-03

## Контекст

Текущий набор `RUN_DB_TESTS=1` запускается с тем же `DATABASE_URL`, который
использует локальный demo environment. Большинство сценариев обёрнуты во внешнюю
rollback-транзакцию, но часть migration- и concurrency-тестов использует
отдельные committed connections и выполняет разрушительный cleanup.

Во время полного DB-прогона
`test_concurrent_open_seeded_edit_version_returns_one_created_and_one_reopened`
удалил каноническую `EditVersion` для `WO-001`. Cleanup повторно создал seed chain,
но `run_seed_chain()` не открывает новую `EditVersion`. Поэтому после теста
`WO-001` вернулся в статус `assigned`, а пользовательская `EditVersion` исчезла.
Последующий `dev-up.cmd` не удалял volume и не был источником потери данных.

## Цель

Физически отделить весь набор `RUN_DB_TESTS=1` от demo-БД так, чтобы migration,
seed, repository и concurrency-тесты не могли изменить локальные demo-данные
даже при падении pytest или аварийном завершении cleanup.

## Не входит в scope

- восстановление утраченной пользовательской `EditVersion`;
- изменение поведения `dev-up.cmd` и demo startup;
- отказ от destructive setup внутри изолированной test-БД;
- параллельный запуск DB-тестов;
- изменение production Compose-пути.

Текущая demo-БД остаётся без `EditVersion` до отдельного явного решения
пользователя о восстановлении.

## Рассмотренные варианты

### 1. Отдельный disposable `postgis_test` — выбран

Test-БД работает в отдельном Compose-проекте, отдельной сети и `tmpfs` без
постоянного volume. Это обеспечивает физическую изоляцию и делает cleanup
данных необязательным для безопасности demo environment.

### 2. Отдельная база `geo_test` в текущем `geo-postgis`

Логически отделяет данные, но сохраняет общий PostgreSQL instance и общие
административные реквизиты. Ошибка в URL или migration-команде всё ещё может
затронуть `geo`.

### 3. Уникальные строки или snapshot/restore в demo-БД

Подходит для отдельных repository-тестов, но не защищает от migration-тестов,
которые изменяют схемы. Restore также нельзя гарантировать после аварийного
завершения процесса.

## Архитектура

### `infra/docker-compose.test.yml`

Новый standalone Compose-файл определяет только два сервиса:

- `postgis_test` — `postgis/postgis:16-3.4`, база `geo_test`, PostGIS init,
  healthcheck, `tmpfs` для `/var/lib/postgresql/data`, без published ports и
  named volumes;
- `backend_db_tests` — backend image, `depends_on` с условием healthy,
  `RUN_DB_TESTS=1`, `TEST_DATABASE_URL` на hostname `postgis_test` и единая
  команда `pytest tests/integration_tests`. Alembic запускается из защищённого
  pytest bootstrap только после проверки и переключения URL.

Compose запускается с фиксированным project name `geoservice-db-tests`.
Поэтому его сеть и container namespace не совпадают с demo-проектом `infra`.
`backend_db_tests` не подключается к `infra_default` и не может разрешить
hostname `postgis` из demo Compose.

### `infra/db-tests.cmd`

Windows entrypoint зависит только от Docker CLI и Compose; host Python не
требуется. Скрипт:

1. удаляет остатки только проекта `geoservice-db-tests`;
2. собирает и запускает `backend_db_tests` с `--abort-on-container-exit`;
3. сохраняет exit code test-runner;
4. всегда выполняет `down -v` только для test-проекта;
5. возвращает исходный exit code.

Ни `dev-up.cmd`, ни `scripts/dev.cmd` этот test-проект не запускают.

### CI

CI заменяет последовательные вызовы
`exec utility_service env RUN_DB_TESTS=1 pytest ...` единым запуском test
Compose-проекта. Demo Compose остаётся поднятым для health и API smoke, но DB
tests не используют его сеть или `DATABASE_URL`.

Перед isolated DB-run CI считывает fingerprint канонической demo-цепочки, а
после завершения повторяет read-only запрос и сравнивает результат. Fingerprint
включает идентификаторы и counts для `WorkOrder`, `DefaultState` и
`EditVersion`. Несовпадение завершает job ошибкой.

## Fail-closed bootstrap

При старте pytest `apps/backend/conftest.py` вызывает отдельный test bootstrap.
Правила применяются только если `RUN_DB_TESTS=1`:

1. `TEST_DATABASE_URL` обязан присутствовать;
2. URL обязан иметь PostgreSQL-compatible scheme;
3. имя базы обязано заканчиваться на `_test`;
4. нормализованный `TEST_DATABASE_URL` не может совпадать с исходным
   `DATABASE_URL`;
5. только после успешной проверки процесс назначает
   `DATABASE_URL=TEST_DATABASE_URL`;
6. bootstrap применяет `alembic upgrade head` к уже проверенной test-БД;
7. только затем pytest начинает collection integration-тестов.

Переопределение выполняется до collection. Поэтому существующие integration-
тесты, SQLAlchemy engines и Alembic `env.py`, которые читают `DATABASE_URL`,
автоматически используют изолированную БД.

Если любое правило нарушено, pytest завершается с понятной configuration error
до первого SQL-запроса. Старый ручной вызов внутри `utility_service` без
`TEST_DATABASE_URL` становится безопасно неработоспособным.

Логи и ошибки не должны печатать пароль или полный URL. Сообщение содержит
только название отсутствующей переменной или безопасное имя базы.

## Поток данных

```text
db-tests.cmd / CI
        |
        v
geoservice-db-tests Compose project
        |
        +--> postgis_test:5432/geo_test (tmpfs)
        |
        +--> backend_db_tests
                 |
                 +--> conftest fail-closed validation
                 +--> DATABASE_URL := TEST_DATABASE_URL
                 +--> alembic upgrade head
                 +--> pytest tests/integration_tests

infra Compose project / postgis:5432/geo
        ^
        |
        +-- не подключён к test network; только read-only fingerprint в CI
```

## Тестирование

### Bootstrap unit tests

- без `RUN_DB_TESTS=1` окружение не переопределяется;
- отсутствующий `TEST_DATABASE_URL` отклоняется;
- равные application/test URL отклоняются;
- база без суффикса `_test` отклоняется;
- неподдерживаемая схема URL отклоняется;
- корректный URL назначается в `DATABASE_URL` до collection;
- диагностические сообщения не раскрывают credentials.

### Compose contract tests

- `postgis_test` не публикует ports;
- PostgreSQL data directory использует `tmpfs`;
- test Compose не объявляет named volume;
- `backend_db_tests` зависит только от `postgis_test`;
- runner получает `RUN_DB_TESTS=1` и `TEST_DATABASE_URL` с БД `geo_test`;
- pytest bootstrap запускает Alembic после URL guard и до collection;
- `dev-up.cmd` не ссылается на test Compose.

### Integration acceptance

- fresh `postgis_test` проходит Alembic и весь `tests/integration_tests`;
- destructive migration- и concurrency-тесты продолжают проверять реальную
  PostgreSQL/PostGIS семантику;
- test Compose удаляется и не оставляет volume после успешного и ошибочного
  завершения;
- demo fingerprint до и после полного DB-run совпадает;
- текущая demo-БД не получает новую `EditVersion` автоматически.

## Изменения существующего concurrency-теста

В рамках этого исправления тест может сохранить текущий committed cleanup:
после физической изоляции он разрушает только disposable `geo_test`. Отдельная
переработка теста на уникальные aggregate IDs не требуется для защиты demo-БД и
не входит в scope.

## Критерии готовности

1. Любой `RUN_DB_TESTS=1` без безопасного `TEST_DATABASE_URL` завершается до
   SQL-доступа.
2. Полный DB-набор выполняется только в `postgis_test/geo_test`.
3. Test PostgreSQL не имеет persistent volume и host port.
4. Windows entrypoint не зависит от host Python.
5. CI больше не запускает DB-тесты через demo `utility_service`.
6. Fingerprint demo-БД не меняется после полного DB-прогона.
7. `dev-up.cmd` сохраняет прежнее поведение и не управляет test Compose.
8. Утраченная `EditVersion` не восстанавливается этим изменением.
