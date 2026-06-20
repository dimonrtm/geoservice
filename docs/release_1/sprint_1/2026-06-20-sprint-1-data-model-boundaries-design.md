# Спринт 1: Границы Схем И Рабочая Копия WorkOrder

Дата: 2026-06-20
Статус: draft для пользовательской проверки
Расположение: `docs/release_1/sprint_1`

## Назначение

Спринт 1 переводит модель данных от общей схемы `utility_network` к bounded-context
схемам, которые можно будет позже выделять в отдельные сервисы без переписывания
доменной логики.

Цель изменения:

- перенести пользовательские данные в schema `"user"`;
- оставить опубликованную utility network и `DefaultState` в schema `utility_network`;
- перенести workflow сущности `WorkOrder` и `EditVersion` в schema `work_order`;
- убрать cross-schema FK и SQLAlchemy relationships между разными bounded contexts;
- создать материализованную рабочую копию участка сети при открытии `EditVersion`;
- сохранить текущую логику приложения, deploy path и CI на время перехода.

## Принятое Решение

Используется schema-per-bounded-context подход:

```text
"user"
  users

utility_network
  network_states
  aois
  feeders
  network_features
  network_associations
  default_states
  default_state_features
  default_state_associations

work_order
  work_orders
  edit_versions
  edit_version_features
  edit_version_associations
```

Между разными схемами хранятся только UUID/reference values. FK, composite FK и ORM
relationships между `user`, `utility_network` и `work_order` запрещены.
Целостность таких ссылок проверяется через repositories/use cases.

FK внутри одной схемы разрешены. Например, `work_order.edit_versions.work_order_id`
может ссылаться на `work_order.work_orders.id`, потому что `WorkOrder` и `EditVersion`
находятся внутри одного агрегата workflow.

## Доменная Семантика

`WorkOrder` отвечает за процесс:

- кому назначена работа;
- в каком статусе находится задание;
- как задача называется и показывается в очереди;
- есть ли активная `EditVersion`.

`DefaultState` отвечает за baseline сети для конкретного `WorkOrder`:

- какой slice актуальной сети относится к заданию;
- из какой версии опубликованной сети собран baseline;
- какие features и associations входят в baseline.

`EditVersion` отвечает за рабочую копию:

- создается при начале работы редактора;
- является deep copy `DefaultState`;
- после создания не синхронизируется автоматически с `DefaultState`;
- хранит `base_network_revision` для проверки `post`.

Lifecycle:

```text
1. Создается WorkOrder в schema work_order.
2. Для WorkOrder создается DefaultState в schema utility_network.
3. DefaultState поддерживает актуальный slice сети до начала работы.
4. Редактор начинает работу через POST /api/v1/work-orders/{id}/edit-versions.
5. EditVersion создается как deep copy DefaultState.
6. WorkOrder переходит assigned -> in_progress.
7. Если сеть ушла вперед, post EditVersion не проходит по version check.
```

## Версионность И UUID

`utility_network.network_states` хранит текущую версию опубликованной сети.
`DefaultState.network_revision` копируется из `network_states.current_revision` при
создании или refresh baseline. `EditVersion.base_network_revision` копируется из
`DefaultState.network_revision` при начале работы.

UUID сетевых объектов сохраняется между `DefaultState`, `EditVersion` и будущим
`post` в опубликованную сеть.

Для существующих features:

```text
feature_id = UUID из DefaultState/актуальной сети
base_version = version из DefaultState на момент copy
version = версия рабочей копии
```

Для новых features:

```text
feature_id = будущий UUID в DefaultState
base_version = null
version = 1
operation_state = 'new'
```

Primary key рабочих copy-таблиц должен включать owner container:

```text
default_state_features: (default_state_id, feature_id)
edit_version_features:  (edit_version_id, feature_id)
```

Это позволяет одной и той же feature identity одновременно существовать в актуальной
сети, baseline нескольких `DefaultState` и рабочих копиях нескольких `EditVersion`.

## Storage Contract

### `"user".users`

Переезд текущей таблицы `users` из `public` в schema `"user"`.

Минимальный контракт сохраняется:

- `id`;
- `email`;
- `password_hash`;
- `role`;
- `is_active`;
- `created_at`.

PostgreSQL identifier `user` должен использоваться аккуратно: в SQL migrations schema
пишется как `"user"`. В SQLAlchemy допустимо задать `schema="user"` и проверить
сгенерированный SQL в migration/integration tests.

### `utility_network.network_states`

Таблица хранит current revision опубликованной сети.

Минимальные поля:

- `id`;
- `name` - для Sprint 1 достаточно `default`;
- `current_revision`;
- `created_at`;
- `updated_at`.

Рекомендуемые constraints:

- unique `name`;
- `current_revision >= 1`.

