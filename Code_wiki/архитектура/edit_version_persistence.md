---
title: Атомарная запись current geometry в EditVersion
type: technical-note
status: active
created: 2026-10-10
updated: 2026-10-10
source: repository-change:2026-10-10
tags: [edit-version, repository, transaction, postgis, geometry]
---

# Атомарная запись current geometry в EditVersion

## Агрегат и transaction boundary

`EditVersionRepository` относится к агрегату `EditVersion`. Геометрия — значение дочернего объекта, а не самостоятельный агрегат. Репозиторий ищет открытую версию (`get_open_edit_version`), создаёт её с объектами и связями из базового состояния (`create_open_edit_version`), обновляет время повторного открытия (`touch_edit_version`) и обслуживает проверку и ограниченную запись текущей геометрии. Production Save service ещё не подключён.

`EditVersionService` получает репозиторий версии отдельной обязательной зависимостью. Все репозитории используют одну AsyncSession. При открытии сервис блокирует наряд через `WorkOrderRepository`, вызывает операции версии через `EditVersionRepository` и сохраняет состояние наряда через `WorkOrderRepository` в общей транзакции. Ошибка после создания снимка откатывает и версию, и состояние наряда. Обработка конфликта уникальности открытой версии остаётся в сервисе.

Вызывающий сервис владеет `AsyncSession` и внешней transaction с READ COMMITTED. Последовательность: `lock_version` → `read_context` → `prepare_candidate` → `validate_candidate` → `write_current`. Repository не начинает и не завершает transaction. `SELECT FOR UPDATE` блокирует root по паре WorkOrder/EditVersion; отдельный последующий SELECT читает current feature, baseline именно по `default_state_id`, AOI и IDs остальных изменённых features всей версии. Column projection исключает stale ORM identity-map state после ожидания конкурента. Workspace AOI-filter к поиску target не применяется.

Порядок будущего Save: root → command → feature. После root нельзя брать конфликтующий lock WorkOrder: существующий reopen использует WorkOrder → EditVersion. AOI, baseline и assignment считаются стабильными на время Save. Writers, обходящие root-lock protocol, этой boundary не защищены.

## Проверка и запись

Подготовка использует persisted GeometryPolicy и [[edit_geometry_determinism]]. Исходные baseline/current проверяются до candidate: связь baseline, структура, endpoints, одна внутренняя вершина, согласованность operation; повреждённый context отвергается без repair. Другая feature с operation, отличной от `unchanged`, блокирует изменение независимо от её попадания в workspace.

PostGIS проверяет XY/SRID/range, nonempty, `ST_IsValid`, `ST_IsSimple`, соседние совпадающие вершины и валидность AOI. Guarded `ST_Covers` проверяет всю линию, включая сегменты между vertices: boundary разрешена, holes и разрывы MultiPolygon учитываются. Временное правило D5-Q1 отвергает нулевой сегмент после canonicalization как `GEOMETRY_INVALID`; доменная допустимость требует уточнения, источник — принятая спецификация Дня 5.

`write_current` принимает только результат проверки, выданный repository. UPDATE меняет geometry/operation ровно одной current feature; DefaultState, associations, properties, network_version и draft_revision остаются прежними. Numeric no-op не выполняет UPDATE и сохраняет current EWKB. Revert после реального изменения восстанавливает точный baseline EWKB, включая off-grid координаты и signed zero.

## Lifetime handles

Frozen handles проверяются по identity реально выданных объектов, session, transaction и поколению чтения. Commit/rollback освобождает ссылки. Любой savepoint во время жизни scope делает его непригодным до завершения внешней transaction. Mutation и no-op потребляют все прежние context этой версии; новое чтение под тем же root lock допустимо. Это защита от ошибочного использования протокола, не sandbox для произвольного Python-кода. Два session-local SQLAlchemy listeners живут вместе с session и не накапливаются при повторных transaction.

Ожидаемые отказы представлены `RepositoryRejection`; неправильное использование handles — `RepositoryProtocolError`. HTTP mapping, actor/access/lifecycle, token/replay, registry, revision и events остаются ответственностью будущего Save service. Интеграционный сценарий подтверждает совместимость записи с существующим history trigger, но не заменяет такую orchestration.

## Источники и связи

- `apps/backend/utility_service/infrastructure/postgresql/repositories/edit_version_repository.py`
- `apps/backend/utility_service/infrastructure/postgresql/repositories/edit_geometry_scope.py`
- `apps/backend/utility_service/infrastructure/postgresql/repositories/edit_geometry_validation.py`
- `apps/backend/utility_service/infrastructure/postgresql/sql/edit_geometry_context.sql`
- `apps/backend/utility_service/infrastructure/postgresql/sql/edit_geometry_spatial.sql`
- `apps/backend/tests/integration_tests/test_edit_geometry_concurrency.py`
- `apps/backend/tests/integration_tests/test_edit_geometry_mutation.py`
- `docs/sprint_2/2026-10-10-day-5-repository-context-design.md`
- [[backend]], [[data_model]], [[edit_geometry_determinism]].
