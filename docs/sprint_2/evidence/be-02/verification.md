# BE-02: результаты проверки

Дата: 2026-11-01. Проверялось текущее рабочее дерево; изменения не закоммичены.

## Результат

FeatureService различает `None` и `{}` при сборке ответа. Очистка свойств работает с неизменной и новой geometry. Схема запроса, SQL и интерфейс repository не менялись.

| Проверка | Результат |
|---|---|
| Исходные service/publisher/HTTP unit-тесты | 32 passed, 2 warnings |
| Новая регрессия до исправления | 3 failed, 1 passed, 14 deselected |
| Целевые service/schema/publisher/HTTP тесты после исправления | 45 passed, 2 warnings |
| Весь набор use_cases/tests и web_api/tests | 348 passed, 2 warnings |
| Реальная PostGIS: commit, stale version, rollback после UPDATE; по два варианта geometry | 6 passed, без skips |
| Black и Ruff для четырёх Python-файлов задачи | Успешно |
| Независимое read-only ревью кода и тестов | Critical/Important/Minor — нет |
| Git diff --check и окончания строк всех 11 изменённых/новых файлов | Успешно, LF |

Три RED-падения: старый словарь вместо `{}` и два `BusinessValidationException` при передаче geometry. Единственный исходно успешный вариант — повторная очистка уже пустого словаря без изменения geometry. Это маскирующий дефект сценарий, сохранённый как регрессия.

Два предупреждения unit-наборов относятся к устаревшим `crypt` в passlib и `anyio.abc.BlockingPortal` в Starlette. Они присутствовали и в исходном прогоне.

## Команды unit-проверок

Команды выполнялись из корня репозитория. Исходный и целевой прогон использовали `geoservice-day14-check:latest` с текущими исходниками, подключёнными read-only. Общая проверка и lint использовали свежий backend dev image `geoservice-be02-0da6492d-backend_db_tests:latest`.

Общий запуск:

```powershell
docker run --rm --network none --read-only --tmpfs /tmp -e PYTHONDONTWRITEBYTECODE=1 -e PYTHONPATH=/app -v C:/Repositories/geoservice/apps/backend:/app:ro -w /app --entrypoint python geoservice-be02-0da6492d-backend_db_tests:latest -m pytest -p no:cacheprovider utility_service/use_cases/tests utility_service/web_api/tests --tb=short
```

Для исходной проверки выбран набор:

```text
utility_service/use_cases/tests/test_feature_service.py
utility_service/use_cases/tests/test_feature_realtime_publisher.py
utility_service/web_api/tests/test_layers_api.py
```

Для RED использован `utility_service/use_cases/tests/test_feature_service.py -k clears_properties --tb=short`. Для целевого GREEN к исходному набору добавлен `utility_service/use_cases/tests/test_patch_feature_request.py`.

Black (`python -m black --check`) и Ruff (`python -m ruff check`) выполнены в read-only контейнере с writable cache в `/tmp` для:

```text
utility_service/use_cases/services/feature_service.py
utility_service/use_cases/tests/test_feature_service.py
utility_service/use_cases/tests/test_patch_feature_request.py
tests/integration_tests/test_legacy_patch_properties.py
```

## Интеграционная проверка

Изолированный проект: `geoservice-be02-0da6492d`. PostGIS `16-3.4`, БД `geo_test` на tmpfs. Образ backend собран из текущих исходников; Alembic успешно применил migrations до `e9f1a2b3c4d5`.

```powershell
docker compose -p geoservice-be02-0da6492d -f infra/docker-compose.test.yml run --build --rm backend_db_tests python -m pytest tests/integration_tests/test_legacy_patch_properties.py --tb=short
docker compose -p geoservice-be02-0da6492d -f infra/docker-compose.test.yml down --volumes --remove-orphans
```

Cleanup выполнен в `finally` с сохранением exit code тестов; контейнер PostGIS и сеть удалены. Общая demo-БД не использовалась.

Подтверждено:

- При обоих успешных PATCH отдельная session читает `{}`, новую version и ожидаемую geometry; результат совпадает с DTO ответа.
- Callback publisher читает эту же запись через отдельную session, то есть commit завершён до публикации. Assertion вынесен наружу callback, поскольку сервис подавляет исключения publisher.
- Запрос с устаревшей version не меняет свойства, geometry или version; публикации нет.
- Тестовая подмена выполняет настоящий UPDATE, проверяет изменённые поля внутри транзакции и выбрасывает исключение. Независимый readback после отказа подтверждает полный rollback; публикации нет.

## Границы

Фактическая доставка по WebSocket и сквозной HTTP+PostGIS сценарий не запускались. Проверены настоящий сервис/repository на БД, граница request schema, существующие HTTP-тесты с подменой сервиса и сериализация publisher. Это не заявка на устранение соседних проблем доставки/производительности legacy realtime.

Новые сведения о доменной модели или архитектурном контракте не появились: исправлено нарушение существующего контракта. Agent memory и Code_wiki не дублируются.
