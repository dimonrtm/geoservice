# Спринт 1, День 7: Документация И Резерв

Дата: 2026-06-19
Статус: согласован пользователем
Расположение: `docs/release_1/sprint_1`

## Назначение

День 7 является облегченным днем документации и резерва после интеграционной
проверки Дня 6 и перед началом блока `EditVersion`.

Цель дня - сверить фактическую основу Спринта 1 после Дней 2-6 с исходными
контрактами Дня 1, уточнить схему данных и тестовые сценарии, а также явно
зафиксировать ранние блокеры для Дня 8. Новая пользовательская функциональность
не добавляется.

День 7 закрывает риск, что backend foundation уже развивается вертикально, но
документы, API-ожидания, seed-инварианты и тестовые gates начинают расходиться
до появления `EditVersion`, `Workspace API` и frontend.

## Выбранный Подход

Используется легкий audit-and-alignment spec без production-кода.

Результатом дня является актуализированный documentation baseline:

- что считается стабильным контрактом после Дней 1-6;
- какие data model и seed invariants являются prerequisite для Дня 8;
- какие тестовые сценарии должны защищать вертикаль Спринта 1;
- какие ранние блокеры закрыты документацией, а какие остаются явными
  prerequisites или follow-up.

Такой подход сохраняет облегченный режим дня: он не открывает новый backend или
frontend scope, но снижает риск обнаружить несовместимость только на этапе
`EditVersion` и workspace.

## Граница Scope

### Входит

- сверка acceptance-сценария Дня 1 с результатами Дней 2-6;
- сверка API-контракта Дня 1 с уточнениями role guard, utility dataset и
  `WorkOrder`;
- сверка схемы данных для `User`, `AOI`, `Feeder`, `NetworkFeature`,
  `NetworkAssociation` и `WorkOrder`;
- сверка seed chain `demo users -> utility dataset -> work orders`;
- актуализация тестовых сценариев Sprint 1 baseline;
- фиксация ранних блокеров и решений по ним;
- обновление ссылок в `docs/release_1/sprint_1/README.md`;
- русскоязычная документация с сохранением API paths, JSON keys, enum values,
  identifiers и file paths на языке исходного кода.

### Не Входит

- production-код;
- Alembic migrations;
- новые SQLAlchemy-модели или поля;
- публичные endpoints `/api/v1/work-orders/...`;
- `EditVersion` model или API;
- workspace API;
- frontend `My Work Orders` или `Edit Workspace`;
- reviewer queue, approve/reject, validation, reconcile или post;
- reset/full-clean для demo dataset;
- repository-change ingest как обязательный шаг.

## Контрактная Матрица

День 7 использует матрицу сверки вместо новой архитектуры.

| Область | Источник Истинности | Что Сверить | Результат |
|---|---|---|---|
| Acceptance | `2026-06-12-sprint-1-day-1-acceptance-design.md` | `Login -> My Work Orders -> Create/Open EditVersion -> Edit Workspace` остается целью Спринта 1, но Дни 2-6 покрывают только backend foundation | Не расширять День 7 до пользовательского workflow |
| API | `2026-06-12-sprint-1-day-1-api-contract-design.md` | Error `code`, HTTP semantics и masking policy не противоречат новым role/work-order ошибкам | Уточнения оформить как documentation alignment, не как новый endpoint |
| Roles | `2026-06-13-sprint-1-day-2-roles-access-design.md` | `Editor` и `Reviewer` существуют, separation of duties сохраняется | `Reviewer` не становится assignee и не получает workflow в Sprint 1 |
| Network Data | `2026-06-14-sprint-1-day-3-network-model-design.md`, `2026-06-15-sprint-1-day-4-utility-dataset-design.md` | `AOI`, `Feeder`, features и associations остаются read-only baseline для workspace | Не добавлять editing, validation или topology recalculation |
| Work Orders | `2026-06-17-sprint-1-day-5-work-orders-design.md` | `WO-001` связан с active `Editor`, `AOI` и `Feeder`; create-once seed сохраняется | Дальше можно проектировать `EditVersion` поверх устойчивого work order |
| Integration | `2026-06-18-sprint-1-day-6-integration-check-design.md` | Startup seed order и idempotency gates подтверждают целостность chain | Блокеры seed/migration должны быть видимым prerequisite для Дня 8 |

## Data Model Baseline Перед Днем 8

К началу Дня 8 документация должна считать стабильными следующие связи:

