---
title: Edit Version Persisted Edit Invariants
type: invariant
status: active
created: 2026-06-28
updated: 2026-06-29
source: "RAW_inputs/meetings/persisted_edit_slice_EditVersion.md; RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md"
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
- Endpoints, `NetworkAssociation`, create/delete и attributes не меняются.
- Resulting geometry валидна.
- Изменение проходит AOI policy.
- `DraftVersionToken` совпадает с текущим draft state.
- `operation` отражает текущий diff относительно baseline и может нормализоваться обратно в `unchanged`.
- Readback возвращает persisted draft object и explicit baseline diff, а не только operation summary.
- Authoritative `Default` не меняется.

## Deferred Invariants

Topology validation, subnetwork cleanliness, reconcile against newer `Default`, review evidence, `can_post` и authoritative post проверяются downstream и не входят в first persisted edit slice.
