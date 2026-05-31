# Discover Phase F1 Research Goals

Date: 2026-05-31
Type: session
Tags: wiki, discover, phase-f1, research, collaborative-editing
Related files:

- `Vision_wiki/chats/2026-05-31-phase-f1-why-now.md`
- `Vision_wiki/concepts/about_project.md`
- `Vision_wiki/concepts/product_vision_board.md`
- `Vision_wiki/concepts/lean_canvas.md`
- `Vision_wiki/decisions/risk_assumption_log.md`
- `Vision_wiki/decisions/followups/index.md`
- `memory/project-state.md`

## Summary

Фаза Ф1 установила: GeoService появился как исследовательский pet-проект для изучения алгоритмов совместного редактирования геометрии, когда похожая реализация планировалась на работе. Дополнительная цель - проверить AI-first разработку сложной геоинформационной системы.

## Context

Нельзя считать GeoService подтвержденным продуктовым решением или приписывать ему внешнюю пользовательскую боль. На Ф1 подтверждены исследовательская мотивация, demo/portfolio-направление и потенциальное применение в реальной работе. Пользовательская ценность за пределами автора проекта остается гипотезой до Ф2-Ф3.

## Actions

- 2026-05-31: Созданы сводка Ф1, draft Product Vision Board, draft Lean Canvas и Risk And Assumption Log.
- 2026-05-31: В follow-up очередь добавлена необходимость разложить критерий "все типа работает" на demo-script и acceptance criteria.
- 2026-05-31: Следующие discovery-фазы: Ф2 пользователи и боль, Ф3 альтернативы и контекст использования.

## Verification

`python scripts/lint-wiki.py --root .` через bundled Python -> `Wiki lint passed.`; `python -m unittest discover -s scripts\tests` -> 8 tests OK; `python scripts/check-memory-needed.py --check` -> passed; `git diff --check` -> без ошибок.

## Retrieval Hints

discover Ф1, why-now, research pet project, collaborative editing geometry, AI-first GIS, demo portfolio, acceptance criteria