Эта таблица заменяет старую singleton-семантику `utility_network.default_states`.
Новый `DefaultState` больше не является глобальным `default`, а становится baseline
для конкретного `WorkOrder`.

### `work_order.work_orders`

Таблица хранит процесс, а не сетевой scope.

Минимальные поля:

- `id`;
- `code`;
- `title`;
- `description`;
- `status`;
- `assignee_user_id` - plain UUID, no FK to `"user".users`;
- `created_at`;
- `updated_at`.

`aoi_id` и `feeder_id` уходят из `WorkOrder`. Scope задания хранится в
`utility_network.default_states`.

### `utility_network.default_states`

Одна активная baseline projection для одного `WorkOrder`.

Минимальные поля:

- `id`;
- `work_order_id` - plain UUID, no FK to `work_order.work_orders`;
- `network_revision`;
- `source_feeder_id`;
- `source_aoi_id`;
- `status`;
- `created_at`;
- `updated_at`.

Рекомендуемые constraints:

- unique `work_order_id`;
- `network_revision >= 1`;
- status check, например `active`, позже `stale`/`closed`.

`source_feeder_id` и `source_aoi_id` могут иметь FK внутри `utility_network`, потому
что это не cross-schema связь. Если позже `Feeder` или `AOI` будут вынесены из
`utility_network`, эти поля нужно будет перевести в plain UUID с repository checks.

### `utility_network.default_state_features`

Материализованный baseline features для `WorkOrder`.

Поля:

- `default_state_id`;
- `feature_id`;
- `feeder_id`;
- `asset_code`;
- `feature_type`;
- `geometry`;
- `name`;
- `description`;
- `properties`;
- `version`;
- `created_at`;
- `updated_at`.

Constraints повторяют важные локальные инварианты `network_features`: geometry validity,
SRID 4326, geometry type by feature type, `version >= 1`. FK на
`utility_network.default_states.id` допустим, потому что это та же schema.

### `utility_network.default_state_associations`

Материализованный baseline associations для `WorkOrder`.

Поля:

- `default_state_id`;
- `association_id`;
- `feeder_id`;
- `from_feature_id`;
- `to_feature_id`;
- `association_type`;
- `version`;
- `created_at`;
- `updated_at`.

Composite FK на `default_state_features(default_state_id, feature_id)` допустим внутри
`utility_network` и полезен для защиты baseline graph.

### `work_order.edit_versions`

Рабочая версия внутри агрегата `WorkOrder`.

Поля:

- `id`;
- `work_order_id` - FK to `work_order.work_orders.id`;
- `owner_user_id` - plain UUID, no FK to `"user".users`;
- `default_state_id` - plain UUID, no FK to `utility_network.default_states`;
- `base_network_revision`;
- `status`;
- `created_at`;
- `last_opened_at`.

Storage invariant: у одного `WorkOrder` не может быть больше одной open
`EditVersion`. Partial unique index сохраняется:

```text
unique(work_order_id) where status = 'open'
```

### `work_order.edit_version_features`

Deep copy features из `DefaultState`.

Поля:

- `edit_version_id`;
- `feature_id`;
- `feeder_id`;
- `asset_code`;
- `feature_type`;
- `geometry`;
- `name`;
- `description`;
- `properties`;
- `base_version`;
- `version`;
- `operation_state`;
- `created_at`;
- `updated_at`.

`operation_state` нужен для будущего `post`: `unchanged`, `new`, `modified`, `deleted`.
В Спринте 1 можно поддержать только `unchanged` при copy, но schema должна быть готова
к редактированию.

### `work_order.edit_version_associations`

Deep copy associations из `DefaultState`.

Поля:

- `edit_version_id`;
- `association_id`;
- `feeder_id`;
- `from_feature_id`;
- `to_feature_id`;
- `association_type`;
- `base_version`;
- `version`;
- `operation_state`;
- `created_at`;
- `updated_at`.

Composite FK на `edit_version_features(edit_version_id, feature_id)` допустим внутри
`work_order`, потому что это внутренняя целостность рабочей копии.

## Анализ Текущего Кода

Сейчас `WorkOrder`, `DefaultState` и `EditVersion` находятся в
`models/utility_network`, а миграции создают:

- `utility_network.work_orders` с FK на `users.id`, `utility_network.aois.id`,
  `utility_network.feeders.id`;
- `utility_network.default_states` как singleton `name='default'`;
- `utility_network.edit_versions` с FK на `utility_network.work_orders.id` и
  `users.id`.

Затронутые зоны:

