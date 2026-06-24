# Release 2: конфликт геометрии/ассоциации

Дата: 2026-06-23
Статус: черновой пакет артефактов
Расположение: `docs/release_2/geometry_association_conflict`

## Назначение

Папка содержит контракт реализации v0.1 и машиночитаемые приложения для
Release 2 по `geometry/association conflict`.

Release 2 рассматривается как слой поддержки решений (`decision support`) перед
`post` вокруг цепочки `reconcile -> consequence package -> review -> post`.
Он не заменяет штатный движок разрешения конфликтов (`conflict resolution engine`),
topology engine или production-процесс для `post`.

## Артефакты

- [Контракт реализации v0.1](2026-06-23-implementation-contract-v0.1.md)
- [Чеклист реальной проверки с Editor/Reviewer](real-editor-reviewer-validation-checklist.md)
- [Манифест фикстуры](appendices/fixture-manifest.yaml)
- [Датасет канонического сценария](appendices/canonical-scenario-dataset.yaml)
- [Снимки Base-Mine-Default](appendices/base-mine-default-snapshots.json)
- [Пример пакета доказательств](appendices/evidence-package.example.json)
- [Пример запуска решения](appendices/decision-run.example.json)
- [Схема пакета](appendices/schemas/package.schema.json)
- [Схема аудита](appendices/schemas/audit.schema.json)
- [Схема запуска](appendices/schemas/run.schema.json)
- [Схема метрик времени](appendices/schemas/timing.schema.json)

## Источники

- `RAW_inputs/meetings/geometry_association_conflict_f6.md`
- `RAW_inputs/meetings/geometry_association_conflict_f7.md`
- `RAW_inputs/meetings/geometry_association_conflict_f8.md`
- `Vision_wiki/decisions/release_2_conflict_explanation.md`
- `Vision_wiki/concepts/metrics.md`
- `Vision_wiki/solution/roadmap.md`

## Использование

1. Использовать контракт как источник истины (`source of truth`) для первого инженерного плана.
2. Использовать приложения как фикстуры и примеры схем для будущего demo harness.
3. Не использовать примеры как production-данные: ids, geometry и checksums
   являются синтетическими черновыми значениями для детерминированной demo.
4. Перед claims сильнее `helps explain/detect/block` пройти чеклист реальной
   проверки с `Editor`/`Reviewer`.
