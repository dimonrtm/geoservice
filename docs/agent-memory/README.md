# Agent Memory

This directory stores long-term memory for agents working in the GeoService repository.

The memory is local to this repository, versioned in Git, and written as Markdown. It is intentionally simple: no CLI, no JSONL index, no database, no embeddings, and no external service.

## Files

- `protocol.md` - authoritative workflow for reading and writing memory.
- `file-map.md` - compact topic-to-file map for fast retrieval.
- `sessions/` - summaries of significant completed work.
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

After significant work, add a Markdown entry using the template in `protocol.md`. Significant work means context that will still be useful in a week.

Do not store secrets, full chats, noisy logs, or unverified guesses.