- `apps/backend/utility_service/infrastructure/postgresql/models/user.py`;
- `apps/backend/utility_service/infrastructure/postgresql/models/work_order/work_order.py`;
- `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/default_state.py`;
- `apps/backend/utility_service/infrastructure/postgresql/models/work_order/edit_version.py`;
- `apps/backend/utility_service/infrastructure/postgresql/repositories/work_order_repository.py`;
- `apps/backend/utility_service/infrastructure/postgresql/repositories/default_state_repository.py`;
- `apps/backend/utility_service/use_cases/services/work_order_service.py`;
- `apps/backend/utility_service/use_cases/services/edit_version_service.py`;
- `apps/backend/seeds/repositories/seed_work_order_repository.py`;
- `apps/backend/seeds/services/seed_work_order_service.py`;
- metadata, migration, seed-chain и API tests.

Положительная сторона текущей архитектуры: Web API уже зависит от use cases, а use cases
работают через repositories. Поэтому изменение можно провести без изменения endpoint на
первом шаге.

## Стратегия Переписывания Без Поломки App/Deploy/CI

Переписывание должно идти не через большой разрыв, а через compatibility-preserving
миграцию.

### Шаг 1. Новые схемы и модели

Добавить schema `"user"` и `work_order`.

Перенести Python ownership:

```text
models/user.py
  остается import-compatible, но задает __table_args__ = {"schema": "user"}

models/work_order/
  __init__.py
  work_order.py
  edit_version.py
  edit_version_feature.py
  edit_version_association.py

models/utility_network/
  default_state.py
  default_state_feature.py
  default_state_association.py
```

`models.utility_network.__all__` больше не должен экспортировать `WorkOrder`,
`WorkOrderStatus`, `EditVersion` и `EditVersionStatus`. Все импорты этих моделей
должны перейти на `models.work_order`. Compatibility re-export не используется,
чтобы тесты сразу находили старые импорты из прежней границы.

### Шаг 2. Structural migration без переноса demo-данных

Текущие данные проекта заполняются через seed, редактирование `EditVersion` еще не
использовалось. Поэтому Спринт 1 не делает полноценную data migration для старых
`WorkOrder`, `DefaultState` и `EditVersion`.

Новая Alembic migration после `a8c1f2d3e4b5_edit_versions.py` должна быть reset-style
структурной миграцией:

1. Удалить старые workflow tables из `utility_network`: `edit_versions`, `work_orders`
   и singleton-форму `default_states`.
2. Удалить старую `public.users`, если seed environment не требует сохранения demo
   accounts.
3. Создать schema `"user"` и таблицу `"user".users`.
4. Создать schema `work_order` и новые `work_order.*` таблицы.
5. Создать `utility_network.network_states`.
6. Создать новую per-WorkOrder форму `utility_network.default_states` и
   `utility_network.default_state_*` таблицы.
7. Создать constraints и indexes для новых таблиц, но не создавать cross-schema FK.

После `alembic upgrade head` стартовый seed заново создает:

```text
demo users -> utility dataset -> work orders -> default states -> FastAPI application
```

Существующие open `EditVersion` не переносятся, потому что в текущем состоянии проекта
они не содержат пользовательских правок. Если перед реализацией появятся реальные
редактируемые данные, этот пункт нужно пересмотреть и заменить reset-style migration
на data migration.

Downgrade должен быть CI-friendly: удалить новые таблицы в обратном порядке, восстановить
старую структуру `public.users`, `utility_network.work_orders`,
`utility_network.default_states` и `utility_network.edit_versions`. Восстановление
данных в downgrade не требуется для seed-only окружения.

### Шаг 3. Repository/use case проверки вместо FK

`WorkOrderService` и `EditVersionService` сохраняют текущие публичные ошибки:

- `ROLE_NOT_ALLOWED`;
- `WORK_ORDER_NOT_FOUND`;
- `WORK_ORDER_STATE_CONFLICT`;
- `WORK_ORDER_CONTEXT_INVALID`.

Но проверка внешних ссылок переносится в repositories/use cases:

- `assignee_user_id` проверяется через `UserRepository`;
- `default_state_id` проверяется через `DefaultStateRepository`;
- source scope проверяется через `UtilityNetworkRepository`;
- отсутствие `DefaultState` для `WorkOrder` возвращает `WORK_ORDER_CONTEXT_INVALID`.

Для schema `work_order` используется единый aggregate repository:

```text
WorkOrderRepository
  get_by_id(...)
  get_by_code(...)
  list_assigned_to_user(...)
  get_open_edit_version(...)
  create_open_edit_version(...)
  touch_edit_version(...)
  save(...)
```

