# Agent Memory

This directory stores long-term memory for agents working in the GeoService repository.

The memory is local to this repository, versioned in Git, and written as Markdown. It is intentionally simple: no CLI, no JSONL index, no database, no embeddings, and no external service.

## Files

- `protocol.md` - authoritative workflow for reading and writing memory.
- `file-map.md` - compact topic-to-file map for fast retrieval.
- `sessions/` - exceptional unfinished handoff or unique outcomes that fit no decision, pattern, bugfix, or wiki node; not a task log.
- `decisions/` - architectural and product decisions.
- `patterns/` - repeated implementation rules.
- `bugfixes/` - bug symptoms, root causes, fixes, and verification.

## Agent Start

Agents should start with:

```powershell
rg -n "<request terms>" docs/agent-memory
```

Read `protocol.md` first, then use `file-map.md` and relevant memory entries. Do not load every entry without a reason.

## Writing Memory

After significant work, use the gate in `protocol.md`. Create or update memory only for unique durable knowledge that is not already preserved by code, design, plan, runbook, or wiki.

Do not store secrets, full chats, noisy logs, or unverified guesses.

## Auditing Memory

Run the read-only lifecycle audit:

```powershell
python scripts/audit-memory.py --root . --format markdown
```

The report proposes review actions. It never authorizes automatic deletion.
