---
title: Edit Version Persisted Edit Invariants
type: invariant
status: active
created: 2026-06-28
updated: 2026-06-30
source: "RAW_inputs/meetings/persisted_edit_slice_EditVersion.md; RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md; RAW_inputs/meetings/first_save_edit_version.md"
tags: [domain-knowledge, ddd, invariant, edit-version]
confidence: high
related: [Wiki/entities/edit_version, Wiki/commands/update_edit_version_feature_geometry, Wiki/specifications/edit_version_has_persisted_change_set, Wiki/specifications/edit_version_basic_draft_validation]
---

# Edit Version Persisted Edit Invariants

## Must Hold On First Save

- `Editor` назначен на `WorkOrder`.
- `EditVersion` имеет статус `open`.
- Target feature существует в baseline этой `EditVersion`.
- First slice меняет только geometry существующей линии.
- Разрешен только сдвиг внутренних вершин; start/end vertices, `part count`, vertex identity, vertex count, `NetworkAssociation`, create/delete, split/merge и attributes не меняются.
- Resulting geometry валидна.
- Resulting geometry целиком остается внутри AOI.
- `DraftVersionToken` совпадает с текущей версией агрегата `EditVersion`.
- `operation` отражает текущий diff относительно baseline и может нормализоваться обратно в `unchanged`.
- Readback возвращает resulting feature snapshot, новый `DraftVersionToken`, `operation` / `hasPersistedChangeSet` и validation summary; explicit baseline diff является полезной производной, но не обязательным minimum proof.
- Authoritative `Default` не меняется.
- Freshness live `Default` не проверяется как hard requirement first save.

## Deferred Invariants

Topology validation, subnetwork cleanliness, association-row diff, explicit review diff summary, reconcile against newer `Default`, review evidence, `can_post`, idempotency через `CommandId` и authoritative post проверяются downstream и не входят в first persisted edit slice.