Отдельный `EditVersionRepository` не создается. `EditVersion` является частью агрегата
`WorkOrder`, поэтому все чтение и запись `work_order.work_orders`,
`work_order.edit_versions`, `work_order.edit_version_features` и
`work_order.edit_version_associations` выполняются через `WorkOrderRepository`.
Чтение `DefaultStateFeature`/`DefaultStateAssociation` остается в
`DefaultStateRepository`: service получает baseline aggregate через repository
схемы `utility_network` и передает его rows в метод aggregate repository. Чтобы
не делать три round trips и не получать row explosion от `joinedload` двух
коллекций, `DefaultStateRepository.get_active_aggregate_by_work_order_id(...)`
читает `DefaultState`, features и associations одним SQL через независимые
JSONB aggregation subqueries. Сам SQL хранится в
`utility_service/infrastructure/postgresql/sql/default_state_aggregate.sql` и
читается один раз при импорте repository module.

### Шаг 4. Создание EditVersion через deep copy

`EditVersionService.open_for_work_order` сохраняет внешний сценарий:

```text
assigned + нет open version -> создать EditVersion -> WorkOrder.in_progress -> 201
in_progress + есть open version -> вернуть существующую -> 200
```

Изменяется внутренний create path:

```text
DefaultStateRepository.get_active_aggregate_by_work_order_id(work_order.id)
WorkOrderRepository.create_open_edit_version(...)
```

`create_open_edit_version` должен выполнять insert `edit_versions`,
`edit_version_features` и `edit_version_associations` из переданных baseline
rows. Перевод `WorkOrder` в `in_progress` выполняет `EditVersionService` в той
же transaction boundary через `WorkOrderRepository.save(...)`.

### Шаг 5. Seed path

Startup order можно сохранить:

```text
demo users -> utility dataset -> work orders -> default states -> FastAPI application
```

Но `SeedWorkOrderService` после создания `WorkOrder` должен также создать `DefaultState`
для `WO-001`. Метод refresh baseline закладывается в repository/service слой, но
автоматический trigger на изменение актуальной сети в Спринте 1 не добавляется.

Если `WO-001` уже существует:

- `WorkOrder` не перезаписывается;
- если `DefaultState` отсутствует, он создается;
- если `DefaultState` существует и `EditVersion` еще не создана, ручной/service refresh
  допустим, но автоматического trigger нет;
- если `EditVersion` уже создана, seed не меняет baseline, чтобы не ломать начатую
  работу.

## Совместимость API

Endpoint сохраняется:

```text
POST /api/v1/work-orders/{workOrderId}/edit-versions
```

Response должен вернуть `baseNetworkRevision` - revision, от которой создана рабочая
версия. Поле напрямую маппится на `EditVersion.base_network_revision`.

## CI И Проверки

Обязательные проверки для реализации:

- backend unit tests: `pytest`;
- metadata tests для schema ownership и отсутствия cross-schema FK;
- migration tests для `"user"`, `work_order`, `default_state_*`, `edit_version_*`;
- integration seed-chain test, подтверждающий `WorkOrder + DefaultState`;
- backend API tests, подтверждающие endpoint открытия `EditVersion`;
- compose startup health check.

CI сейчас отдельно запускает:

- backend lint/format/test внутри Docker image;
- `docker compose` startup;
- integration migration/network/seed tests.

Поэтому implementation plan должен обновить tests одновременно с моделями и
миграциями, а не оставлять migration tests на старые constraints.

## Не Входит В Этот Дизайн

- UI workspace editor;
- редактирование features/associations через API;
- `post`, `reconcile`, conflict resolution;
- reviewer approve/reject;
- event bus/outbox для будущих микросервисов;
- поддержка старого публичного API поля `baseRevision`;
- перенос существующих demo `WorkOrder`, `DefaultState` и `EditVersion` данных.

## Критерии Готовности

Дизайн считается реализованным, когда:

1. Пользователи хранятся в schema `"user"`.
2. `WorkOrder` и `EditVersion` хранятся в schema `work_order`.
3. `DefaultState` и его baseline copy rows хранятся в schema `utility_network`.
4. `utility_network.network_states` хранит текущую revision опубликованной сети.
5. Cross-schema FK между `user`, `utility_network` и `work_order` отсутствуют.
6. `EditVersion` создается как deep copy `DefaultState` только для slice текущего
   `WorkOrder`.
7. UUID features/associations сохраняются между DefaultState, EditVersion и будущим
   post.
8. Текущий endpoint открытия edit version работает с согласованным response shape.
9. Startup seed создает `WorkOrder` и связанный `DefaultState`.
10. Structural migration не требует переноса старых seed/demo workflow данных.
11. Backend tests, migration tests и compose startup проходят в CI.

## Зафиксированные Решения Перед Implementation Plan

1. В Спринте 1 изменение актуальной сети не планируется. Достаточно заложить schema и
   метод refresh `DefaultState`; автоматический trigger не добавляется.
2. `DefaultState.status` в первом шаге поддерживает только `active`. Статусы
   `stale` и `closed` не добавляются.
3. Compatibility views на старые `utility_network.work_orders` и
   `utility_network.edit_versions` не создаются. Старый контракт на уровне БД удаляется.
