# Agent Memory MVP

Date: 2026-05-30
Type: session
Tags: agent-memory, markdown, documentation, retrieval, workflow
Related files:

- `AGENTS.md`
- `docs/agent-memory/README.md`
- `docs/agent-memory/protocol.md`
- `docs/agent-memory/file-map.md`
- `docs/agent-memory/decisions/2026-05-30-agent-memory-operating-rules.md`
- `README.md`

## Summary

В репозитории внедрена Markdown-память агентов: короткий `AGENTS.md`, общий протокол, компактный `file-map.md`, папки для записей и первая decision-запись с правилами работы памяти.

## Context

Память нужна, чтобы новые чаты быстро восстанавливали релевантный контекст по запросу пользователя, находили связанные файлы и сохраняли только долгосрочно полезные итоги после значимой работы.

## Actions

- 2026-05-30: Добавлен корневой `AGENTS.md` как входная инструкция для агентов.
- 2026-05-30: Добавлен `docs/agent-memory/protocol.md` с правилами чтения, записи, приватности и ручной проверки.
- 2026-05-30: Добавлен `docs/agent-memory/file-map.md` для быстрого поиска файлов по темам.
- 2026-05-30: Добавлена seed decision-запись о правилах памяти.
- 2026-05-30: README получил ссылку на `docs/agent-memory/README.md`.

## Verification

Smoke-проверки:

```powershell
rg -n "protocol.md|file-map.md|significant work|значим" AGENTS.md docs/agent-memory
rg -n "frontend realtime websocket|websocket layer realtime auth|polygon editing|docker compose local dev" docs/agent-memory/file-map.md
rg -n "agent-memory" README.md
rg -n "no CLI|no JSONL|no database|no embeddings|external service" AGENTS.md docs/agent-memory/README.md docs/agent-memory/protocol.md docs/agent-memory/decisions/2026-05-30-agent-memory-operating-rules.md
```

Ожидаемый результат: поиск находит стартовый протокол, карту файлов, seed decision, ссылку из README и только пояснения “не используем” для исключённых MVP-механизмов.

## Retrieval Hints

agent memory MVP, память агентов, AGENTS.md, protocol.md, file-map.md, markdown memory, retrieval workflow, значимая работа, новый чат
