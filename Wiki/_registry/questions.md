---
title: Questions Registry
type: index
status: active
created: 2026-06-24
updated: 2026-10-12
source: docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md
tags: [domain-knowledge, registry, question]
confidence: n/a
related: [Wiki/index, DDD_Wiki/model_health]
---

# Questions Registry

После research-ingest от 2026-10-11 после принятия правил 2026-10-12 открыты пять вопросов: четыре прежних организационных/фактических и назначение ответственного за исходные дефекты. Два вопроса принятия правил закрыты решением пользователя. Ответы на 15 discovery-вопросов сохранены в [[RAW_inputs/research_results/2026-10-11-utility-gis-editor-save-recovery-research]]; это синтез, не интервью. Для demo metadata и fixture появились технические источники: [[Code_wiki/архитектура/edit_geometry_determinism]] и [артефакты Sprint 2](../../docs/sprint_2/README.md). До следующего discovery требуется сверка по `FU-2026-10-11-001` в [[Vision_wiki/decisions/followups/index]]; прежние вопросы не следует повторять без проверки этих источников.

| Question | Domain Gap | Priority | Status | Answer Source |
| --- | --- | --- | --- | --- |
| Принять ли предложенную политику восстановления и отделение неизвестного исхода для редактора от operation state? | [[Wiki/conflicts/2026-10-11-save-outcome-observer-vs-operation]], [[Wiki/policies/editor_recovery_policy]] | high | answered | `docs/sprint_2/2026-10-12-save-recovery-rules-decision.md`: принято пользователем 2026-10-12 |
| Сделать ли временный запрет нулевых XY-сегментов постоянным правилом текущего среза? | [[Wiki/policies/geometry_quality_escalation_policy]] | high | answered | `docs/sprint_2/2026-10-12-save-recovery-rules-decision.md`: принято пользователем 2026-10-12 |
| Кто принимает дефекты исходной геометрии и как разрешает безопасное возобновление работы? | [[Wiki/policies/geometry_quality_escalation_policy]] | medium | open | Тот же research, ответ 2; роль ответственности предложена, реальный владелец не назначен |
| `Publisher` - отдельная роль, ответственность data owner или техническая операция? | [[Wiki/conflicts/2026-06-24-reviewer-vs-publisher]] | high | answered | `RAW_inputs/meetings/implementation_contract_for_review_and_post.md` |
| Какие правила Release 2 про устаревание и блокеры должны влиять на следующий 14-дневный спринт? | [[Wiki/conflicts/2026-06-24-release1-vs-release2-review-policy]] | high | answered | `RAW_inputs/meetings/implementation_contract_for_review_and_post.md` |
| Новый review/post contract должен обновлять legacy artifact или быть отдельным integrated artifact? | [[Wiki/conflicts/2026-06-26-legacy-contract-vs-integrated-flow]] | high | answered | user chat 2026-06-26 |
| Где должен заканчиваться ближайший review/post slice? | [[DDD_Wiki/use_cases/utility_editor_workflow]] | high | answered | `RAW_inputs/meetings/ic_review_package_and_simulated_post.md` |
| `can_post` должен быть persisted state или computed specification? | [[Wiki/specifications/post_allowed]] | high | answered | `RAW_inputs/meetings/ic_review_package_and_simulated_post.md` |
| Какой ближайший полноценный инкремент после открытия workspace? | [[Wiki/conflicts/2026-06-27-review-post-before-edit-persistence]] | high | answered | `RAW_inputs/meetings/increment_after_open_workspace.md` |
| Что должно предшествовать `ReviewPackage` в текущем кодовом flow? | [[Wiki/specifications/edit_version_has_persisted_change_set]] | high | answered | `RAW_inputs/meetings/increment_after_open_workspace.md` |
| Что считать первым persisted change в `EditVersion`? | [[Wiki/specifications/edit_version_has_persisted_change_set]] | high | answered | `RAW_inputs/meetings/persisted_edit_slice_EditVersion.md`; `RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md`; `RAW_inputs/meetings/first_save_edit_version.md` |
| Как должна называться первая команда сохранения feature change? | [[Wiki/commands/update_edit_version_feature_geometry]] | high | answered | `RAW_inputs/meetings/persisted_edit_slice_EditVersion.md`; `RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md`; `RAW_inputs/meetings/first_save_edit_version.md` |
| Какие инварианты и validation flags обязательны для first save? | [[DDD_Wiki/invariants/edit_version_persisted_edit_invariants]] | high | answered | `RAW_inputs/meetings/persisted_edit_slice_EditVersion.md`; `RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md`; `RAW_inputs/meetings/first_save_edit_version.md` |
| Где stop-line перед review/post после открытия workspace? | [[DDD_Wiki/use_cases/utility_editor_workflow]] | high | answered | `RAW_inputs/meetings/persisted_edit_slice_EditVersion.md`; `RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md`; `RAW_inputs/meetings/first_save_edit_version.md` |
| Что доказывает successful first save/readback? | [[Wiki/specifications/edit_version_has_persisted_change_set]] | high | answered | `RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md`; `RAW_inputs/meetings/first_save_edit_version.md` |
| Что означает `DraftVersionToken` / `networkVersion`? | [[Wiki/value_objects/draft_version_token]] | high | answered | `RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md`; `RAW_inputs/meetings/first_save_edit_version.md` |
| Должен ли explicit baseline diff быть обязательным minimum proof первого save? | [[Wiki/specifications/edit_version_has_persisted_change_set]] | high | answered | `RAW_inputs/meetings/first_save_edit_version.md` |
| Что хранить как source of truth для first save: full geometry snapshot или pure diff? | [[DDD_Wiki/aggregates/edit_version]] | high | answered | `RAW_inputs/meetings/first_save_edit_version.md` |
| Как отличать optimistic concurrency от idempotent retry в first save? | [[Wiki/value_objects/draft_version_token]] | medium | answered | `RAW_inputs/meetings/first_save_edit_version.md` |
| Должна ли команда выражать UI-операцию или full resulting geometry? | [[Wiki/commands/update_edit_version_feature_geometry]] | high | answered | `RAW_inputs/meetings/first_save_for_edit_version.md` |
| Сколько features и внутренних вершин может менять first-save slice? | [[DDD_Wiki/invariants/edit_version_persisted_edit_invariants]] | high | answered | `RAW_inputs/meetings/first_save_for_edit_version.md` |
| Как различаются workspace visibility и first-save edit eligibility? | [[Wiki/value_objects/aoi]] | high | answered | `RAW_inputs/meetings/first_save_for_edit_version.md` |
| Сохранять ли prohibited/invalid state как blocked draft? | [[Wiki/specifications/edit_version_basic_draft_validation]] | high | answered | `RAW_inputs/meetings/first_save_for_edit_version.md` |
| Когда меняется `DraftVersionToken` и что делает no-op save? | [[Wiki/value_objects/draft_version_token]] | high | answered | `RAW_inputs/meetings/first_save_for_edit_version.md` |
| Какова cadence событий для save, revert, no-op и retry? | [[Wiki/conflicts/2026-07-25-edit-version-event-cadence]] | high | answered | `RAW_inputs/meetings/first_save_for_edit_version.md` |
| Меняет ли first save lifecycle `EditVersion` / `WorkOrder`? | [[DDD_Wiki/use_cases/utility_editor_workflow]] | medium | answered | `RAW_inputs/meetings/first_save_for_edit_version.md` |
| Как называются утверждённая спецификация продукта данных, её версия, scope и числовой positional tolerance для demo? | [[Wiki/policies/positional_accuracy_acceptance_policy]] | high | open | `RAW_inputs/meetings/demo_utility_gis.md` (правило определено, утверждённый документ и значения отсутствуют) |
| Какие фактические CRS, coordinate unit, `xyResolution`, `xyTolerance`, origin/domain и transformations использует сохраняющий demo dataset? | [[Wiki/policies/edit_geometry_precision_policy]] | high | open | `RAW_inputs/meetings/demo_utility_gis.md` (читать из metadata actual dataset; предложенные числа не являются project fact) |
| Какая текущая demo line имеет eligible внутреннюю shape vertex и какие before/after coordinates использовать как fixture? | [[DDD_Wiki/invariants/edit_version_persisted_edit_invariants]] | high | open | `RAW_inputs/meetings/demo_utility_gis.md` (критерии выбора определены, фактический объект не указан) |
| Каков idempotency window и logical storage record `CommandId`? | [[Wiki/value_objects/command_id]] | medium | answered | `RAW_inputs/meetings/demo_utility_gis.md` (server-side operational registry на весь lifecycle `EditVersion`, отдельно от immutable operation history) |
| Какой records policy задаёт долгосрочный срок хранения immutable save-operation history после закрытия `EditVersion`? | [[Wiki/value_objects/command_id]] | medium | open | `RAW_inputs/meetings/demo_utility_gis.md` (граница registry/history определена, срок в годах не задан) |
| Переименовать `networkVersion` в `BaselineRevisionRef` или скрыть его за mapping? | [[Wiki/value_objects/draft_version_token]] | medium | answered | `RAW_inputs/meetings/tolerance_rules.md` |
| Какое минимальное event evidence выбрать: `geometryHash`, `bbox` или оба поля? | [[Wiki/domain_events/edit_version_change_set_persisted]] | low | answered | `RAW_inputs/meetings/tolerance_rules.md` |
