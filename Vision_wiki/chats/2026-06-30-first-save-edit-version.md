---
title: First Save EditVersion
type: source-summary
status: active
created: 2026-06-30
updated: 2026-06-30
source: RAW_inputs/meetings/first_save_edit_version.md
tags: [source-summary, edit-version, first-save, ddd]
---

# First Save EditVersion

## Контекст

Источник уточняет доменную модель первого сохранения внутри `EditVersion` для utility-network versioned editing. Это design/architecture input, а не direct user interview: он закрепляет рекомендуемую границу ближайшего slice перед review/post.

## Сводка

- Первый slice должен сохранять локальный, изолированный persisted change set внутри open `EditVersion`, а не смешивать save с review, reconcile, post, full topology validation или conflict resolution.
- Минимальный persisted change set для первого slice - geometry-only изменение существующей line feature относительно baseline `EditVersion`.
- Первая допустимая mutation сужена до сдвига одной или нескольких внутренних вершин существующей polyline без изменения start/end vertices, `part count` и vertex identity; split/merge, insert/delete vertex, endpoint move и association semantics остаются hard blockers.
- Source of truth в persistence - baseline snapshot + full resulting geometry snapshot. Diff должен быть производным артефактом, вычисляемым для readback/review, а не единственной persisted формой.
- `operation=updated` означает текущее отличие persisted state от baseline. Revert к baseline должен возвращать `operation=unchanged`, `hasPersistedChangeSet=false` и `dirtyRelativeToBaseline=false`.
- AOI rule для first slice блокирующая: линия должна целиком оставаться внутри AOI, а не просто пересекать ее.
- Basic validation считается синхронно при save: `geometryValid`, `insideAoi`, `associationsUnchanged`, `topologyNotChecked`, `dirtyRelativeToBaseline`.
- Минимальный readback после save: resulting feature, новый `DraftVersionToken`, `operation` / `hasPersistedChangeSet` и validation summary. Explicit diff полезен позже, но не является обязательным minimum proof.
- `DraftVersionToken` - opaque version всего агрегата `EditVersion`; он меняется после любой успешной persisted мутации. Idempotent retry должен решаться отдельным `CommandId` / idempotency key, а не переиспользованием stale token.
- На first save не нужно проверять свежесть live `Default` как hard requirement; это downstream concern для reconcile/review/post.
- `EditVersionChangeSetPersisted` возникает при переходе `unchanged -> updated`; будущий `EditVersionChangeSetCleared` может фиксировать переход `updated -> unchanged`. Identical retry не должен создавать событие.

## Обновления Модели

- [[../../Wiki/commands/update_edit_version_feature_geometry]] - command scope, hard blockers, readback contract и persistence shape.
- [[../../Wiki/specifications/edit_version_has_persisted_change_set]] - state-based predicate и minimum proof без обязательного explicit diff.
- [[../../Wiki/specifications/edit_version_basic_draft_validation]] - synchronous cheap validation и AOI containment.
- [[../../Wiki/value_objects/draft_version_token]] - aggregate-level concurrency token и разделение optimistic concurrency/idempotency.
- [[../../Wiki/domain_events/edit_version_change_set_persisted]] - event boundary for first non-empty change set.
- [[../../DDD_Wiki/aggregates/edit_version]] и [[../../DDD_Wiki/invariants/edit_version_persisted_edit_invariants]] - aggregate boundary, snapshot-vs-diff и first-save invariants.
- [[../../DDD_Wiki/model_health]] - ближайший sprint/discovery queue уточнен вокруг resulting feature + token + flags.

## Follow-ups

Новый blocking conflict не возник. Источник уточняет прежнее требование explicit baseline diff: diff остается полезной производной для readback/review, но minimum proof первого save теперь state-based - resulting feature snapshot + `hasPersistedChangeSet` + validation flags.
