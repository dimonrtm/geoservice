# Concurrent Open EditVersion

Дата: 2026-06-28
Статус: согласован для written spec
Расположение: `docs/superpowers/specs`

## Назначение

`POST /api/v1/work-orders/{workOrderId}/edit-versions` должен оставаться идемпотентным при конкурентном открытии одного `WorkOrder`. Если два запроса приходят одновременно, ровно один запрос создает `EditVersion` и получает `created=true` с HTTP `201`, а остальные успешные конкурентные запросы возвращают ту же открытую `EditVersion` как reopen: `created=false` с HTTP `200`.

Сейчас сервис уже поддерживает последовательный reopen и база данных защищает инвариант partial unique index `uq_edit_versions_open_work_order`. Проблема в том, что текущий path делает `get_open_edit_version -> create_open_edit_version -> save(work_order)` без блокировки строки `WorkOrder`. Два параллельных запроса могут одновременно увидеть `existing is None`; один создаст версию, а второй получит `IntegrityError` от уникального индекса и может уйти клиенту как 500.

## Границы Scope

Входит:

- backend use-case `EditVersionService.open_for_work_order()`;
- repository-метод чтения `WorkOrder` с row-level lock;
- сохранение partial unique index как DB-инварианта;
- `IntegrityError` recovery для уникального конфликта открытой `EditVersion`;
- backend unit tests для locked read и recovery;
- repository SQL test на `FOR UPDATE`;
- по возможности integration test с двумя конкурентными opens.

Не входит:

- изменение публичного API-контракта;
- изменение frontend;
- изменение схемы БД или миграций;
- переход на полноценный PostgreSQL upsert-first flow;
- изменение lifecycle `EditVersion` за пределами статуса `open`;
- новые состояния `WorkOrder`.

## Выбранный Подход

Основной путь: row lock на `WorkOrder` плюс текущий unique index.

`EditVersionService.open_for_work_order()` после проверки actor читает `WorkOrder` через новый метод `WorkOrderRepository.get_by_id_for_update(work_order_id)`. Дальше сервис выполняет текущие проверки assignee/status уже под блокировкой строки `WorkOrder`, читает open `EditVersion` и принимает решение:

- если `WorkOrder.status == in_progress` и open version есть, обновляет `last_opened_at`, возвращает `created=false`;
- если `WorkOrder.status == in_progress` и open version отсутствует, возвращает текущий corrupted context `422 WORK_ORDER_CONTEXT_INVALID`;
- если `WorkOrder.status == assigned` и open version есть, возвращает текущий corrupted context `422 WORK_ORDER_CONTEXT_INVALID`;
- если `WorkOrder.status == assigned` и open version отсутствует, копирует active `DefaultState` в новую `EditVersion`, переводит `WorkOrder` в `in_progress`, возвращает `created=true`;
- если статус не поддерживает open, возвращает текущий `409 WORK_ORDER_STATE_CONFLICT`.

Partial unique index `uq_edit_versions_open_work_order` остается последней линией защиты. Он не заменяется приложением и не удаляется.

## Отклоненные Альтернативы

PostgreSQL upsert-first не выбран как основной путь. Он хорошо защищает single-row insert, но текущий open создает parent `EditVersion`, затем копирует `edit_version_features` и `edit_version_associations`. Из-за зависимых rows и partial unique index подход усложняет определение "кто создал parent и должен копировать slice". Для текущего scope row lock проще и ближе к агрегату `WorkOrder`.

Optimistic-only recovery без lock тоже не выбран как основной путь. Он требует меньше кода, но два запроса могут параллельно выполнить дорогой read/copy default slice до того, как один проиграет уникальному индексу. Кроме того, поведение перехода `WorkOrder.assigned -> in_progress` остается более хрупким.

## Компоненты

`EditVersionService` остается главным use-case и не меняет внешний result type `OpenEditVersionResult`.

Нужны небольшие внутренние helper-границы:

- locked open path, который выполняется внутри `async with session.begin()`;
- helper reopen existing version: `touch_edit_version(existing)` и `OpenEditVersionResult(created=False, edit_version=existing)`;
- recovery path после constraint-specific `IntegrityError`, который запускается в новой транзакции;
- predicate, который распознает только unique violation по `uq_edit_versions_open_work_order`.

`WorkOrderRepository` добавляет:

