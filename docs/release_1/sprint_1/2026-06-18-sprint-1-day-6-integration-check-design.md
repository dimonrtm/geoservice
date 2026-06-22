# Спринт 1, День 6: Облегченная Интеграционная Проверка

Дата: 2026-06-18
Статус: согласован пользователем
Расположение: `docs/release_1/sprint_1`

## Назначение

День 6 является облегченным интеграционным днем после backend foundation `WorkOrder`.
Цель дня - подтвердить, что миграции, demo users, utility dataset и work orders seed
работают в одной цепочке, а `WO-001` корректно связан с `alexey.editor`,
`synthetic_utility_feeder_01` и рабочим `AOI`.

Новая пользовательская функциональность не добавляется. День 6 закрывает риск, оставленный
Днем 5: unit-тесты подтвердили модель, seed и service-правила по отдельности, но startup chain,
миграции и междоменные связи должны быть проверены совместно.

## Выбранный Подход

Используется интеграционный smoke + targeted invariants.

День 6 остается легким: он не добавляет API, frontend, `EditVersion` или workspace behavior,
но проверяет, что уже собранная вертикаль действительно живет вместе:

```text
migrations -> demo users seed -> utility dataset seed -> work orders seed
```

Проверка фокусируется на стабильных инвариантах, которые важны для следующих дней Sprint 1:

- `User`, `AOI`, `Feeder` и `WorkOrder` создаются в согласованном порядке;
- `WO-001` существует ровно один раз;
- `WO-001` назначен активному `Editor`, а не `Reviewer`;
- `WO-001` ссылается на существующий `AOI` и `Feeder`;
- повторный seed не дублирует и не перезаписывает пользовательское состояние.

Если окажется, что `seed_work_orders` существует, но не включен в startup chain, День 6 может
добавить минимальное orchestration wiring после utility dataset seed. Это не считается новой
продуктовой функциональностью, потому что без такого wiring интеграционная цель дня не выполнена.

## Граница Scope

### Входит

- проверка Alembic upgrade на чистой PostgreSQL/PostGIS test database;
- запуск seed chain в порядке `demo users -> utility dataset -> work orders`;
- проверка связей `WorkOrder -> User`, `WorkOrder -> AOI`, `WorkOrder -> Feeder`;
- проверка `WO-001` по стабильному UUID, code, status и assignee;
- повторный запуск seed chain как restart/idempotency smoke;
- минимальное подключение `seed_work_orders` к startup chain, если оно отсутствует;
- targeted integration tests и короткий runbook/команды проверки в implementation plan;
- русскоязычные прикладные сообщения и logs, если требуется изменить orchestration code.

### Не входит

- публичные endpoints `/api/v1/work-orders/...`;
- frontend `Мои наряды`;
- `EditVersion` model или API;
- workspace API;
- reviewer queue, approve/reject и post;
- reset/full-clean для demo dataset;
- изменение модели `AOI`, `Feeder`, `NetworkFeature` или `NetworkAssociation`;
- новая role administration или assignment UI.

## Архитектура

День 6 оформляется как тонкий интеграционный слой вокруг уже существующих компонентов, без новой
бизнес-логики.

`tests/integration_tests/` получает focused test module для цепочки миграций, seed и связей.
Он использует существующую поддержку test DB из network integration tests, чтобы не создавать
второй механизм управления PostgreSQL/PostGIS окружением.

`seeds/runners` и startup/lifespan проверяются как orchestration boundary. Если runner
`seed_work_orders` уже есть, но не вызывается при startup, implementation plan должен добавить
минимальный вызов после utility dataset seed.

`WorkOrderService` остается use-case boundary для доменных правил. День 6 не переносит проверки
доступа в API и не добавляет routes. Интеграционная проверка может использовать service или
repository слой, чтобы подтвердить, что seeded `WorkOrder` читается и проходит уже реализованные
assignment checks.

`Alembic` остается source of truth для структуры. Проверка идет от чистой БД до head, потому что
важен полный порядок миграций: users и roles, utility network, затем work orders.

## Поток Данных

```text
clean test database
-> alembic upgrade head
-> seed demo users
-> seed utility dataset
-> seed work orders
-> assert users/network/work_orders links
-> repeat seed chain
-> assert no duplicates and no overwritten state
```

