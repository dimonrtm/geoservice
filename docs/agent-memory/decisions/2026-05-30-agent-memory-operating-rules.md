# Правила Работы Долговременной Памяти Агентов

Date: 2026-05-30
Type: decision
Tags: agent-memory, workflow, markdown, retrieval, git
Related files:

- `AGENTS.md`
- `docs/agent-memory/protocol.md`
- `docs/agent-memory/file-map.md`
- `docs/superpowers/specs/2026-05-30-agent-memory-design.md`
- `docs/superpowers/specs/2026-06-13-memory-knowledge-base-optimization-design.md`
- `docs/superpowers/plans/2026-06-13-memory-knowledge-base-optimization.md`

## Summary

Память агентов в GeoService хранится внутри репозитория как Markdown и
версионируется через Git. Новая запись создаётся только для уникального
долговременного знания, которое нельзя надёжно восстановить из канонических
файлов. Новый чат читает минимальный протокол и загружает только релевантные
записи.

## Context

Первоначальный Markdown-подход сохраняется без JSONL, базы данных, embeddings
и внешних зависимостей. Оптимизация потребовалась, потому что критерий
«значимой работы» превращал память и repository-change ingest в хронологию
задач, тестовых прогонов и изменений файлов.

## Actions

- 2026-05-30: Зафиксировано, что память должна быть repo-local и Git-versioned.
- 2026-05-30: Выбран ручной Markdown-формат записей.
- 2026-05-30: Выбран компактный `file-map.md` как самый экономный по токенам способ находить связанные файлы.
- 2026-05-30: Выбрана структура `sessions/`, `decisions/`, `patterns/`, `bugfixes/`.
- 2026-06-13: Согласован дизайн оптимизации памяти и knowledge base. После
  реализации memory-записи должны создаваться только для уникального
  долговременного знания, `sessions/` становится исключением, а
  `/ingest repository-change` вызывается только при наличии нового устойчивого
  технического знания для `Code_wiki`; конкретные ноды и create/update
  определяет и выполняет сам ingest.
- 2026-06-13: Подготовлен implementation plan с read-only memory audit,
  бюджетами `20 sessions / 90 days / 200 lines / 24 KiB`, сохранением legacy
  записей до отчёта и отдельным пользовательским подтверждением cleanup.
- 2026-06-13: Реализованы узкий memory gate, исключительный режим
  `sessions/`, read-only `/audit-memory`, двухусловный repository-change gate
  и компактный реестр. После явного подтверждения пользователя process-only
  и canonical-source session task logs удалены, legacy repository-change
  history убрана из рабочего дерева, а Git оставлен историческим архивом.

## Verification

Проверяется smoke-поиском после внедрения:

```powershell
rg -n "уникального|read-only|repository-change gate|file-map" docs/agent-memory
```

Ожидается, что поиск находит эту запись и протокол памяти.

## Retrieval Hints

agent memory, долговременная память, repo-local, markdown memory, file-map, significant work, значимая работа, протокол памяти, новый чат, Git-versioned memory, оптимизация памяти, repository-change trigger, memory audit
