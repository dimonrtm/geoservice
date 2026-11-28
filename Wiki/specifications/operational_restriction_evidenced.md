---
title: "Эксплуатационное ограничение установлено"
type: specification
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, utility-gis, field-evidence]
confidence: inferred
related: [Wiki/entities/network_feature, DDD_Wiki/integration_patterns/asset_status_reconciliation]
---

# Эксплуатационное ограничение установлено

## Predicate

Для опознанного актива установлены ограничение, отказ или вывод, затронутая часть, время и источник. Чтобы исключить насос из действующей сети постоянно, нужны подтверждение эксплуатации о выводе либо проверенное фактическое отключение с установленными характером и датой. Временное отключение учитывается на срок его действия.

## Failure Meaning

Дефект с датой и местом остаётся результатом осмотра и передаётся эксплуатации для оценки. Списание требует сверки. Если характер отключения установить нельзя, доступность остаётся неопределённой. Находящийся на месте насос сохраняет физическую запись и историю.

Основание — решения условной организации через `expert_repson`. [NET-08](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-08) · [NET-16](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-16).
