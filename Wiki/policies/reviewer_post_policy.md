---
title: Reviewer Post Policy
type: policy
status: active
created: 2026-06-24
updated: 2026-11-22
source: "Vision_wiki/decisions/release_2_conflict_explanation.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md; RAW_inputs/meetings/ic_review_package_and_simulated_post.md"
tags: [domain-knowledge, policy, review]
confidence: high
related: [Wiki/actors/reviewer, Wiki/value_objects/risk_tier, Wiki/specifications/post_allowed]
---

# Reviewer Post Policy

## Rule

`Reviewer` approves package content, а не один отдельный conflict item. `approve package` и техническое `can_post` - разные решения. В developer demo `Publisher` представлен system actor `post-gate`; он выполняет simulated post только после успешного computed pre-post check.

## Inputs

Risk tier, полнота evidence, validation/topology status, trace/subnetwork impact, work order/evidence, stale status и hard blockers.

## Decision Outcome

В v0.1 `Reviewer` может принять одно из четырех human decisions: `approve package`, `return for changes`, `request evidence`, `escalate`. `stale` является системным переходом состояния, а `block post` - вычисляемым результатом pre-post check.

## Risk Authority Matrix

- `Normal`: обязательного второго контроля нет.
- `High`: `Reviewer` принимает основное содержательное решение, если evidence полный.
- `Critical`: в developer demo завершается `escalated` как terminal non-goal; отдельный Specialist/Data Owner workflow не симулируется до real validation.

## Истечение назначения и проверка по выписке

Одобрение точного пакета сохраняет силу после обычного окончания назначения Reviewer, если в момент решения его полномочия, охват и основание были действительны. При допуске post снова проверяют действующие права исполнителя публикации, свежесть и обязательные условия [[Wiki/specifications/post_allowed]]. Если прежних полномочий не было, отзыв действует на дату решения или его область спорна, пакет удерживают до полномочной проверки. Исходное решение и причину пересмотра сохраняют. Одобрение другого пакета или изменившегося основания требует собственной проверки. [[RAW_inputs/research_results/2026-11-22-utility-gis-editor-governance-answers#DISC-2026-11-21-14]].

Заверенная выписка подтверждает перечисленные в ней утверждения в пределах объекта, периода и цели, если известны редакция оригинала, компетенция проверившего, метод, существенные точность и ограничения. Различают извлечение текста и самостоятельное заключение специалиста. Если скрыто существенное условие или уровень риска требует прямой проверки, запрашивают допустимое дополнение либо назначают Reviewer с доступом к оригиналу. Пробел в обязательном свидетельстве блокирует пакет. Например, подтверждение материала не подтверждает XY. [[RAW_inputs/research_results/2026-11-22-utility-gis-editor-governance-answers#DISC-2026-11-21-15]].