Ожидаемый порядок startup seed после Дня 6:

```text
demo users -> utility dataset -> work orders -> FastAPI application
```

`WorkOrder` не создает свой `AOI` или `Feeder`. Он использует уже созданные dependency records:

- assignee находится по `alexey.editor@example.local`;
- feeder находится по `synthetic_utility_feeder_01`;
- `AOI` выбирается из существующего utility dataset по текущему seed contract.

## Инварианты

`alexey.editor@example.local` существует, активен и имеет роль `Editor`.

`marina.reviewer@example.local` существует, но не может быть assignee для `WO-001`.

`synthetic_utility_feeder_01` существует, содержит ожидаемый demo dataset и связан с `WO-001`
через `feeder_id`.

Есть хотя бы один `AOI`, который используется `WO-001` через `aoi_id`. День 6 не добавляет FK
между `Feeder` и `AOI`, потому что День 4 уже выбрал spatial relationship между feeder features
и AOI.

`WO-001` существует ровно один раз, имеет стабильный UUID
`6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0401`, status `assigned`, assignee `alexey.editor`, feeder
`synthetic_utility_feeder_01` и существующий `AOI`.

Повторный запуск seed chain не меняет assignee, status, title, description, AOI или feeder
существующего `WO-001`.

Поврежденные зависимости остаются явной ошибкой seed/use-case слоя, а не молчаливым
пересозданием данных.

## Обработка Ошибок

Интеграционный тест должен различать сбои orchestration и доменные нарушения:

- migration failure означает нарушение схемы или порядка ревизий;
- missing user, feeder или AOI означает нарушение seed chain;
- duplicate `WO-001` означает нарушение create-once контракта;
- assignment to non-Editor означает нарушение роли assignee;
- изменение существующего `WO-001` при повторном seed означает нарушение idempotency.

Если seed chain падает из-за отсутствующей зависимости, ошибка должна оставаться явной и
диагностируемой. День 6 не должен добавлять fallback, который автоматически создает недостающий
user, feeder или AOI внутри work order seed.

## Тестирование

### Integration Smoke

Проверяет полный цикл:

1. чистая БД поднимается до Alembic head;
2. demo users seed создает `alexey.editor`, `bolat.editor` и `marina.reviewer`;
3. utility dataset seed создает `synthetic_utility_feeder_01` и рабочий `AOI`;
4. work orders seed создает `WO-001`;
5. все FK и доменные связи валидны;
6. повторный seed chain не создает дублей и не перезаписывает `WO-001`.

### Targeted Unit Regression

Сохраняются быстрые unit gates, уже введенные в Дни 4-5:

- network model metadata;
- seed utility dataset specs/service;
- seed work order specs/service;
- work order service assignment/status rules;
- utility network API tests, если startup wiring затрагивает lifespan.

### Manual/Compose Smoke

Если implementation plan будет включать Compose smoke, он должен подтвердить только минимальную
цепочку:

1. migrations выполняются успешно;
2. backend запускает seed chain без ошибок;
3. backend становится healthy;
4. повторный restart не меняет seeded dataset и `WO-001`.

## Критерии Готовности

День 6 завершен, когда:

1. миграции применяются на чистой PostgreSQL/PostGIS БД до head;
2. seed chain запускается в согласованном порядке;
3. `WO-001` существует ровно один раз и связан с `alexey.editor`, `synthetic_utility_feeder_01`
   и существующим `AOI`;
4. `Reviewer` не является assignee seeded work order;
5. повторный seed chain не создает дублей и не перезаписывает состояние `WO-001`;
6. targeted unit/integration tests проходят;
7. публичный Work Orders API, frontend и `EditVersion` не добавлены преждевременно.

## Последствия Решения

- День 6 превращает результаты Дней 2-5 в проверяемую backend цепочку перед следующими
  интенсивными днями.
- Следующий backend этап сможет добавлять `Мои наряды` или `EditVersion` поверх проверенных
  seed и FK relationships.
- Minimal startup wiring допустим только для существующего work order seed; любые новые
  пользовательские workflow остаются вне scope.
- Полный reset/full-clean остается отдельной будущей задачей, чтобы не менять create-once
  semantics обычного restart.
