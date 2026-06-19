# Спринт 1, День 7: Результат Сверки Документации И Резерва

Дата: 2026-06-19
Статус: выполнено
Расположение: `docs/release_1/sprint_1`

## Назначение

Документ фиксирует результат выполнения Дня 7: сверку контрактов, схемы данных,
seed chain, тестовых сценариев и ранних блокеров перед началом блока
`EditVersion`.

День 7 не добавлял production-код, migrations, public API, frontend,
`EditVersion` model/API, workspace API, reviewer workflow, validation,
reconcile или post. Результатом является documentation baseline для Дня 8.

## Сверка Контрактов

| Область | Проверенный источник | Итог сверки | Решение |
|---|---|---|---|
| Acceptance | `2026-06-12-sprint-1-day-1-acceptance-design.md` | Цель Спринта 1 остается `Login -> My Work Orders -> Create/Open EditVersion -> Edit Workspace`. Дни 2-6 закрывают backend prerequisites, но еще не реализуют пользовательский путь целиком. | Считать Дни 8-12 ответственными за `EditVersion`, workspace API и frontend. |
| API | `2026-06-12-sprint-1-day-1-api-contract-design.md` | Дневной baseline сохраняет error `code`, HTTP semantics и русскоязычный `message`. День 2 сознательно уточнил `WORK_ORDER_NOT_ASSIGNED` для локальной диагностики. | Перед добавлением routes нужно явно выбрать, где маскировать чужой `WorkOrder` как `404`, а где оставлять доменный `403 WORK_ORDER_NOT_ASSIGNED`. |
| Roles | `2026-06-13-sprint-1-day-2-roles-access-design.md` | `Editor` и `Reviewer` разделены; `Reviewer` входит в систему, но не получает editor workspace и не становится assignee. | Reviewer queue, approve/reject и post остаются вне Sprint 1. |
| Network Data | `2026-06-14-sprint-1-day-3-network-model-design.md`, `2026-06-15-sprint-1-day-4-utility-dataset-design.md` | `AOI`, `Feeder`, `NetworkFeature` и `NetworkAssociation` дают read-only основу будущего workspace. | Не добавлять editing, validation, topology recalculation или clipping behavior в День 8. |
| Work Orders | `2026-06-17-sprint-1-day-5-work-orders-design.md` | `WorkOrder` является устойчивым bridge от `User(Editor)` к `AOI` и `Feeder`; статусы ограничены `assigned` и `in_progress`; seed `WO-001` create-once. | День 8 должен создавать/open version только через assignment guard и существующий `WorkOrderService`. |
| Integration | `2026-06-18-sprint-1-day-6-integration-check-design.md`, `apps/backend/scripts/start_utility_service.sh`, `apps/backend/tests/test_compose_startup_contract.py` | Startup order содержит `seed_demo_users`, `seed_utility_dataset`, `seed_work_orders`, затем `uvicorn`. Интеграционный тест `test_work_order_seed_chain_integration.py` существует. | Seed/migration проблемы считать блокерами Дня 8, а не скрытыми frontend/API проблемами. |

## Data Baseline Перед Днем 8

Активная связка перед проектированием `EditVersion`:

```text
User(Editor) -> WorkOrder -> AOI
                         -> Feeder -> NetworkFeature
                                   -> NetworkAssociation
```

Стабильные элементы baseline:

- `alexey.editor@example.local` существует как active `Editor`;
- `marina.reviewer@example.local` существует как `Reviewer`, но не может быть
  assignee для `WO-001`;
- `synthetic_utility_feeder_01` является canonical demo feeder;
- `WO-001` имеет стабильный UUID `6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0401`;
- `WO-001` назначен `alexey.editor@example.local`;
- `WO-001` связан с существующими `AOI` и `Feeder`;
- `WorkOrderStatus` содержит только `assigned` и `in_progress`;
- повторный seed не должен дублировать или перезаписывать `WO-001`.

Последствие для Дня 8: `EditVersion` должна создаваться от конкретного
`WorkOrder`, использовать актуального `actor_id`, уважать assignment guard,
переводить `WorkOrder` в `in_progress` только через доменный сервис и
предотвращать дубли active version.

## Тестовый Baseline

| Уровень | Текущее назначение | Проверяемые источники |
|---|---|---|
| Unit | Быстро защищать доменные правила и seed specs | `seeds/tests/test_seed_demo_user_service.py`, `seeds/tests/test_seed_utility_dataset_specs.py`, `seeds/tests/test_seed_work_order_specs.py`, `utility_service/use_cases/tests/test_work_order_service.py` |
| Metadata | Защищать SQLAlchemy schema, constraints и enum values | `utility_service/infrastructure/tests/test_network_model_metadata.py` |
| Integration Smoke | Проверять migration/startup/seed chain и FK-связи | `tests/test_compose_startup_contract.py`, `tests/integration_tests/test_work_order_seed_chain_integration.py` |
| Sprint Acceptance | Подтверждать полный пользовательский путь на чистом seed | Будущие проверки после Дней 8-12: login, assigned work order, create/open version, workspace |

До реализации `EditVersion` полный end-to-end smoke не является gate Дня 7.
После Дней 8-12 он должен стать основным подтверждением Sprint 1 acceptance.

## Ранние Блокеры И Решения

| Блокер | Решение Дня 7 | Статус Перед Днем 8 |
|---|---|---|
| Старый `legacy-generic-plan/day-7-plan.md` описывает realtime scope прежнего generic GIS плана. | Зафиксировано, что он исторический и не управляет текущим Utility Workflow. | Закрыт документацией. |
| День 1 допускает masking `404` для чужого `WorkOrder`, а День 2 ввел диагностический `403 WORK_ORDER_NOT_ASSIGNED`. | Перед public routes нужно явно оформить adapter policy: use-case может различать ошибки, API может маскировать их согласно endpoint contract. | Prerequisite для Work Orders/EditVersion API. |
| `EditVersion` еще не имеет окончательной storage-модели. | День 7 не проектирует структуру version, но фиксирует входные invariants: `WorkOrder`, `actor_id`, assignment guard, active-version uniqueness. | Prerequisite для Дня 8. |
| Seed chain может быть принят за неважную операционную деталь. | Startup order и idempotency считаются Sprint 1 baseline. | Закрыт документацией; regression остается в тестах Дня 6. |
| Reviewer role может преждевременно втянуть reviewer workflow. | Повторно закреплено: `Reviewer` существует для separation of duties, но queue/approve/reject/post вне Sprint 1. | Закрыт документацией. |

## Активный Scope Дня 7

Актуальный День 7 - это `documentation reserve` для текущего Utility Workflow.
Файл `docs/release_1/sprint_1/legacy-generic-plan/day-7-plan.md` остается
историческим материалом прежнего generic GIS scope и не является источником
задач для текущего Спринта 1.

День 7 не создал и не должен был создавать:

- production-код;
- migrations;
- public Work Orders API;
- `EditVersion`;
- workspace API;
- frontend;
- reviewer queue, approve/reject или post;
- validation, reconcile или editing.

## Критерии Готовности Дня 7

День 7 считается выполненным, потому что:

1. design/spec Дня 7 принят и связан из Sprint 1 README;
2. создан execution plan для doc-only реализации;
3. создан результат сверки документации и резерва;
4. baseline Дней 1-6 описан как вход для Дня 8;
5. ранние блокеры получили решение или статус prerequisite;
6. legacy generic Day 7 явно отделен от текущего Utility Workflow;
7. production scope не расширен.
