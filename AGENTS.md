# Agent Instructions

Before working in this repository:

1. Read `docs/agent-memory/protocol.md`.
2. Search `docs/agent-memory/file-map.md` and memory entries for context related to the user's request.
3. Read only the memory entries that are relevant to the request.
4. After significant work, add or update a memory entry.

Significant work means context that will still help in a week: decisions, bug root causes, non-obvious file relationships, important commands, or stable project patterns. Do not store secrets, full chats, temporary logs, or unverified guesses.

## Project Knowledge Wiki

This repository also contains a broader project knowledge wiki:

- `RAW_inputs/` stores raw source materials.
- `Vision_wiki/` stores product knowledge, decisions, conflicts, assumptions, stakeholders, and follow-ups.
- `Code_wiki/` stores technical knowledge, architecture notes, runbooks, ADRs, API notes, and repository-change ingest entries.
- `memory/` stores live wiki state and LLM-wiki method files.
- `Общие_принципы/` stores reusable discovery and meeting methodology.
- `docs/knowledge-pipeline/README.md` describes the manual pipeline.

Human-readable wiki content, implementation plans, runbooks, follow-ups, and state files must be written in Russian. Do not translate paths, commands, file names, API names, types, identifiers, package names, or code.

Manual wiki workflow:

1. Morning: run `/sync-vision`, check `memory/project-state.md`, check new files in `RAW_inputs/`, then run `/ingest` for new raw inputs.
2. Before a meeting: run `/discover --context ... --phase ...`, prepare 10-15 questions, and prepare a checklist.
3. After a meeting: put the transcript in `RAW_inputs/meetings/`, run `/ingest`, update `Vision_wiki`, record conflicts/follow-ups, and update `memory/project-state.md`.
4. Weekly: run `/lint-wiki`, run `/sync-vision`, and produce a wiki health report.

When `/ingest` is run without parameters, process 1-5 unambiguous new RAW inputs sequentially. If there are more than 5 RAW candidates or any ambiguity, list the candidates and ask for confirmation before processing. If there are no new RAW inputs, do not edit files; report that ingest was not performed and suggest an explicit path, `/ingest repository-snapshot`, or `/ingest repository-change` if appropriate.

Use `/ingest repository-snapshot` through `.agents/skills/source-command-ingest/SKILL.md` when existing unchanged repository content needs to be added to `Code_wiki`: initial technical inventory, large external changes, or stale Code_wiki. Snapshot writes only knowledge documentation and must not edit code, configuration, migrations, or tests.

After the full implementation plan or major task is complete, and before the final report to the user, the agent must invoke `/ingest repository-change` through `.agents/skills/source-command-ingest/SKILL.md`. Do not invoke it after every small step. This is tied to completed plan/task work, not to commit. Pre-commit must not run or check repository-change ingest. Repository-change ingest writes only knowledge documentation in `Code_wiki`; it must not edit code, configuration, migrations, or tests.

Do not edit `C:\Repositories\ai-po-template-experiments`. It is a read-only reference for template/methodology ideas only. Do not copy project-specific facts from it.

If new knowledge conflicts with old documentation, `/ingest` must record the conflict or follow-up. After `/ingest`, old documentation may be corrected only for conflicts that already exist in `Vision_wiki/decisions/followups/index.md`, are related to `Code_wiki`, and can be resolved from new knowledge. Code, configuration, migrations, and tests require a separate explicit implementation task.
