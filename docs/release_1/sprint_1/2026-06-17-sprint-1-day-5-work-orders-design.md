# Спринт 1, День 5: Backend Foundation Work Orders

Дата: 2026-06-17
Статус: согласован пользователем
Расположение: `docs/release_1/sprint_1`

## Назначение

Интенсив 5 добавляет серверную основу `WorkOrder`: persistent-модель,
статусы и назначение задачи активному `Editor`.

Результат дня:

- `WorkOrder` хранится в `utility_network` schema и связан с `User`, `AOI` и
  `Feeder`;
- поддерживаются статусы `assigned` и `in_progress`;
- seed создает воспроизводимый `WO-001`, назначенный `alexey.editor`;
- use-case слой умеет проверить назначение и подготовить foundation для
  будущих endpoints;
- достаточная проверка дня выполняется unit-тестами.

Публичный список work orders, создание `EditVersion`, workspace API и frontend
не входят в этот интенсив.

## Выбранный Подход

Используется минимальный backend aggregate без публичного API.

`WorkOrder` становится отдельной ORM-моделью в utility domain, но не запускает
пользовательский workflow сам по себе. День 5 фиксирует данные и правила,
которые нужны следующим дням:

1. `Editor` получает назначенную задачу через seed.
2. Service принимает `actor_id`, загружает актуального `User` из БД, проверяет
   что пользователь является активным `Editor` и совпадает с `assignee_id`.
3. Repository предоставляет узкие методы чтения по `id`, `code` и assigned
   user.
4. Переход `assigned -> in_progress` проектируется как внутренняя операция,
   но публично будет использован только при создании `EditVersion` в
   следующем backend-этапе.

Такой подход не смешивает День 5 с будущими `EditVersion` и `Мои наряды`,
но оставляет проверяемую модель для следующего вертикального шага.

## Граница Scope

### Входит

- `WorkOrderStatus` со значениями `assigned` и `in_progress`;
- ORM-модель `WorkOrder`;
- Alembic migration для таблицы `utility_network.work_orders`;
- repository для чтения и сохранения `WorkOrder`;
- use-case service для assignment checks и безопасной смены статуса;
- seed spec и seed service для `WO-001`;
- unit-тесты model metadata, seed specs, seed service и work-order service;
- русскоязычные прикладные сообщения и logs.

### Не Входит

- HTTP endpoints `/api/v1/work-orders/...`;
- frontend `Мои наряды`;
- `EditVersion` model или API;
- workspace API;
- reviewer queue, approve/reject и post;
- audit events;
- assignment UI или role administration;
- integration tests и PostgreSQL/PostGIS tests как обязательный gate дня.

## Доменная Модель

`WorkOrder` представляет назначенную рабочую задачу для одного участка
utility network.

Минимальные поля:

| Поле | Назначение |
|---|---|
| `id` | UUID primary key |
| `code` | стабильный человекочитаемый код, например `WO-001` |
| `title` | русское название задачи |
| `description` | русское описание задачи |
| `status` | `assigned` или `in_progress` |
| `assignee_id` | ссылка на `users.id` |
| `aoi_id` | ссылка на `utility_network.aois.id` |
| `feeder_id` | ссылка на `utility_network.feeders.id` |
| `created_at` | время создания |
| `updated_at` | время обновления |

Инварианты:

- `code` уникален;
- `assignee_id` обязателен;
- `aoi_id` и `feeder_id` обязательны;
- назначенный пользователь должен быть активным `Editor`;
- `Reviewer` не может быть assignee;
- задача всегда относится ровно к одному `AOI` и одному `Feeder`;
- в День 5 разрешен только переход `assigned -> in_progress`;
- обратный переход и закрывающие состояния добавляются в будущих спринтах.

## Storage Contract

Таблица размещается в существующей schema:

```text
utility_network.work_orders
```

Миграция добавляет:

- таблицу `work_orders`;
- CHECK constraint для `status`;
- unique constraint `uq_work_orders_code`;
- FK на `users.id`;
- FK на `utility_network.aois.id`;
- FK на `utility_network.feeders.id`;
- индексы по `assignee_id`, `status`, `aoi_id` и `feeder_id`.

Удаление `User`, `AOI` или `Feeder`, на которые ссылается work order,
запрещается через FK semantics. В demo-среде reset/full-clean будет
спроектирован отдельно, поэтому День 5 не добавляет каскадное удаление.

## Seed Contract

Seed использует существующие specs:

