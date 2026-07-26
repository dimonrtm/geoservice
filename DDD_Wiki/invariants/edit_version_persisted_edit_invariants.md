---
title: Edit Version Persisted Edit Invariants
type: invariant
status: active
created: 2026-06-28
updated: 2026-07-26
source: "RAW_inputs/meetings/persisted_edit_slice_EditVersion.md; RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md; RAW_inputs/meetings/first_save_edit_version.md; RAW_inputs/meetings/first_save_for_edit_version.md; RAW_inputs/meetings/tolerance_rules.md"
tags: [domain-knowledge, ddd, invariant, edit-version]
confidence: high
related: [Wiki/entities/edit_version, Wiki/glossary/base_work_state, Wiki/glossary/coordinate_storage_precision, Wiki/policies/edit_geometry_precision_policy, Wiki/commands/update_edit_version_feature_geometry, Wiki/specifications/edit_version_has_persisted_change_set, Wiki/specifications/edit_version_basic_draft_validation]
---

# Edit Version Persisted Edit Invariants

## Must Hold On First Save

- `Editor` назначен на `WorkOrder`.
- `EditVersion` имеет статус `open`.
- Target feature существует в baseline этой `EditVersion`.
- First slice меняет geometry только одной существующей line feature во всей версии.
- Непустой diff разрешает сдвиг ровно одной внутренней вершины, идентифицированной индексом в immutable baseline coordinate array; нулевой diff допустим только как baseline/no-op state.
- Позиционная точность для приёмки берётся из спецификации задания/продукта данных, а coordinate normalization — из настроек слоя/БД; эти правила не взаимозаменяемы.
- Перед сравнением изменённая вершина детерминированно канонизируется к dataset precision/grid. Start/end vertices, остальные coordinates, `part count`, vertex identity, vertex count, `NetworkAssociation`, create/delete, split/merge и attributes не меняются.
- Full-line renormalization и shared-node/topological editing не являются побочным эффектом обычного save и остаются отдельными операциями.
- Resulting line geometry валидна и проста.
- Resulting geometry целиком `covered by` AOI; касание boundary допустимо.
- `DraftVersionToken` совпадает с текущей версией агрегата `EditVersion`.
- `CommandId` обязателен; одинаковый id нельзя переиспользовать для другого payload.
- `operation` отражает текущий diff относительно baseline и может нормализоваться обратно в `unchanged`.
- Readback возвращает resulting feature snapshot, новый `DraftVersionToken`, `operation` / `hasPersistedChangeSet` и validation summary; explicit baseline diff является полезной производной, но не обязательным minimum proof.
- Если канонический результат совпал с текущим persisted state, save является no-op, не меняет token и не создаёт событие.
- Stale token и нарушение hard invariants не меняют aggregate; stale response возвращает актуальные persisted object и token.
- Authoritative `Default` не меняется.
- Freshness live `Default` не проверяется как hard requirement first save.

## Deferred Invariants

Topology validation, subnetwork cleanliness, full association-row diff, explicit review diff summary, reconcile against newer `Default`, review evidence, `can_post` и authoritative post проверяются downstream и не входят в first persisted edit slice.
