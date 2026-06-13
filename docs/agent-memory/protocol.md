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

Create or update memory only when both conditions hold:

1. The knowledge is likely to remain useful for at least a week.
2. Existing code, design, plan, runbook, or wiki does not already preserve it,
   or the memory adds an important explanation of why.

Store:

- architectural and product decisions with alternatives and consequences;
- bug symptoms, root cause, fix, and verification;
- non-obvious relationships between files;
- unique commands or environment constraints that are absent from a runbook;
- stable implementation patterns already used in this repository;
- project constraints that affect future work.

Do not store:

- task, plan, test run, or commit completion;
- changed-file lists;
- summaries of existing designs, plans, code, or wiki nodes;
- `/sync-vision`, `/lint-wiki`, or `/ingest` results;
- temporary status or chronological action logs;
- full chat transcripts;
- temporary reasoning or discarded scratch work;
- small mechanical actions with no durable value;
- secrets, tokens, passwords, API keys, `.env` values, or personal data;
- build output, noisy logs, or unverified guesses.

## When To Write Memory

After significant work, first search for an existing relevant entry. Update it
instead of creating a duplicate.

Before creating a memory entry, answer:

1. What unique knowledge would be lost without this entry?
2. Why is a link to existing code, design, plan, runbook, or wiki insufficient?
3. In which future task should an agent retrieve this entry?

If the answers are not concrete, do not create the entry.

Changes to `AGENTS.md`, `CONTRIBUTING.md`, `docs/knowledge-pipeline/`,
`docs/agent-memory/`, or repo-local command skills should be checked for a
needed update to existing operating knowledge. The changed rule may be
self-contained; do not create memory merely to satisfy the checker.

Before finishing work in those areas, run:

```powershell
python scripts/check-memory-needed.py --check
```

If the check warns, update existing durable memory when possible. Create a new
entry only if it passes the three-question gate. Update
`docs/agent-memory/file-map.md` when a durable topic-to-file relationship
changed.

Use these folders:

- `docs/agent-memory/sessions/` only for unfinished handoff or a unique result
  that fits no decision, pattern, bugfix, or wiki node;
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

Keep a useful historical entry when its context still matters. If a new entry
replaces it, add this metadata line to the old entry:

```markdown
Superseded by: docs/agent-memory/<folder>/<new-entry>.md
```

Do not use `Superseded by` to preserve noise. After `/audit-memory` and explicit
user confirmation, duplicate or process-only entries may be merged or deleted
from the working tree; Git remains the historical archive. Update
`file-map.md` and direct links in the same cleanup.

## Periodic Audit

Weekly, run:

```powershell
python scripts/audit-memory.py --root . --format markdown
```

The audit is read-only. Review age, uniqueness, canonical sources, duplicates,
broken references, session budget, registry budget, and historical fields in
`memory/project-state.md`. Do not delete, move, or merge files without explicit
user confirmation.

## Manual Check Before Finishing

Before finishing work that changed memory, check:

- the entry is in the correct folder;
- the filename matches `YYYY-MM-DD-short-ascii-slug.md`;
- all required sections are present;
- `Related files` exist or are explicitly described as planned files;
- `file-map.md` is updated when durable file relationships changed;
- the entry contains no secrets, full chats, noisy logs, or unverified guesses;
- the entry is useful beyond the current chat;
- the entry contains unique knowledge and a concrete retrieval scenario;
- the same knowledge is not already preserved by code, design, plan, runbook,
  wiki, or another active memory entry.
