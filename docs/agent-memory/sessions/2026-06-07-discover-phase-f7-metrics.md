# Discover Phase F7 Metrics

Date: 2026-06-07
Type: session
Tags: wiki, discover, phase-f7, metrics, risks
Related files:

- `Vision_wiki/chats/2026-06-07-phase-f7-metrics-and-risks.md`
- `Vision_wiki/concepts/metrics.md`
- `Vision_wiki/decisions/risk_assumption_log.md`
- `Vision_wiki/decisions/followups/index.md`
- `Vision_wiki/solution/nfr.md`
- `Vision_wiki/solution/roadmap.md`
- `memory/project-state.md`

## Summary

Ф7 определила измерительный контракт utility demo: North Star `Safe Authoritative Post Rate >=95%` на 200 started work orders, 7-дневное correction window и абсолютный veto для silent overwrite, пропущенного critical conflict и Critical/High review error.

## Context

Ф4-Ф6 определили workflow, rollout и NFR. Ф7 связала их с manual baseline, secondary metrics, обязательными P95 и минимальными экспериментами. Пять новых RAW sources закрыли ранее отложенные определения post-проблемы, baseline и risky assumptions.

## Actions

- 2026-06-07: Созданы Ф7 summary и `Vision_wiki/concepts/metrics.md`.
- 2026-06-07: RAL дополнен четырьмя assumptions и тремя risks.
- 2026-06-07: Roadmap получил порядок workflow, validation, conflict, baseline и product experiments.
- 2026-06-07: Follow-up queue дополнена measurement pipeline и manual baseline; UX/performance follow-up'ы получили точные gates.
- 2026-06-07: Выполнен `/ingest repository-change`; Ф7 добавлена в технический журнал как measurement contract, а не реализованная instrumentation.

## Verification

- `scripts/lint-wiki.py --root .`: только 11 ожидаемых `missing_frontmatter` для неизменяемых RAW Markdown sources.
- `scripts/check-memory-needed.py --check`: passed.
- `git diff --check`: passed.
- Follow-up count после Ф7: 9 open, 7 resolved.

## Retrieval Hints

Ф7, Safe Authoritative Post Rate, 200 work orders, 7 days, manual baseline, safety blockers, metrics, risk experiments