- `get_by_id_for_update(work_order_id)`, который компилируется в `SELECT ... FOR UPDATE`;
- существующие `get_open_edit_version()`, `create_open_edit_version()`, `touch_edit_version()` и `save()` сохраняются как основные операции.

`web_api/api/work_orders.py` не меняет контракт. Он уже мапит `created=true` в HTTP `201`, а `created=false` в HTTP `200`.

## Data Flow Конкурентного Open

1. Request A и Request B приходят одновременно для одного `WorkOrder`.
2. Request A получает row lock на `work_order.work_orders.id`.
3. Request B ждет освобождения lock.
4. Request A видит `assigned + no open version`, читает active `DefaultState`, создает `EditVersion`, копирует features/associations, переводит `WorkOrder` в `in_progress`, commit.
5. Request B продолжает после commit A, перечитывает locked `WorkOrder`, видит `in_progress + existing open version`, обновляет `last_opened_at`, commit.
6. Request A возвращает `created=true` и HTTP `201`.
7. Request B возвращает тот же `EditVersion.id`, `created=false` и HTTP `200`.

После завершения должно остаться:

- одна open `EditVersion` для `WorkOrder`;
- один набор copied features и associations;
- `WorkOrder.status == in_progress`;
- `last_opened_at` у reopen не меньше исходного значения.

## Error Handling

Обычный конкурентный path не должен попадать в `IntegrityError`, потому что row lock сериализует open по `WorkOrder`.

Recovery нужен как страховка от старого кода, будущего call path, ручной операции или редкой race вокруг constraint. Он работает только для уникального конфликта открытой версии:

1. locked open path выбрасывает `IntegrityError`;
2. outer service layer проверяет, что ошибка относится к SQLSTATE `23505` и constraint/index `uq_edit_versions_open_work_order`;
3. failed transaction полностью откатывается;
4. сервис открывает новую короткую транзакцию;
5. снова читает actor и locked `WorkOrder`;
6. читает existing open `EditVersion`;
7. если version найдена и принадлежит тому же `WorkOrder`, делает `touch_edit_version()` и возвращает `created=false`;
8. если existing version не найдена, ошибка не маскируется как успех.

Нельзя ловить произвольный `IntegrityError` от copied features, associations, FK или geometry constraints как reopen. Такие ошибки означают поврежденный context или реальный дефект данных и должны оставаться видимыми.

## Testing

Unit/use-case tests:

- `open_for_work_order()` использует locked read вместо обычного `get_by_id`;
- `in_progress + existing open version` остается reopen с `created=false` и `touch`;
- `assigned + existing open version` в нормальном locked path остается corrupted context `422`;
- `IntegrityError` по `uq_edit_versions_open_work_order` во время create запускает recovery transaction, перечитывает existing open version, делает `touch`, возвращает `created=false`;
- `IntegrityError` не по `uq_edit_versions_open_work_order` не маскируется как reopen.

Repository/SQL tests:

- `WorkOrderRepository.get_by_id_for_update()` компилирует statement с `FOR UPDATE`;
- существующий migration test partial unique index остается частью regression coverage.

Integration test желателен:

- две независимые async sessions одновременно вызывают `EditVersionService.open_for_work_order()` для одного seeded `WorkOrder`;
- результаты содержат один `created=true`, один `created=false`;
- оба результата указывают на один `EditVersion.id`;
- в БД одна open version;
- copied slice содержит 19 features и 9 associations для seeded dataset.

Если настоящий DB concurrency test окажется нестабильным в CI, минимальный обязательный gate: unit recovery test, repository `FOR UPDATE` test, существующий unique-index migration test.

## Последствия

Open `EditVersion` становится надежно идемпотентным не только последовательно, но и конкурентно. Поведение соответствует доменному инварианту `WorkOrder` имеет не больше одной active `EditVersion`, а клиент видит ожидаемую семантику `201` для создателя и `200` для reopen.

Решение сознательно оставляет `WorkOrderRepository` владельцем операций вокруг открытия version и сборки workspace aggregate. Новый отдельный `EditVersionRepository` не нужен для этого scope.

## Проверка Spec

Документ не требует изменения API, схемы БД или frontend. Все требования имеют проверяемые backend tests. Scope ограничен исправлением P1 из Sprint 1 review backlog: concurrent open `EditVersion` через lock и `IntegrityError` recovery.
