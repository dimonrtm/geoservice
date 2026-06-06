# Utility Target Times RAW Ingest

Date: 2026-06-06
Type: session
Tags: wiki, ingest, performance, nfr, utility-gis-editor
Related files:

- `RAW_inputs/documents/utility_gis_editor_target_times.md`
- `RAW_inputs/index.md`
- `Vision_wiki/chats/2026-06-06-utility-gis-editor-target-times.md`
- `Vision_wiki/solution/nfr.md`
- `Vision_wiki/decisions/risk_assumption_log.md`
- `Vision_wiki/decisions/followups/index.md`
- `memory/project-state.md`

## Summary

Обработан новый RAW source с draft P95 acceptance targets для пользовательского контура `Utility GIS editor`. Пороги внесены в NFR как рабочие цели, а не как уже доказанная производительность.

## Context

Ф6 не задала точные latency targets. Новый source заполнил этот пробел для малого `synthetic_utility_feeder_01`, но достижимость порогов еще нужно подтвердить repeatable benchmark в Chrome на reference hardware.

## Actions

- 2026-06-06: Создана source summary-нода с P95 targets и семантикой измерений.
- 2026-06-06: Обновлены NFR, Risk And Assumption Log, follow-up queue, индексы и live state.
- 2026-06-06: Добавлен `FU-2026-06-06-001` для benchmark P50/P95.
- 2026-06-06: Известный RAW frontmatter conflict расширен до пяти Markdown sources.

## Verification

Проверить `python scripts/lint-wiki.py --root .`, `python scripts/check-memory-needed.py --check` и `git diff --check`.

## Retrieval Hints

utility target times, P95, performance NFR, benchmark, map load, validation, reconcile, post, synthetic_utility_feeder_01
