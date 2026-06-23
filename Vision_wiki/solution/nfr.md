---
title: NFR
type: solution
status: active
created: 2026-05-30
updated: 2026-06-23
source: "RAW_inputs/documents/спринт 1.odt; Vision_wiki/chats/2026-06-06-phase-f6-constraints-and-nfr.md; RAW_inputs/documents/utility_gis_editor_target_times.md; Vision_wiki/chats/2026-06-07-phase-f7-metrics-and-risks.md; user answers to /discover --phase Ф8, 2026-06-11; RAW_inputs/meetings/geometry_association_conflict_f6.md"
tags: [solution, nfr, release-1, demo]
---

# NFR

NFR нового Release 1. Старые generic map/CRUD ограничения применяются как foundation, если не конфликтуют с utility workflow.

## Ф8 Safety Invariants

- Post выполняется одной database transaction.
- Validation, unresolved conflicts, missing approval и stale `Default` блокируют post.
- Protective failure сохраняет change set.
- `Editor` не может approve собственную `EditVersion`.
- Любое изменение после validation/reconcile/approval инвалидирует последующие результаты.
- Post нельзя выполнить повторно.
- WebSocket events публикуются только после успешного commit.

## Performance

- Realtime updates должны доходить до других клиентов через WebSocket в течение 1-2 секунд.
- Bbox loading обязателен для карты; запросы без валидного bbox не должны становиться неограниченной загрузкой данных.
- `limit` для bbox endpoint: default 500, max 5000.
- Если GeoJSON import используется для подготовки demo data, он остается SYNC и ограничивается 20MB; это не acceptance criterion utility workflow.
- Целевой demo dataset: `synthetic_utility_feeder_01` с 1 AOI, 1 feeder, 7 junctions, 6 line segments, 6 devices, 8-10 associations, 2 work orders, 3 users, `Default` + 2 edit versions и 4 conflict-сценариями.

### Utility Demo P95 Targets

Рабочие acceptance targets из `RAW_inputs/documents/utility_gis_editor_target_times.md`:

| Операция | P95 |
|---|---:|
| Map load до пригодного к работе AOI | <= 5 сек |
| Переход к объекту / AOI | <= 2 сек |
| Сохранение одного edit | <= 2 сек |
| Сохранение 5-20 edits | <= 5 сек |
| Validation рабочего AOI | <= 15 сек |
| Reconcile без конфликтов | <= 10 сек |
| Reconcile до списка конфликтов | <= 20 сек |
| Открытие conflict diff | <= 5 сек |
| Post в `Default` | <= 15 сек |
| Отказ post при stale `Default` | <= 5 сек |

Эти пороги являются draft SLO для малого synthetic dataset и требуют benchmark на reference hardware. Ручное разрешение конфликтов не входит во время reconcile; измеряется время до показа списка конфликтов.

Ф7 разделяет targets по критичности. Обязательны single edit save, small AOI validation, reconcile без conflicts, показ conflicts, conflict diff, post и stale-post rejection. Initial map load, jump to AOI, batch save и full refresh могут временно нарушать target без автоматического провала demo. Benchmark выполняется 30 повторов.

## Security

- Все API endpoints требуют валидный Bearer token.
- `401 Unauthorized`: token отсутствует или невалиден.
- `403 Forbidden`: `Viewer` пытается выполнить `POST`/`PATCH`/`DELETE`.
- Активные роли Release 1: `Editor` и `Reviewer`; совмещение этих ролей одним пользователем запрещено.
- Legacy `Viewer` может оставаться compatibility role для read-only foundation, но не является участником основного Release 1 workflow.
- CORS должен ограничиваться нужными origins; refresh token отложен.

## Availability

- Источник требует воспроизводимый запуск: DB up -> API up -> Front up -> map shows data.
- Reference hardware: ноутбук Asus TUF Gaming 2022 года, AMD Ryzen 7 5000 series, 16 GB RAM.
- Первый запуск Docker Compose и явный reset должны укладываться в несколько минут.
- Обычный restart сохраняет данные; обычный reset восстанавливает synthetic seed и сохраняет `audit_log`.
- Отдельный `full-clean` удаляет demo data и audit.
- Первый поддерживаемый browser - Chrome; расширение browser support отложено.
- CI/CD или локальный pseudo-CI должен иметь зеленые lint/tests/build commands.
- При WebSocket reconnect frontend должен переподписаться и выполнить bbox reload для восстановления консистентности.
- Для local demo не требуются SLA, backup и restore.

## Observability And Audit