```text
User(Editor) -> WorkOrder -> AOI
                         -> Feeder -> NetworkFeature
                                   -> NetworkAssociation
```

`WorkOrder` является мостом между пользователем и рабочим участком сети.
`AOI` задает серверную границу будущего workspace. `Feeder` задает агрегат
demo-сети, а `NetworkFeature` и `NetworkAssociation` остаются read-only
содержимым, которое будет показано в workspace позже.

День 7 не выбирает окончательную структуру `EditVersion`. Он только фиксирует,
что будущая version должна создаваться от конкретного `WorkOrder`, не обходить
assignment guard и не создавать дубликаты активной version для того же
пользователя и задачи.

## Тестовый Baseline

После Дня 7 документация Спринта 1 должна различать четыре уровня проверок:

| Уровень | Назначение | Примеры |
|---|---|---|
| Unit | Быстро проверить isolated business rules | role guard, seed specs, work-order service status transition |
| Metadata | Защитить schema/ORM contract | table names, schema `utility_network`, FK, CHECK/UNIQUE constraints |
| Integration Smoke | Проверить, что части живут вместе | migrations, seed chain, `WO-001 -> User/AOI/Feeder` |
| Sprint Acceptance | Подтвердить полный пользовательский путь | login, assigned work order, create/open version, workspace |

День 7 не требует полного end-to-end smoke, потому что frontend и
`EditVersion` еще не реализованы. Он должен оставить явный список checks,
которые станут обязательными после Дней 8-12.

## Ранние Блокеры И Решения

| Блокер | Риск | Решение Дня 7 |
|---|---|---|
| Документы Дня 1 не знают о фактическом `WorkOrder` foundation | День 8 может спроектировать `EditVersion` мимо assignment и seed rules | Зафиксировать `WorkOrder` как prerequisite и bridge к `EditVersion` |
| Seed chain не считается частью sprint baseline | Локальный demo может проходить unit-тесты, но падать при startup | Считать День 6 источником baseline для startup order и idempotency |
| API-контракт и use-case error codes расходятся | Router Дня 8-10 может смешать masking policy и доменные ошибки | Отдельно сверить error `code` и HTTP behavior перед добавлением endpoints |
| `Reviewer` существует, но его workflow вне scope | Можно случайно добавить reviewer queue раньше времени | Повторно зафиксировать separation of duties без reviewer workflow |
| Старые `legacy-generic-plan` документы содержат другой День 7 | Агент может взять realtime scope из исторического плана | README и design должны явно ссылаться на актуальный Utility Workflow scope |

## Обработка Несоответствий

Если при сверке находится расхождение между документами и фактическим Sprint 1
baseline, День 7 выбирает один из трех путей:

1. Исправить документацию, если код и ранее согласованный scope уже однозначны.
2. Записать prerequisite для Дня 8, если без этого нельзя безопасно проектировать
   `EditVersion`.
3. Вынести follow-up за пределы Sprint 1, если тема относится к editing,
   validation, reconcile, post, reviewer workflow или production administration.

День 7 не должен исправлять code-level проблемы. Если обнаружен реальный дефект
в production-коде, он фиксируется как блокер или prerequisite для отдельной
задачи реализации.

## Критерии Готовности

День 7 завершен, когда:

1. актуальный Sprint 1 README содержит ссылку на design Дня 7;
2. scope Дня 7 явно отделен от старого `legacy-generic-plan/day-7-plan.md`;
3. контракты Дней 1-6 описаны как единый baseline перед `EditVersion`;
4. data model и seed chain prerequisites для Дня 8 перечислены явно;
5. тестовые уровни Sprint 1 baseline описаны без требования преждевременного
   end-to-end;
6. ранние блокеры имеют решение: закрыть документацией, перенести в День 8 или
   вынести за Sprint 1;
7. production-код, migrations, public API, frontend и `EditVersion` не добавлены.

## Последствия Решения

- День 8 может проектировать `EditVersion` поверх проверенной связки
  `User -> WorkOrder -> AOI/Feeder`.
- Старый realtime Day 7 остается историческим материалом и не влияет на текущий
  Utility Workflow.
- Документация становится gate перед следующими интенсивными днями, но не
  превращается в скрытый implementation plan.
- Если при будущей реализации выяснится, что фактический код противоречит этому
  baseline, исправление должно идти отдельной implementation-задачей, а не
  задним числом расширять День 7.
