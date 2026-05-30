# Правила Работы Долговременной Памяти Агентов

Date: 2026-05-30
Type: decision
Tags: agent-memory, workflow, markdown, retrieval, git
Related files:

- `AGENTS.md`
- `docs/agent-memory/protocol.md`
- `docs/agent-memory/file-map.md`
- `docs/superpowers/specs/2026-05-30-agent-memory-design.md`

## Summary

Память агентов в GeoService хранится строго внутри репозитория как Markdown и версионируется через Git. Новый чат читает минимальный протокол, делает поиск по запросу пользователя и не загружает всю память без причины.

## Context

Пользователь выбрал новый дизайн с нуля: без восстановления старого плана, без CLI, JSONL, базы данных, embeddings и внешних зависимостей. Записи добавляются агентом самостоятельно после значимой работы, если контекст будет полезен через неделю.

## Actions

- 2026-05-30: Зафиксировано, что память должна быть repo-local и Git-versioned.
- 2026-05-30: Выбран ручной Markdown-формат записей.
- 2026-05-30: Выбран компактный `file-map.md` как самый экономный по токенам способ находить связанные файлы.
- 2026-05-30: Выбрана структура `sessions/`, `decisions/`, `patterns/`, `bugfixes/`.

## Verification

Проверяется smoke-поиском после внедрения:

```powershell
rg -n "repo-local|Markdown|file-map|значимой работы" docs/agent-memory
```

Ожидается, что поиск находит эту запись и протокол памяти.

## Retrieval Hints

agent memory, долговременная память, repo-local, markdown memory, file-map, significant work, значимая работа, протокол памяти, новый чат, Git-versioned memory
