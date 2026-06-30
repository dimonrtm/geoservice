---
title: Edit Version Aggregate
type: aggregate
status: active
created: 2026-06-24
updated: 2026-06-30
source: "docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md; Code_wiki/архитектура/data_model.md; RAW_inputs/meetings/increment_after_open_workspace.md; RAW_inputs/meetings/persisted_edit_slice_EditVersion.md; RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md; RAW_inputs/meetings/first_save_edit_version.md"
tags: [domain-knowledge, ddd, aggregate]
confidence: high
related: [Wiki/entities/edit_version, Wiki/entities/network_feature, Wiki/entities/network_association, Wiki/commands/update_edit_version_feature_geometry, DDD_Wiki/invariants/edit_version_persisted_edit_invariants]
---

# Edit Version Aggregate

## Aggregate Root

`EditVersion` - root для изолированной рабочей копии features и associations.

## Consistency Boundary

Текущий реализованный slice трактует workspace как read-only после открытия. Следующий обязательный slice добавляет persistence для change set: geometry-only изменение существующей line feature внутри open `EditVersion`, full resulting geometry snapshot как current draft state, computed diff относительно baseline, нормализацию `operation` от текущего diff к baseline, readback resulting feature + новый `DraftVersionToken` + validation summary. `ReviewPackage` и `submit_for_review` не должны появляться раньше persisted change set.

## Protected Invariants

- `baseNetworkRevision` неизменяем после создания.
- Workspace features фильтруются по `WorkOrder.scope.aoi`.
- Associations включаются только когда присутствуют оба endpoint features.
- Первая mutation сохраняет только geometry-only изменение существующей line feature: разрешен сдвиг внутренних вершин, но запрещены endpoint move, vertex insert/delete, split/merge, `part count` change, create/delete, attributes и association mutation.
- `operation` является текущей проекцией diff относительно baseline и может вернуться в `unchanged`, если diff исчез.
- `DraftVersionToken` является version всего агрегата `EditVersion` и защищает first save от stale draft; idempotent retry требует отдельный `CommandId`.
- Draft summary/evidence могут жить рядом с `EditVersion` до submit; durable review snapshot создается позже в `ReviewPackage`.
