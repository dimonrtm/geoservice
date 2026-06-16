# Планы И Спецификации На Русском Языке

Date: 2026-05-30
Type: pattern
Tags: planning, specs, superpowers, language, documentation
Related files:

- `docs/superpowers/plans/2026-05-30-project-knowledge-wiki-pipeline.md`
- `docs/superpowers/plans/`
- `docs/superpowers/specs/`
- `docs/agent-memory/protocol.md`

## Summary

Implementation plans в `docs/superpowers/plans/` и design specs в
`docs/superpowers/specs/` должны писаться на русском языке. Пути, команды, имена
файлов, API, типы, идентификаторы, названия пакетов и код не переводятся.

## Context

Пользователь явно уточнил это правило после подготовки плана
`2026-05-30-project-knowledge-wiki-pipeline.md`, а 2026-06-16 расширил его на
спецификации после подготовки refactor design/plan. Это устойчивое предпочтение
для будущих planning/spec artifacts, а не разовая правка конкретного файла.

Ранее в `docs/agent-memory/protocol.md` уже было общее правило: human-facing fields обычно пишутся на основном языке чата, в этом репозитории обычно на русском. Но отдельной записи, которую будущий агент найдет по запросу про планы, не было.

## Actions

- 2026-05-30: План `docs/superpowers/plans/2026-05-30-project-knowledge-wiki-pipeline.md` переведен на русский язык.
- 2026-05-30: Зафиксировано правило, что будущие implementation plans должны быть на русском языке.
- 2026-05-30: Root cause того, что правило не было записано сразу: процессный пропуск memory write после durable user preference. Технического блокера не было; `docs/agent-memory/` доступна для записи.
- 2026-06-16: Правило расширено: specs в `docs/superpowers/specs/` тоже должны
  писаться на русском языке, как и plans. Plan
  `docs/superpowers/plans/2026-06-16-utility-service-refactor-links.md`
  переведен на русский язык.

## Verification

Проверено поиском:

```powershell
rg -n "план|plans|specs|спецификац|русск|язык|implementation plan|design spec|writing-plans" docs/agent-memory docs/superpowers -g "*.md"
```

До этой записи отдельного memory pattern про язык implementation plans не было;
позже она стала также канонической записью про язык design specs.

## Retrieval Hints

планы на русском, спецификации на русском, implementation plans, design specs,
writing-plans, brainstorming specs, русский язык, язык планов, язык
спецификаций, docs/superpowers/plans, docs/superpowers/specs, planning language,
superpowers plans, superpowers specs
