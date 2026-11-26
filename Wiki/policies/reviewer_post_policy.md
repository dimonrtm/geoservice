---
title: Reviewer Post Policy
type: policy
status: active
created: 2026-06-24
updated: 2026-11-24
source: "Vision_wiki/decisions/release_2_conflict_explanation.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md; RAW_inputs/meetings/ic_review_package_and_simulated_post.md; RAW_inputs/documents/2026-11-24-field-records-answers.md"
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

## Независимость оценки и возражение к одобренному пакету

Назначенный Reviewer раскрывает свой вклад. Если он создал или заверил единственное доказательство, от которого зависит обязательный вывод, другой компетентный специалист независимо проверяет этот вывод по доступному исходному материалу либо получает равносильное независимое свидетельство. До этого одобрение удерживают. Сбор общих сведений или техническая передача файла сами по себе не создают отвода. Проверка сохраняет имя, область, метод и исход. Роли Reviewer и Publisher сохраняют прежние обязанности. [[RAW_inputs/documents/2026-11-24-field-records-answers#DISC-2026-11-24-11]].

Возражение принимает координатор review с указанием автора, пакета, критерия, оспариваемого вывода и последствий. Регистрация сохраняет исходное одобрение. Как только установлено, что возражение относится к обязательному условию именно этого пакета и может изменить допуск, ответственный за review фиксирует удержание до независимого рассмотрения. Если это уже видно при поступлении, удержание ставят сразу. На границе post проверяют действующие удержания и статус попытки. После решения требуется свежая проверка допуска. Для уже состоявшегося post действует коррекция выпущенного результата. [[RAW_inputs/documents/2026-11-24-field-records-answers#DISC-2026-11-24-12]].

Матрица уровня риска продолжает определять штатный маршрут. Вторая проверка нужна для конкретного решающего свидетельства, когда специалист оценивает собственное заверение. Удержание перед допуском конкретной попытки описано в [[Wiki/specifications/post_allowed]].
