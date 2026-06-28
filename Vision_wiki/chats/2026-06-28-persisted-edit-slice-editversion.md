---
title: Persisted Edit Slice Для EditVersion
type: session
status: active
created: 2026-06-28
updated: 2026-06-28
source: RAW_inputs/meetings/persisted_edit_slice_EditVersion.md
tags: [vision-wiki, source-summary, edit-version, persisted-edit]
---

# Persisted Edit Slice Для EditVersion

## Контекст Источника

Design/architecture input уточняет ответы discovery по первому persisted edit slice после открытия workspace. Источник не является direct user interview; он фиксирует рекомендуемую доменную семантику `EditVersion` для utility-network versioned editing.

## Главные Решения

- Первый persisted change определяется как сохраненный diff относительно baseline, а не как факт нажатия save.
- Ближайшая команда уточнена до [[../../Wiki/commands/update_edit_version_feature_geometry]]: first slice меняет только geometry существующей line feature.
- Generic [[../../Wiki/commands/update_edit_version_feature]] и [[../../Wiki/domain_events/edit_version_feature_updated]] сохранены как superseded для first slice.
- `operation=updated` является текущей проекцией diff относительно baseline и может вернуться в `unchanged`, если diff исчез.
- `networkVersion` в draft-сценарии трактуется как [[../../Wiki/value_objects/draft_version_token]], то есть optimistic concurrency token текущего draft state.
- Минимальный proof сохранения: persisted feature + diff относительно baseline; operation summary может быть convenience, но не единственным доказательством.
- Basic draft validation считается синхронно на save и отделена от full topology validation, reconcile, review и post.

## Обновленные Узлы

- [[../../Wiki/commands/update_edit_version_feature_geometry]]
- [[../../Wiki/domain_events/edit_version_change_set_persisted]]
- [[../../Wiki/specifications/edit_version_has_persisted_change_set]]
- [[../../Wiki/specifications/edit_version_basic_draft_validation]]
- [[../../Wiki/value_objects/draft_version_token]]
- [[../../DDD_Wiki/invariants/edit_version_persisted_edit_invariants]]
- [[../../DDD_Wiki/aggregates/edit_version]]
- [[../../DDD_Wiki/model_health]]

## Non-Goals

Create/delete feature, изменение attributes, endpoint rewiring, association mutation, topology trace, full topology QA, reconcile, submit for review, `ReviewPackage`, `can_post` и review conflict UI остаются вне scope first persisted edit slice.
