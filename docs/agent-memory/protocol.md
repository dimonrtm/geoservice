# Agent Memory Protocol

This repository uses local Markdown files as long-term memory for agents. The memory is part of the Git repository and must stay readable by humans.

## Start Of Work

At the start of a new chat or task:

1. Read `AGENTS.md`.
2. Read this protocol.
3. Extract 3-8 search terms from the user's request: feature names, errors, domains, technologies, file names, or module names.
4. Search the memory area with `rg`.
5. Prefer `docs/agent-memory/file-map.md` for fast topic-to-file lookup.
6. Read only memory entries that are relevant to the current request.
7. Continue normal repository exploration with `rg`.

Example searches:

```powershell
rg -n "realtime|websocket|typecheck" docs/agent-memory
rg -n "auth|login|jwt" docs/agent-memory/file-map.md docs/agent-memory
```

Do not load every memory entry and do not read recent entries without a reason.

## What To Store

Store durable context that will still help in a week:

- architectural and product decisions;
- bug symptoms, root cause, fix, and verification;
- non-obvious relationships between files;
- important commands for running, checking, or debugging the project;
- stable implementation patterns already used in this repository;
- project constraints that affect future work.

Do not store:

- full chat transcripts;
- temporary reasoning or discarded scratch work;
- small mechanical actions with no durable value;
- secrets, tokens, passwords, API keys, `.env` values, or personal data;
- build output, noisy logs, or unverified guesses.

## When To Write Memory

After significant work, add or update a memory entry yourself. Significant work means the result is likely to help the next agent understand what happened, why it matters, and which files are involved.

Use these folders:

- `docs/agent-memory/sessions/` for summaries of significant completed work;
- `docs/agent-memory/decisions/` for architectural and product decisions;
- `docs/agent-memory/patterns/` for repeated implementation rules;
- `docs/agent-memory/bugfixes/` for bug root causes and fixes.

Use filenames in this format:

```text
YYYY-MM-DD-short-ascii-slug.md
```

Examples:

```text
2026-05-30-agent-memory-operating-rules.md
2026-05-30-realtime-typecheck-fix.md
```

## Entry Template

```markdown
# Short Title

Date: YYYY-MM-DD
Type: session | decision | pattern | bugfix
Tags: frontend, realtime, websocket
Related files:

- `apps/frontend/src/example.ts`

## Summary

Коротко, что должен помнить следующий агент.

## Context

Почему это важно и когда применять.

## Actions

- YYYY-MM-DD: Что было сделано и результат.

## Verification

Команды проверки и итог. Если не проверялось, явно указать почему.

## Retrieval Hints

Слова и фразы, по которым эту запись должен найти будущий агент.
```

Human-facing fields should use the main language of the chat, usually Russian in this repository. Do not translate paths, commands, APIs, identifiers, or type names.

## File Map

Update `docs/agent-memory/file-map.md` when work creates or changes a durable topic-to-file relationship.

Keep entries compact:

```markdown
- map realtime websocket: `apps/frontend/src/composables/map/useLayerRealtime.ts`, `apps/frontend/src/contracts/realtime.ts`
```

The file map is not a history log. It is a quick navigation aid.

## Superseding Memory

Do not delete old memory entries only because they became outdated. If a new entry replaces an old one, add this metadata line to the old entry:

```markdown
Superseded by: docs/agent-memory/<folder>/<new-entry>.md
```

Delete a memory entry only when it was accidental, contains a secret, or is clearly harmful.

## Manual Check Before Finishing

Before finishing work that changed memory, check:

- the entry is in the correct folder;
- the filename matches `YYYY-MM-DD-short-ascii-slug.md`;
- all required sections are present;
- `Related files` exist or are explicitly described as planned files;
- `file-map.md` is updated when durable file relationships changed;
- the entry contains no secrets, full chats, noisy logs, or unverified guesses;
- the entry is useful beyond the current chat.
