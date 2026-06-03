# F3 Alternatives Raw Ingest

Date: 2026-06-03
Type: session
Tags: wiki, ingest, phase-f3, alternatives, utility-network
Related files:

- `RAW_inputs/documents/03.06.2026deep-research-report.md`
- `Vision_wiki/chats/2026-06-03-phase-f3-alternatives.md`
- `Vision_wiki/entities/competitors/collaborative_editing_alternatives.md`
- `Vision_wiki/concepts/lean_canvas.md`
- `Vision_wiki/concepts/product_vision_board.md`
- `Vision_wiki/decisions/risk_assumption_log.md`
- `Vision_wiki/decisions/followups/index.md`
- `memory/project-state.md`

## Summary

Обработан новый RAW source Ф3 `RAW_inputs/documents/03.06.2026deep-research-report.md`. Ф3 сравнила альтернативы для `Utility GIS editor`: baseline - `ArcGIS Enterprise + Utility Network`, а наиболее реалистичная niche GeoService - focused conflict/review explainability layer.

## Context

Источник переоценивает альтернативы из `Ф2.md` относительно chain `edit -> reconcile -> review -> post -> authoritative state`. Полноценную GIS-платформу уже закрывает ArcGIS Enterprise; GeoService не должен автоматически расширяться до замены mature system of record.

## Actions

- 2026-06-03: Создана summary-нода `Vision_wiki/chats/2026-06-03-phase-f3-alternatives.md`.
- 2026-06-03: Обновлены alternatives, Lean Canvas, Product Vision Board, Risk And Assumption Log и follow-up queue.
- 2026-06-03: `FU-2026-05-31-001` закрыт как Ф1-Ф3 research completion; `FU-2026-06-01-002`, `FU-2026-06-01-003` и `FU-2026-06-02-001` уточнены.

## Verification

Проверено через bundled Python/runtime:

- `python scripts/lint-wiki.py --root .`: ожидаемые `missing_frontmatter` для `RAW_inputs/documents/Ф2.md` и `RAW_inputs/documents/03.06.2026deep-research-report.md`; RAW sources не редактируются по правилам `/ingest`, конфликт зафиксирован в `FU-2026-06-01-004`.
- `python scripts/check-memory-needed.py --check`: passed.
- `git diff --check`: без ошибок.

## Retrieval Hints

Ф3 alternatives, Utility GIS editor, ArcGIS Enterprise baseline, Utility Network, branch versioning, geometry association conflict, dirty areas, conflict review, authoritative post, non-Esri URL follow-up
