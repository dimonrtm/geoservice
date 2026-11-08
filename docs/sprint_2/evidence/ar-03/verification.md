# AR-03: проверка диагностики realtime

Дата: 2026-11-08. Изменения в рабочем checkout; commit не создавался. Статус: реализация и проверки завершены, независимое ревью не выявило блокирующих дефектов; три замечания Minor обработаны и перепроверены.

Последующая проверка CI выявила зависимость AR-03 от предшествующих migration-тестов, не входивших в первоначальный выборочный DB-прогон. Причина, исправление Alembic logging и результаты полного DB-набора приведены в [отчёте регрессии](../../2026-11-08-ar-03-smoke-regression.md). Таблица ниже сохраняет область первоначальных проверок и не означает, что тогда запускался весь DB-набор.

## Подтверждённое поведение

- Ошибки подготовки и сериализации публикуют отдельную WARNING JSON-запись для каждого целевого подключения с одним eventId изменения. При отсутствии подписчиков payload не строится и потери не логируются.
- При аварийном прекращении доставки учитываются текущий кадр, остаток очереди и отвергнутый кадр переполнения. Записи содержат eventId, eventType, layerId, featureId, featureVersion, connectionId, reason, stage и outcome.
- Завершённая серверная отправка не становится потерей при гонке с retire. Повторные завершения подписки не дублируют записи. Ошибка проверки сессии отличается от её недействительности и сохраняет fail-closed.
- Штатные закрытия, logout, остановка и отсутствие подписчиков не создают записей о потерях. Ошибки cleanup диагностируются отдельно от потерь изменений.
- Произвольные тексты исключений, payload, close reason и секреты не попадают в новый лог. Стек ограничен безопасными полями последних 10 кадров. Ошибка logging handler не выходит за диагностическую границу.
- Create/update/delete остаются успешными после commit при ошибке publisher, сериализации, отправки и обработчика логов. Результат подтверждён независимым HTTP-чтением с реальной PostGIS.

## Выполненные проверки

| Проверка | Результат |
| --- | --- |
| Исходные FeatureService, publisher, manager, ws_layers | 51 passed до изменений |
| Безопасный logging | 3 passed; перед реализацией зафиксирован RED |
| FeatureService, publisher, manager и контекст публикации | 43 passed; 6 новых сценариев сначала RED |
| Queue/current-frame/publication и регрессии менеджера | 38 passed; диагностические сценарии сначала RED |
| Очереди после исправлений по ревью | 18 passed, включая idle writer и cleanup при отказе logging handler |
| Маршрут закрытия, auth и очереди | 59 passed; аварийные receive-сценарии сначала RED |
| Целевые PostGIS integration tests | 28 passed, 0 skipped |
| Итоговый полный backend без RUN_DB_TESTS | 742 passed, 334 skipped, 2 исходных deprecation warnings |
| Реальный Uvicorn/WebSocket transport и вывод процесса | PASS; close codes 1000, 1005, 1006; диагностическая JSON-строка обнаружена в stdout/stderr |
| Ruff изменённых backend Python-файлов | PASS |
| Black с явной конфигурацией проекта | PASS |

Независимый reviewer прочитал production diff и новые файлы, самостоятельно повторил 38 новых unit/route/logging тестов. Его замечания: тихий idle writer, недостаточное доказательство отсутствия публикации rejected CRUD и отсутствие прямой проверки аварийного cleanup при падающем handler. Первое исправлено через RED→GREEN, два других закрыты усилением тестов. После этого основной исполнитель повторил полный backend и 28 интеграционных сценариев; отдельного второго независимого ревью не было. Подробности — [журнал исполнения](../../2026-11-08-ar-03-execution-ledger.md).

В первоначальном интеграционном тесте PATCH не передавал обязательное `geometry: null`, а отказ геометрии ошибочно ожидался как HTTP 400 вместо существующего HTTP 422. Исправлены тестовые данные/ожидания; контракт API не менялся. Callback старого теста BE-02 адаптирован к keyword-only context, сохранив независимое чтение commit.

Transport-проба использует настоящий Uvicorn с его обычной конфигурацией логирования, production менеджер и production функцию маршрута. Auth/DB заменены явными синтетическими fixtures внутри отдельного probe app; это не проверка production авторизации или браузерного UI. Пустой close frame передаётся как пустые wire bytes: 1005 — наблюдаемый сервером статус, а не разрешённый код для отправки по сети.

## Воспроизведение

Unit tests: контейнер с Python-зависимостями проекта, read-only mount `apps/backend` в `/app`, рабочий каталог `/app`, `PYTHONDONTWRITEBYTECODE=1`, сеть отключена. Выполнялся полный `python -m pytest -p no:cacheprovider`; DB-dependent tests без RUN_DB_TESTS штатно пропускаются.

Интеграционная проверка из корня репозитория:

```powershell
docker compose -p ar03-check-1108-b102 -f infra/docker-compose.test.yml run --build --rm backend_db_tests python -m pytest tests/integration_tests/test_legacy_realtime_diagnostics.py tests/integration_tests/test_legacy_realtime_delivery.py tests/integration_tests/test_browser_auth_websocket_revocation.py tests/integration_tests/test_legacy_patch_properties.py -o addopts= -q
```

Повторные запуски использовали тот же построенный образ с read-only mount актуальных исходников. Изоляция БД — отдельные Compose network/container и PostgreSQL tmpfs. Для следующего независимого запуска выбрать новое уникальное имя проекта.

Проба транспорта из корня после сборки образа:

```powershell
docker run --rm --network none -e PYTHONDONTWRITEBYTECODE=1 -v C:/Repositories/geoservice/apps/backend:/app:ro -v C:/Repositories/geoservice/docs/sprint_2/ar-03:/probe:ro -w /app ar03-check-1108-b102-backend_db_tests:latest python /probe/transport_probe.py
```

Она запускает временный Uvicorn-процесс на loopback контейнера, проверяет закрытия и JSON-лог, останавливает процесс и удаляет временный файл вывода. Не изменяет production routes или конфигурацию.

## Как читать записи

Logger: `utility_service.realtime`. По eventId найти сбой конкретного уведомления; по connectionId — сбои одной подписки. Для изменения объекта использовать слой, featureId, featureVersion и eventType. Переподключение получает новый connectionId; сопоставление с личностью пользователя не добавляется.

- `realtime_delivery_failed`: известны изменение и целевой получатель.
- `realtime_publication_failed`: защитный fallback до доступных сведений о получателях; отсутствие connectionId не означает отсутствие подписчиков.
- `realtime_connection_failed`: сбой служебного кадра connected, проверки перед подключением или writer без ожидающих изменений; вымышленные идентификаторы изменения не добавляются.
- `realtime_cleanup_failed`: отдельный сбой закрытия транспорта, не повторный перечень потерь.

`not_sent` означает отказ до начала серверной отправки; `send_unconfirmed` — неуспешную либо незавершённую попытку. Это не доказательство неполучения браузером. Для queue_discard причина объясняет прекращение всей подписки. Размеры очереди записываются до очистки.

## Ограничения

Проверка UI не выполнялась: frontend не меняется, получение/применение сообщения вне согласованных границ. Нет гарантии сохранности логов при падении процесса, отказе logging sink или потере контейнерных журналов. Отсутствие записи не подтверждает доставку. Метрики, retries, outbox и межпроцессная доставка не добавлены.

Предупреждения passlib/crypt и Starlette/anyio наблюдались на исходном наборе до изменений и не связаны с AR-03.
