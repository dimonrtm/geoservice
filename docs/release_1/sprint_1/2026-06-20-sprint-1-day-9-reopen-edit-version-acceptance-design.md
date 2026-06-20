# Спринт 1, Пункт 9: Acceptance Test Повторного Открытия EditVersion

Дата: 2026-06-20
Статус: согласован для design spec
Расположение: `docs/release_1/sprint_1`

## Назначение

Пункт 9 усиливает acceptance/integration coverage для backend-сценария повторного
открытия `EditVersion`:

```text
Editor повторно входит в назначенный WorkOrder
-> backend возвращает существующую открытую EditVersion
-> новая EditVersion и новые рабочие копии features/associations не создаются
```

Сценарий должен проверяться через реальный backend/DB seed path, а не через мок
service/API. Риск, который закрывает тест: повторный вход в уже начатую задачу
незаметно создает дубль `EditVersion` или повторно копирует рабочий slice сети.

## Выбранный Подход

Добавить новый integration/acceptance test в:

```text
apps/backend/tests/integration_tests/test_work_order_seed_chain_integration.py
```

Файл уже содержит нужную инфраструктуру:

- очистку canonical seed chain через `remove_canonical_seed_chain`;
- запуск demo users, utility dataset и work order seed через `run_seed_chain`;
- реальный `EditVersionService` с `UserRepository`, `WorkOrderRepository` и
  `DefaultStateRepository`;
- `run_in_rollback_transaction`, который skip-ает тесты без `RUN_DB_TESTS=1` и
  откатывает изменения после сценария.

Новый тест логически продолжает существующий
`test_seed_chain_opens_edit_version_with_full_default_state_slice`, но проверяет
не первое создание, а идемпотентный повторный вход.

## Test Scope

Новый тест:

```python
test_reopening_seeded_edit_version_returns_existing_version_without_duplicates
```

Проверяет один happy-path сценарий на реальной БД:

1. Очистить canonical seed chain.
2. Запустить seed chain.
3. Найти `assignee_id` по `SEED_WORK_ORDER_SPEC.assignee_email`.
4. Вызвать `EditVersionService.open_for_work_order(...)` первый раз.
5. Зафиксировать `edit_version.id`, `last_opened_at`, количество open versions,
   количество `EditVersionFeature` и `EditVersionAssociation`.
6. Вызвать `EditVersionService.open_for_work_order(...)` второй раз для того же
   `WorkOrder`.
7. Проверить, что второй вызов вернул существующую версию без дублей.

## Acceptance Criteria

Тест считается достаточным, когда подтверждает:

1. Первый вызов возвращает `created=True`.
2. Второй вызов возвращает `created=False`.
3. `first_result.edit_version.id == second_result.edit_version.id`.
4. В `work_order.edit_versions` для `SEED_WORK_ORDER_SPEC.id` остается ровно одна
   `open` version.
5. Для этой `EditVersion` остается ровно `19` строк `edit_version_features`.
6. Для этой `EditVersion` остается ровно `9` строк `edit_version_associations`.
7. `last_opened_at` после второго входа не меньше значения после первого входа.
8. Тест использует стандартный `require_db_tests()` path и skip-ается без
   `RUN_DB_TESTS=1`.

## Не Входит В Scope

- Новый HTTP-level integration test через FastAPI route.
- Изменение production-кода `EditVersionService`, repositories или migrations.
- Новые fixtures, если сценарий остается читаемым с существующими helper-функциями.
- Дополнительная проверка partial unique index: storage-level duplicate guard уже
  покрыт в `tests/integration_tests/test_edit_version_migration.py`.
- Новые wiki/Code_wiki знания: текущий технический контракт уже зафиксирован в
  `Code_wiki`, а задача добавляет acceptance coverage.

## Размещение В Существующей Тестовой Структуре

Новый тест добавляется в конец
`apps/backend/tests/integration_tests/test_work_order_seed_chain_integration.py`
рядом с другими seed-chain acceptance сценариями.

Для подсчета строк использовать SQLAlchemy `select(func.count(...))`, как в
существующем файле:

- `EditVersion.id`;
- `EditVersionFeature.feature_id`;
- `EditVersionAssociation.association_id`.

Для open version count фильтровать:

```python
EditVersion.work_order_id == SEED_WORK_ORDER_SPEC.id
EditVersion.status == EditVersionStatus.OPEN
```

Если в файле еще не импортирован `EditVersionStatus`, добавить его из
`utility_service.infrastructure.postgresql.models.work_order`.

## Verification

Focused integration test:

```powershell
cd apps/backend
python -m pytest tests/integration_tests/test_work_order_seed_chain_integration.py::test_reopening_seeded_edit_version_returns_existing_version_without_duplicates -q
```

При `RUN_DB_TESTS` не равном `1` ожидается `SKIPPED`.

Если PostgreSQL/PostGIS integration окружение включено:

```powershell
python -m pytest tests/integration_tests/test_work_order_seed_chain_integration.py -q
```

Перед завершением implementation task желательно прогнать связанный набор:

```powershell
python -m pytest utility_service/use_cases/tests/test_edit_version_service.py tests/integration_tests/test_work_order_seed_chain_integration.py -q
```

## Consequences

Пункт 9 закрывает gap между unit/API мок-проверками и storage constraint:
теперь реальный seed-chain path доказывает, что application logic повторно
открывает существующую `EditVersion`, а не пытается создать вторую рабочую
версию или повторно скопировать рабочие features/associations.
