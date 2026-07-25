---
title: First Save For EditVersion
type: source-summary
status: active
created: 2026-07-25
updated: 2026-07-25
source: RAW_inputs/meetings/first_save_for_edit_version.md
tags: [source-summary, edit-version, first-save, ddd]
---

# First Save For EditVersion

## Контекст

Источник добавлен как ответы на code-aware discovery о first save внутри `EditVersion`. Это принятый design/architecture input с рекомендуемой моделью, а не direct user interview или independently verified vendor research. Он уточняет предыдущий first-save contract и закрывает вопросы о geometry intent, baseline, aggregate boundary, AOI, concurrency, idempotency, событиях и stop-line.

## Сводка

- `UpdateEditVersionFeatureGeometry` принимает full resulting geometry; diff вычисляется относительно immutable baseline внутри `EditVersion`.
- First slice разрешает изменение одной существующей line feature во всей версии и сдвиг ровно одной внутренней вершины.
- Endpoints, остальные координаты, vertex/part count, identity, attributes и associations заморожены; comparison выполняется после нормализации к dataset precision/grid.
- Workspace visibility и write eligibility различаются: показывать можно features, пересекающие AOI, а сохранять - только line, целиком `covered by` AOI; boundary допустима.
- Hard invariant failure отклоняет save атомарно. Persisted blocked draft для invalid/prohibited geometry не создается.
- `basicValidation` использует статусы `passed` / `failed` / `not_checked`; после first save `topologyChecked=not_checked`.
- `DraftVersionToken` является opaque strong validator всего aggregate и меняется только на content-changing mutation. Read, refresh, `lastOpenedAt`, no-op save и idempotent retry token не меняют.
- `CommandId` обязателен: тот же id с тем же payload возвращает idempotent success, а reuse для другого payload отклоняется.
- Stale token отклоняет mutation и возвращает актуальные persisted object и token.
- `EditVersionChangeSetPersisted` возникает на каждый content-changing save с непустым diff; revert к baseline создает `EditVersionChangeSetCleared`; no-op/retry событий не создают.
- Command response и отдельный durable readback должны показать одинаковые `updatedFeature`, token, `operation`, `hasPersistedChangeSet` и `basicValidation`.
- First save не меняет lifecycle: `EditVersion` остается `open`, `WorkOrder` - `open/in_progress`; достигнутое состояние называется `persisted-draft-ready`, а не review-ready.

## Обновления Модели

- [[../../Wiki/commands/update_edit_version_feature_geometry]] - full-geometry intent, exact guard, atomic failure, response/readback/revert.
- [[../../Wiki/value_objects/draft_version_token]] и [[../../Wiki/value_objects/command_id]] - разделение optimistic concurrency и idempotent retry.
- [[../../Wiki/domain_events/edit_version_change_set_persisted]] и [[../../Wiki/domain_events/edit_version_change_set_cleared]] - event cadence для save/revert.
- [[../../Wiki/specifications/edit_version_basic_draft_validation]] и [[../../Wiki/specifications/edit_version_has_persisted_change_set]] - validation vocabulary и persisted proof.
- [[../../Wiki/value_objects/aoi]] - различие visibility и edit eligibility, `CoveredBy` с допустимой boundary.
- [[../../Wiki/conflicts/2026-07-25-edit-version-event-cadence]] - разрешено противоречие с прежним event-only-on-first-transition contract.
- [[../../DDD_Wiki/aggregates/edit_version]], [[../../DDD_Wiki/invariants/edit_version_persisted_edit_invariants]] и [[../../DDD_Wiki/state_machines/edit_version_persisted_change_set]] - consistency boundary, hard invariants и state machine.
- [[../../DDD_Wiki/use_cases/utility_editor_workflow]] и [[../../DDD_Wiki/model_health]] - acceptance path и актуальные planning/discovery queues.

## Конфликты

Разрешен один конфликт: прежняя модель эмитила `EditVersionChangeSetPersisted` только при `unchanged -> updated`; текущая модель эмитит его на каждый content-changing save с непустым diff и отделяет revert через `EditVersionChangeSetCleared`.

## Follow-ups

Для implementation остаются четыре неблокирующих выбора: dataset precision/grid, retention и payload fingerprint `CommandId`, mapping `networkVersion` / `BaselineRevisionRef`, а также минимальное event evidence (`geometryHash`, `bbox` или оба).
