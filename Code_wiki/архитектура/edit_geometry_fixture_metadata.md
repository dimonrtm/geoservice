---
title: Fixture L-003 и metadata геометрии первого Save
type: technical-note
status: active
created: 2026-10-16
updated: 2026-10-16
source: repository-change:2026-10-16
tags: [fixture, seed, geometry, metadata, edit-version]
---

# Fixture L-003 и metadata геометрии первого Save

## Что подтверждено исходниками

В `synthetic_utility_feeder_01` seed выделяет `UTILITY_EDITABLE_LINE_SPEC` с asset code `L-003`. Это единственная из шести линий с тремя вершинами; остальные имеют по две. Baseline: `(65.520,44.820) → (65.525,44.8205) → (65.530,44.820)`. Меняется vertex index 1. Endpoints совпадают с J-003/J-004; внутренняя вершина не совпадает с junction/device. Seed-тест проверяет valid/simple, полное покрытие AOI, внутреннюю вершину внутри AOI и сохранение связей D-002/D-003 → L-003.

В integration helper `save_geometry_support.py` такой baseline сопоставлен candidate `(65.520,44.820) → (65.525,44.8215) → (65.530,44.820)`. Это синтетическая fixture для проверки Save, не измеренная поправка и не evidence позиционной приёмки. Существующий create-once dataset seed не переписывает старый feeder: исходники не гарантируют эти координаты в ранее созданной БД.

## Координаты и policy

Текущий код использует XY, SRID 4326, диапазоны X `[-180,180]`, Y `[-90,90]`, координатную сетку в градусах и origin 0. В `GeometryPolicy` persisted-параметры — `xy_resolution`, `rounding_mode`, `version`; policy v1 задаёт `ROUND_HALF_AWAY_FROM_ZERO`. Default настройки — `0.0000001`; runtime DI передаёт настройки при создании версии, а Save использует immutable snapshot из EditVersion. Reopen не переносит новую конфигурацию в старую версию.

Отдельных persisted `xyTolerance`, произвольного origin/domain или CRS transformation pipeline этот контракт не задаёт. Проверки диапазона и сетка не являются метрическим positional tolerance. Текущее значение resolution конкретной запущенной версии нужно читать из её persisted policy; в этом ingest БД не опрашивалась и default не выдаётся за production metadata.

## Связь с открытыми вопросами

Для [[Wiki/_registry/questions]] найдены технические основания выбора fixture и реализованной policy. Это устраняет прежнее утверждение об отсутствии eligible объекта в seed, но не закрывает автоматически вопросы в доменном реестре. Нужно различать проверенные исходники, фактическую БД и принятую [[Wiki/specifications/simulated_line_positional_acceptance]]. SIM-EVID-001 не доказывает точность L-003; technical Save по-прежнему возвращает `POSITIONAL_ACCURACY_UNVERIFIED`, topology/review/post не реализуются этой fixture.

## Источники

- `apps/backend/seeds/specs/seed_utility_dataset_specs.py`
- `apps/backend/seeds/tests/test_seed_utility_dataset_specs.py`
- `apps/backend/seeds/specs/seed_work_order_specs.py`
- `apps/backend/tests/integration_tests/save_geometry_support.py`
- `apps/backend/utility_service/domain_services/edit_geometry/policy.py`
- `apps/backend/utility_service/utils/settings.py`
- `apps/backend/utility_service/use_cases/deps.py`
- `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/c8e3f0a5b7d9_edit_version_geometry_policy.py`

Связи: [[edit_geometry_determinism]], [[edit_version_persistence]], [[data_model]].
