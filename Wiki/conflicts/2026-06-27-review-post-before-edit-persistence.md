---
title: Review/Post Before Edit Persistence
type: conflict
status: resolved
created: 2026-06-27
updated: 2026-06-27
source: RAW_inputs/meetings/increment_after_open_workspace.md
tags: [domain-knowledge, conflict, sprint-planning, review, edit-version]
confidence: high
related: [DDD_Wiki/model_health, DDD_Wiki/use_cases/utility_editor_workflow, Wiki/commands/update_edit_version_feature, Wiki/commands/submit_for_review]
---

# Review/Post Before Edit Persistence

## Conflict

После integrated review/post ingest модель планирования склонялась к тому, что ближайший sprint сразу создает `submit_for_review` и `ReviewPackage`. Новый source уточняет, что это преждевременно: в текущем коде workspace уже открывается, но write path и persisted change set еще отсутствуют.

## Blocks

14-дневное sprint planning может уйти в review/post UI и статусы, которые выглядят убедительно, но стоят на пустом основании без сохраненного изменения в `EditVersion`.

## Resolution

Ближайший вертикальный срез должен идти так: workspace -> update existing feature in named/edit version -> persist `operation=updated` -> readback diff -> draft validation flags. `ReviewPackage`, reviewer decision, `can_post`, simulated post, full audit, trace/subnetwork evidence, automated risk tiers, reviewer queue и association mutation откладываются до появления persisted change set.

## Consequences

- `SubmitForReview` остается planned downstream command.
- `ReviewPackage v0.1` строится как materialized snapshot поверх persisted `edit_version_features` с backrefs на исходные rows.
- Новые durable review states пока не добавляются; readiness выражается computed predicates.
- Smoke path расширяется сначала до edit-save-readback, а не до submit mock.
