---
title: Детерминированная геометрия EditVersion
type: technical-note
status: active
created: 2026-10-08
updated: 2026-10-08
source: repository-change:2026-10-08
tags: [geometry, decimal, edit-version, fingerprint, postgis]
---

# Детерминированная геометрия EditVersion

## Границы ответственности

`apps/backend/utility_service/domain_services/edit_geometry/` содержит чистое ядро подготовки геометрии и fingerprint. Оно не обращается к БД или global settings. Вызов получает immutable baseline, policy и context явно; current используется только для проверки перехода и no-op. Это позволяет вычислять идентичность до решения об успешности команды и повторять вычисление после изменения current.

Raw JSON parser `web_api/parsers/geometry_save_request.py` читает координаты непосредственно в Decimal до float-конверсии. Ограничения чисел: token не длиннее 64 символов, абсолютная явная exponent не больше 324, X в `[-180,180]`, Y в `[-90,90]`. Форма — строгий XY LineString, без duplicate keys и дополнительных полей. Parser/DTO пока не подключены к отдельному Save endpoint.

## Canonicalization и идентичность

Policy v1: EPSG:4326, origin `(0,0)`, XY, `ROUND_HALF_AWAY_FROM_ZERO`. Grid по умолчанию и минимум `0.0000001`, максимум `360`, `grid * 10^9` должен быть целым. Дополнительные конечные нули допустимы. Это вычислительная сетка, а не подтверждение геодезической точности исходных данных.

Для каждой ordinate сравниваются округлённые request и baseline. Если они равны, восстанавливается точное baseline значение; иначе используется округлённый request. Baseline/current целиком не нормализуются. Endpoints и количество вершин сохраняются; меняется не более одной внутренней вершины. После изменения A переход к B требует отдельного Revert. No-op сравнивается с current, operation — с baseline.

Fingerprint `geom-v1:sha256:<hex>` строится по canonical JSON с сортировкой ключей, compact separators и ASCII escaping. Числа координат внутри hash представлены Decimal-строками без exponent/конечных нулей; signed zero нормализуется. Context включает actor, WorkOrder/EditVersion/feature/defaultState, baseline revision/hash и сырой `draftVersionToken`. CommandId, current, результат проверки и настройки процесса исключены.

Для совпадающей структуры fingerprint включает весь canonical candidate даже при endpoint/multiple-vertex rejection. Для несовпадающей структуры используется `unmatched_structure` со всеми исходными значениями без grid-rounding. Golden bytes и digest закреплены в `domain_services/tests/test_geometry_fingerprint.py`.

## Policy как часть persisted версии

Revision `c8e3f0a5b7d9` после `b7d2e9f4a6c8` добавляет `geometry_xy_resolution NUMERIC`, `geometry_rounding_mode VARCHAR(32)` и `geometry_policy_version SMALLINT`: NOT NULL, без server defaults. CHECK контролируют допустимость, UPDATE trigger запрещает изменение policy. `EditVersionService` получает policy через DI и передаёт в repository только при создании. Reopen меняет timestamp, сохраняя policy.

Backfill читает параметры geometry из окружения migrator отдельной frozen validation, без импорта runtime Settings/JWT. Данные и DDL изменяются одной транзакцией; геометрия, revision и история команд не пересчитываются. Старый API требуется остановить перед migration. Downgrade уничтожает policy snapshots, следующий upgrade назначает policy заново. Операционный порядок: `docs/sprint_2/2026-10-08-day-4-geometry-runbook.md`.

## Точный storage/readback

`infrastructure/postgresql/geometry_codec.py` принимает только непустые XY Point/LineString SRID 4326 в EWKB. Каждая binary64 ordinate переводится через `Decimal(repr(float_value))`; обратная запись проверяет равенство после roundtrip. Signed zero сохраняется codec и baseline copying; нормализация для hash выполняется отдельно.

`workspace_aggregate.sql` возвращает features как EWKB hex; `WorkOrderRepository` преобразует их в прежний `geometry_data` с JSON numbers. Остаётся один aggregate SQL execute, AOI-фильтрация, порядок и прежняя публичная форма ответа. Это предотвращает сдвиг off-grid baseline возле midpoint из-за девяти знаков `ST_AsGeoJSON`. AOI display и legacy API этим механизмом не перестраиваются.

## Источники и связи

- `apps/backend/utility_service/domain_services/edit_geometry/`
- `apps/backend/utility_service/infrastructure/postgresql/geometry_codec.py`
- `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/c8e3f0a5b7d9_edit_version_geometry_policy.py`
- `apps/backend/tests/integration_tests/test_geometry_policy_migration.py`
- `apps/backend/tests/integration_tests/test_geometry_policy_lifecycle.py`
- `apps/backend/tests/integration_tests/test_geometry_roundtrip.py`
- `docs/sprint_2/2026-10-08-day-4-geometry-design.md`
- [[backend]], [[data_model]], [[api_and_realtime]].