- Нужны healthcheck, container logs, correlation ID и понятные UI errors.
- `audit_log` должен переживать restart и обычный reset.
- Минимальные audit fields: actor, role, action, timestamp, target entity, work order/version, before/after summary и result.
- Минимальные audit events: login, создание edit version, feature/association edit, validation, reconcile, conflict resolution, review decision, post, reset и `full-clean`.

## Release 2 Conflict Package NFR

NFR Release 2 `geometry/association conflict` относятся к developer demo
consequence package и не являются production SLA.

Обязательные свойства package:

- core evidence вычисляется из текущей модели: `Base / Mine / Default`,
  geometry diff, association delta, dirty areas, validation/network errors,
  trace evidence, conditional subnetwork status, current version moments и
  stale conditions;
- contextual evidence может быть fixture/reference: work order metadata, field
  evidence, photos, reviewer comments, escalation note и human-readable
  rationale;
- fixture trace/subnetwork evidence допустимо только как frozen replay с явно
  маркированной контрольной версией/checksum;
- happy path не важнее stale/pre-post failure sidecar.

### Release 2 P95 Draft Targets

| Операция | P95 |
|---|---:|
| Открытие готового package summary | <= 2 сек |
| Открытие evidence details | <= 2.5 сек |
| Stale/block status из уже рассчитанных сигналов | <= 1 сек |
| Audit save ACK | <= 1 сек |
| Audit readable in UI | <= 3 сек |

Trace, validate и update-subnetwork-sensitive evidence должны выполняться как
async job с progress/freshness state. UI должен быстро показывать `job accepted`,
этап job, freshness moment и можно ли переиспользовать cached evidence.

### Release 2 Observability

Минимальные signals:

- `package_build_duration_ms`, `diff_extraction_ms`, `association_read_ms`,
  `dirty_area_fetch_ms`, `trace_job_ms`, `subnetwork_status_fetch_ms`,
  `audit_save_ms`, `stale_detection_ms`;
- `trace_consistency_failures`, `subnetwork_invalid_count`,
  `hard_blocker_count`, `package_recomputed_count`, `approval_staled_count`;
- source-of-truth moments: `version_modified`, `version_reconciled`,
  `common_ancestor`, `subnetwork_last_update`, `package_computed_at`.

### Release 2 Audit Object

Минимальный audit object должен фиксировать:

- `package_id`, `version_name`, `version_owner`, `feature_service`,
  `conflict_ids`, `affected_asset_ids`;
- `created`, `modified`, `reconciled`, `common_ancestor`, а для
  subnetwork-sensitive cases - `last_update_subnetwork` и `subnetwork_status`;
- refs/hashes на Base/Mine/Default diff, association delta, dirty area sample,
  validation result, trace result, subnetwork status и work order/field evidence;
- `risk_tier`, `hard_blockers[]`, `reviewer_decision`, `rationale`,
  `review_note`, `escalated_to`, `resolved_by`;
- `stale`, `stale_reason`, `stale_trigger_event`,
  `recomputed_from_package_id`;
- `posted`, `post_time`, `post_result`, `reconcile_required_before_post`.

## Data And Compliance

- Формат данных: GeoJSON.
- SRID: 4326.
- Порядок координат: `[lon, lat]`.
- `Feature.geometry.type` должен совпадать с `Layer.geometryType`, иначе `422`.
- Координаты должны быть в диапазонах lon `[-180, 180]`, lat `[-90, 90]`, иначе `422`.
- `version` хранится top-level и обязателен для edit/delete concurrency.

## Maintainability

- Контракты backend/frontend нельзя менять breaking changes в течение Release 1.
- Любое изменение API shape должно идти вместе с frontend update в одном PR/MR.
- Все изменения БД идут через миграции, не руками в production.
- Зависимости backend направлены внутрь: `api -> services -> repositories -> db/models`.
- Documentation DoD: run docs, API endpoints, WebSocket protocol, ограничения MVP.
- `import GeoJSON` не является acceptance criterion основного workflow; он может использоваться внутренне для подготовки synthetic seed.

## Источники

- `RAW_inputs/documents/спринт 1.odt`
- `Vision_wiki/chats/2026-06-06-phase-f6-constraints-and-nfr.md`
- `RAW_inputs/documents/utility_gis_editor_target_times.md`
- `RAW_inputs/meetings/geometry_association_conflict_f6.md`
- [[../../Code_wiki/архитектура/api_contract_first_release_requirements]]
- [[../decisions/release_1_utility_workflow]]
- [[../chats/2026-06-11-phase-f8-release-1-closeout]]
