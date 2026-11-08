# AR-03: зависимость DB-тестов от конфигурации логирования Alembic

Дата: 2026-11-08. Основание: пользователь прислал лог CI с 9 failed, 325 passed в шаге PostgreSQL/PostGIS tests in isolated database. Этот шаг выполняется перед API smoke; ошибки demo fingerprint в предоставленном логе нет.

## Причина

В полном наборе migration-тесты повторно вызывают Alembic в том же Python-процессе. [env.py](../../apps/backend/utility_service/infrastructure/postgresql/alembic/env.py) вызывал `fileConfig(config.config_file_name)` с неявным `disable_existing_loggers=True`. В `alembic.ini` перечислены root, sqlalchemy и alembic; уже созданный при collection `utility_service.realtime` отключался. Последующие CRUD успешно сохранялись, но диагностическая запись не попадала в caplog: девять проверок AR-03 получали пустой список.

Изолированная проба показала `logger.disabled: False → True` после fileConfig. Полный DB-набор воспроизвёл исходные девять падений: 9 failed, 325 passed. Новый regression test после реального `command.current()` также воспроизвёл отсутствие записи.

Предыдущая приёмка AR-03 проверяла весь backend без RUN_DB_TESTS и отдельно 28 выбранных PostGIS-сценариев. Ни один запуск не совмещал migration-тесты и AR-03; поэтому зависимость от порядка выполнения осталась незамеченной. Прежние результаты были верны для перечисленных запусков, но не подтверждали полный DB-шаг CI.

## Исправление

В Alembic используется `fileConfig(..., disable_existing_loggers=False)`. Существующие логгеры приложения сохраняются после запуска команды миграций. Проверки AR-03 не включают логгер принудительно и не ослабляют требования к содержимому логов.

[Regression test](../../apps/backend/tests/integration_tests/test_alembic_application_logging.py) создаёт application logger до команды Alembic, выполняет `command.current()` на изолированной БД и вызывает реальный FeatureService с неисправным publisher. Проверяет JSON-запись в stderr через capfd, идентификатор изменения и отсутствие текста секрета. capfd перехватывает файловый дескриптор, сохраняя обычный объект sys.stderr для настроенного Alembic handler.

Схема БД, migrations revisions, auth и бизнес-логика CRUD не изменены.

## Проверки

- RED полного набора: 9 failed, 325 passed.
- RED regression test: отсутствует ожидаемая запись.
- GREEN regression test и AR-03: 14 passed.
- Ruff и Black двух Python-файлов: PASS.
- Полная команда DB-шага CI после исправления: **335 passed, 0 skipped**, 2 прежних deprecation warnings, 63,29 секунды; pytest и Compose завершились с кодом 0.
- Независимое read-only ревью исправления и regression test: замечаний нет.

```powershell
docker compose -p ar03-smoke-1108-c31 -f infra/docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from backend_db_tests
```

Используется отдельный disposable Compose-проект и PostgreSQL tmpfs. Demo-БД не затрагивается; Git add/commit/push не выполняются. Удалённый GitHub Actions run не запускается агентом.

Во время `up --abort-on-container-exit` нельзя параллельно запускать вспомогательный `docker run` из образа с теми же Compose-метками. Построенный здесь образ содержит `com.docker.compose.project` и `com.docker.compose.service`; отдельный lint-контейнер унаследовал их, попал под наблюдение Compose и своим завершением прервал первый контрольный запуск. Этот запуск не считается результатом тестов; повторный выполняется без параллельных вспомогательных контейнеров.
