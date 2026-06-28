---
title: Edit Version Aggregate
type: aggregate
status: active
created: 2026-06-24
updated: 2026-06-28
source: "docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md; Code_wiki/архитектура/data_model.md; RAW_inputs/meetings/increment_after_open_workspace.md; RAW_inputs/meetings/persisted_edit_slice_EditVersion.md"
tags: [domain-knowledge, ddd, aggregate]
confidence: high
related: [Wiki/entities/edit_version, Wiki/entities/network_feature, Wiki/entities/network_association, Wiki/commands/update_edit_version_feature_geometry, DDD_Wiki/invariants/edit_version_persisted_edit_invariants]
---

# Edit Version Aggregate

## Aggregate Root

`EditVersion` - root для изолированной рабочей копии features и associations.

## Consistency Boundary

Текущий реализованный slice трактует workspace как read-only после открытия. Следующий обязательный slice добавляет persistence для change set: geometry diff существующей line feature внутри open `EditVersion`, нормализацию `operation` от текущего diff к baseline, readback persisted feature + diff и basic draft validation flags. `ReviewPackage` и `submit_for_review` не должны появляться раньше persisted change set.

## Protected Invariants

- `baseNetworkRevision` неизменяем после создания.
- Workspace features фильтруются по `WorkOrder.scope.aoi`.
- Associations включаются только когда присутствуют оба endpoint features.
- Первая mutation сохраняет только geometry diff существующей line feature; create/delete, attributes, endpoint rewiring и association mutation откладываются до отдельных rule checks.
- `operation` является текущей проекцией diff относительно baseline и может вернуться в `unchanged`, если diff исчез.
- `DraftVersionToken` защищает first save от stale draft.
- Draft summary/evidence могут жить рядом с `EditVersion` до submit; durable review snapshot создается позже в `ReviewPackage`.
