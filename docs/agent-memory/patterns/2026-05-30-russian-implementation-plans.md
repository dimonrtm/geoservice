# Планы Реализации На Русском Языке

Date: 2026-05-30
Type: pattern
Tags: planning, superpowers, language, documentation
Related files:

- `docs/superpowers/plans/2026-05-30-project-knowledge-wiki-pipeline.md`
- `docs/agent-memory/protocol.md`

## Summary

Implementation plans в `docs/superpowers/plans/` должны писаться на русском языке. Пути, команды, имена файлов, API, типы, идентификаторы, названия пакетов и код не переводятся.

## Context

Пользователь явно уточнил это правило после подготовки плана `2026-05-30-project-knowledge-wiki-pipeline.md`. Это устойчивое предпочтение для будущих планов, а не разовая правка конкретного файла.

Ранее в `docs/agent-memory/protocol.md` уже было общее правило: human-facing fields обычно пишутся на основном языке чата, в этом репозитории обычно на русском. Но отдельной записи, которую будущий агент найдет по запросу про планы, не было.

## Actions

- 2026-05-30: План `docs/superpowers/plans/2026-05-30-project-knowledge-wiki-pipeline.md` переведен на русский язык.
- 2026-05-30: Зафиксировано правило, что будущие implementation plans должны быть на русском языке.
- 2026-05-30: Root cause того, что правило не было записано сразу: процессный пропуск memory write после durable user preference. Технического блокера не было; `docs/agent-memory/` доступна для записи.

## Verification

Проверено поиском:

```powershell
rg -n "план|plans|русск|язык|implementation plan|writing-plans" docs/agent-memory docs/superpowers -g "*.md"
```

До этой записи отдельного memory pattern про язык implementation plans не было; были только общее правило протокола и текст текущего плана.

## Retrieval Hints

планы на русском, implementation plans, writing-plans, русский язык, язык планов, docs/superpowers/plans, planning language, superpowers plans
