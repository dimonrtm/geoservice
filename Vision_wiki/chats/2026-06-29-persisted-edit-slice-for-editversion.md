---
title: Persisted Edit Slice For EditVersion
type: source-summary
status: active
created: 2026-06-29
updated: 2026-06-29
source: RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md
tags: [source-summary, edit-version, persisted-edit, ddd]
---

# Persisted Edit Slice For EditVersion

## Контекст

Источник уточняет ближайший code-aware инкремент после открытия workspace: сначала нужно доказать persisted edit slice в текущем `WorkOrder` / `EditVersion` flow, а review/post оставлять downstream до появления устойчивого change set.

## Сводка

- Первый persisted edit slice - saved geometry diff существующей line feature относительно baseline внутри open `EditVersion`.
- Команда должна называться `UpdateEditVersionFeatureGeometry`, потому что первый slice сознательно не является generic update для любых feature changes.
- Разрешенная первая mutation: geometry существующей линии, предпочтительно сдвиг внутренней вершины. Points/devices/junctions, attributes, create/delete, endpoint rewiring и `NetworkAssociation` mutation остаются вне scope.
- `operation=updated` означает текущий persisted diff относительно baseline, а не факт прошлого save. Если feature вернули к baseline, projection должна нормализоваться к `unchanged`; историю хранит audit/event stream.
- Доказательство successful first save - readback persisted object вместе с explicit baseline diff. Operation summary является удобной производной, но не единственным доказательством.
- Basic draft validation после save синхронно проверяет `geometryValid`, `aoiOk`, `associationsUnchanged`, `topologyNotChecked`, `dirtyRelativeToBaseline` и optional `concurrencyOk`.
- Full topology validation, reconcile, review/post, `can_post`, partial post, reviewer UI, trace/subnetwork и conflict analysis остаются deferred.
- `DraftVersionToken` / `networkVersion` - concurrency token текущего draft state. Он не является `baseNetworkRevision`, не доказывает свежесть authoritative `Default` и не заменяет reconcile/post freshness checks.
- `EditVersionChangeSetPersisted` эмитится только для ненулевого persisted diff. Если diff нормализован к пустому, source рекомендует не эмитить это событие.

## Обновления Модели

- [[../../Wiki/commands/update_edit_version_feature_geometry]] - first write command.
- [[../../Wiki/specifications/edit_version_has_persisted_change_set]] - predicate persisted change set и readback proof.
- [[../../Wiki/specifications/edit_version_basic_draft_validation]] - synchronous draft validation flags.
- [[../../Wiki/value_objects/draft_version_token]] - concurrency semantics.
- [[../../Wiki/domain_events/edit_version_change_set_persisted]] - event boundary.
- [[../../DDD_Wiki/aggregates/edit_version]] и [[../../DDD_Wiki/invariants/edit_version_persisted_edit_invariants]] - aggregate boundary и first-save invariants.

## Follow-ups

Новый blocking conflict не возник. Внешние vendor/API ссылки внутри RAW source остаются source-level background и требуют обычной research verification перед публичными claims; ближайший implementation scope выводится из доменной модели, а не из vendor due diligence.
