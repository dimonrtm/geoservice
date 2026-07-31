---
title: Позиционная Приёмка И Безопасный Повтор First Save
type: source-summary
status: active
created: 2026-07-31
updated: 2026-07-31
source: RAW_inputs/meetings/demo_utility_gis.md
tags: [source-summary, edit-version, positional-accuracy, precision, idempotency]
---

# Позиционная Приёмка И Безопасный Повтор First Save

## Контекст

Источник добавлен как экспертный design/research answer о позиционной приёмке, spatial-reference metadata, выборе demo geometry и безопасном повторе save. Это не утверждённая спецификация продукта данных, не direct user interview и не независимая проверка внешних ссылок. Проектные правила перенесены в planned модель; предложенные числовые значения не приняты как фактическая конфигурация demo dataset.

## Ключевые Решения

- Позиционная приёмка и технический save разделены. При отсутствии утверждённой спецификации или independent evidence first save может создать working draft со статусом `POSITIONAL_ACCURACY_UNVERIFIED`, но такой draft нельзя передать на review/completion/post.
- `XY resolution`, `XY tolerance`, display precision и величина перемещения не являются допуском позиционной приёмки.
- Для существующих объектов source of truth по положению — валидированное полевое/геодезическое измерение, утверждённая исполнительная съёмка или проверенные данные обследования. Утверждённый проект применим к planned object; basemap и текущая GIS geometry недостаточны как independent evidence.
- Storage grid берётся из metadata фактического сохраняющего dataset: CRS, units, `xyResolution`, `xyTolerance`, origin/domain и transformations. Planned save выполняет server-side canonicalization, а client отображает возвращённую persisted geometry.
- Demo move должен затрагивать одну internal shape vertex простой singlepart line, не являющуюся endpoint, junction, device, tap, terminal или attachment point, и не менять структуру линии.
- `saveId` сопоставлен с существующим [[../../Wiki/value_objects/command_id]], чтобы не создавать второе понятие. Одинаковый id и fingerprint относятся к одной operation; concurrent retry получает тот же pending/terminal outcome.
- Idempotency registry живёт весь lifecycle `EditVersion`, переживает reconnect/relogin/device switch и запоминает domain rejection. После закрытия версии старый request отклоняется, а не становится новым intent.
- Операционный registry отделён от immutable save-operation history; точный records-retention срок последней остаётся открытым.

## Обновления Модели

- [[../../Wiki/policies/positional_accuracy_acceptance_policy]] задаёт границу technical save и downstream acceptance.
- [[../../Wiki/glossary/positional_accuracy_for_acceptance]] и [[../../Wiki/glossary/coordinate_storage_precision]] уточняют источники требований и metadata.
- [[../../Wiki/policies/edit_geometry_precision_policy]] фиксирует server-side canonicalization и deterministic midpoint rounding planned contract.
- [[../../Wiki/value_objects/command_id]] и [[../../DDD_Wiki/state_machines/edit_version_save_request]] задают lifecycle безопасного повтора.
- [[../../Wiki/specifications/edit_version_basic_draft_validation]] и [[../../Wiki/specifications/edit_version_ready_for_review]] разделяют технические hard guards и positional acceptance blocker.

## Конфликты

Активного model conflict не обнаружено. Источник уточняет planned first-save contract, но прямо подтверждает отсутствие фактической demo specification, spatial metadata и готовой editable fixture.

## Открытые Вопросы

- Как называются утверждённая спецификация продукта данных, её версия, scope и числовой positional tolerance?
- Каковы фактические CRS, units, `xyResolution`, `xyTolerance`, origin/domain и transformations сохраняющего demo dataset?
- Какая текущая demo line имеет eligible внутреннюю shape vertex и какие before/after coordinates образуют fixture?
- Какой records policy задаёт долгосрочный срок immutable save-operation history?