- `alexey.editor@example.local` как назначенный `Editor`;
- `synthetic_utility_feeder_01` как feeder;
- единственный AOI dataset как рабочая область.

Добавляется стабильный work order:

```text
WO-001
```

Рекомендуемый стабильный UUID:

```text
6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0401
```

Seed работает create-once:

- если `WO-001` отсутствует, создается после demo users и utility dataset;
- если `WO-001` уже существует, seed не меняет assignee, status, title,
  description, AOI или feeder;
- если demo user, AOI или feeder отсутствуют, seed завершается явной ошибкой
  целостности;
- обычный restart не перезаписывает пользовательское состояние work order.

Порядок startup seed после Дня 5:

```text
demo users -> utility dataset -> work orders -> FastAPI application
```

## Use-Case Layer

`WorkOrderService` отвечает за бизнес-правила, а repository остается тонким
PostgreSQL adapter.

Минимальные операции service:

- получить work order по `id` или `code`;
- получить assigned work orders для `Editor`;
- проверить доступ `actor_id` к work order через актуального пользователя из БД;
- перевести work order из `assigned` в `in_progress` внутри transaction
  boundary;
- отказать `Reviewer`, inactive user и чужому `Editor`.

Будущий API сможет использовать эти операции без переноса правил в router.
День 5 не добавляет dependency wiring в `web_api`, кроме того, что может быть
нужно для будущего implementation plan.

## Ошибки И Защитное Поведение

Use-case layer использует стабильные error codes, совместимые с контрактом
Дня 1:

| Code | Условие |
|---|---|
| `WORK_ORDER_ACTOR_NOT_FOUND` | пользователь `actor_id` отсутствует |
| `ROLE_NOT_ALLOWED` | пользователь `actor_id` не является активным `Editor` |
| `WORK_ORDER_NOT_FOUND` | work order отсутствует |
| `WORK_ORDER_NOT_ASSIGNED` | work order существует, но назначен другому `Editor` |
| `WORK_ORDER_STATE_CONFLICT` | запрошенное действие невозможно из текущего статуса |
| `WORK_ORDER_CONTEXT_INVALID` | assignee, AOI или feeder отсутствуют либо невалидны |

На уровне unit-тестов важно зафиксировать различие между
`WORK_ORDER_NOT_FOUND` и `WORK_ORDER_NOT_ASSIGNED`, хотя публичная masking
policy для HTTP endpoint будет подтверждаться позже.

Пользовательские сообщения и application logs пишутся на русском языке.
Error `code`, enum values и Python identifiers остаются на английском языке.

## Unit-Тестирование

День 5 считается готовым по unit-тестам.

Проверки:

- `WorkOrderStatus` содержит только `assigned` и `in_progress`;
- ORM metadata использует schema `utility_network`, таблицу `work_orders`,
  FK, unique/check constraints и индексы;
- seed spec содержит стабильный `WO-001`, UUID, assignee, feeder и AOI
  references;
- seed service создает `WO-001`, когда зависимости существуют;
- seed service не изменяет существующий `WO-001`;
- seed service явно падает при отсутствующем user, feeder или AOI;
- service принимает `actor_id`, загружает пользователя из БД и разрешает доступ
  назначенному активному `Editor`;
- service запрещает `Reviewer`, inactive user и чужого `Editor`;
- service переводит `assigned -> in_progress` внутри transaction boundary;
- service запрещает повторный или недопустимый переход статуса.

Integration tests для миграции и startup chain полезны, но не являются gate
этого интенсива по решению пользователя.

## Критерии Готовности

Интенсив 5 завершен, когда:

1. модель `WorkOrder` и migration подготовлены для хранения assigned задач;
2. seed создает воспроизводимый `WO-001` после demo users и utility dataset;
3. service централизует assignment authorization;
4. статусный переход `assigned -> in_progress` защищен бизнес-правилами;
5. unit-тесты покрывают модель, seed и service;
6. публичный API, frontend и `EditVersion` не добавлены преждевременно.

## Последствия Решения

- День 5 создает устойчивую серверную основу для Дней 8-12.
- Будущий endpoint `GET /api/v1/work-orders/assigned-to-me` сможет быть тонким
  adapter'ом над `WorkOrderService`.
- Create-once seed сохраняет состояние work order при restart, но не решает
  reset/full-clean.
- Отсутствие обязательных integration tests ускоряет интенсив, но migration и
  startup chain должны быть проверены в следующем интеграционном дне.
