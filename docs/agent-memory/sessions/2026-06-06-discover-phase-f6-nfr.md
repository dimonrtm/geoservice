# Discover Phase F6 NFR

Date: 2026-06-06
Type: session
Tags: wiki, discover, phase-f6, nfr, audit, local-demo
Related files:

- `Vision_wiki/chats/2026-06-06-phase-f6-constraints-and-nfr.md`
- `Vision_wiki/solution/nfr.md`
- `Vision_wiki/decisions/constraints.md`
- `Vision_wiki/solution/architecture_vision.md`
- `Vision_wiki/decisions/risk_assumption_log.md`
- `Vision_wiki/decisions/followups/index.md`
- `memory/project-state.md`

## Summary

Выполнен `/discover --phase Ф6`. Для local Docker Compose demo зафиксированы reference hardware, Chrome, startup/reset за несколько минут, JWT, separation of duties для `Editor`/`Reviewer`, минимальная observability и двухрежимная модель reset/audit.

## Context

Ф5 определила local developer demo и оставила открытыми эксплуатационные рамки. Ф6 уточнила их без введения production SLA, backup/compliance требований или неподтвержденных latency targets.

## Actions

- 2026-06-06: Создана chat-нода Ф6 с ответами и решениями.
- 2026-06-06: Обновлены NFR, constraints, architecture vision, Risk And Assumption Log, follow-up queue, индексы и live state.
- 2026-06-06: Принято решение: обычный reset восстанавливает seed и сохраняет audit; отдельный `full-clean` удаляет demo data и audit.
- 2026-06-06: Подтверждено, что `import GeoJSON` входит в первый walking skeleton.

## Verification

Проверить `python scripts/lint-wiki.py --root .`, `python scripts/check-memory-needed.py --check` и `git diff --check`.

## Retrieval Hints

Ф6, NFR, Chrome, reference hardware, JWT, Editor Reviewer separation, audit persistence, reset, full-clean, observability, import GeoJSON
