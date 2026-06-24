# Agent Instructions

Before working in this repository:

1. Read `docs/agent-memory/protocol.md`.
2. Search `docs/agent-memory/file-map.md` and memory entries for context related to the user's request.
3. Read only the memory entries that are relevant to the request.
4. After significant work, decide whether durable memory needs an update.

Create or update agent memory only when both conditions hold:

1. The knowledge is likely to remain useful for at least a week.
2. Existing code, design, plan, runbook, or wiki does not already preserve it, or the memory adds an important explanation of why.

Store decisions with consequences, non-obvious bug root causes, stable patterns, non-obvious file relationships, and unique operational constraints. Do not store task completion, changed-file lists, test logs, sync/ingest/lint results, or summaries of existing plans and wiki nodes. Update an existing entry instead of creating a duplicate. Use `sessions/` only for unfinished handoff or a unique result that fits no decision, pattern, bugfix, or wiki node.

Do not store secrets, full chats, temporary logs, or unverified guesses.

## Project Knowledge Wiki

This repository also contains a broader project knowledge wiki:

- `RAW_inputs/` stores raw source materials.
- `Wiki/` stores canonical domain entities, concepts, actors, commands, events, policies, specifications, conflicts, questions, and registries.
- `DDD_Wiki/` stores the DDD domain model: domains, subdomains, bounded contexts, context maps, aggregates, invariants, state machines, use cases, integration patterns, and model health.
- `Vision_wiki/` stores legacy/source product knowledge, decisions, conflicts, assumptions, stakeholders, and follow-ups.
- `Code_wiki/` stores technical knowledge, architecture notes, runbooks, ADRs, API notes, and repository-change ingest entries.
- `memory/` stores live wiki state and LLM-wiki method files.
- `Общие_принципы/` stores reusable discovery and meeting methodology.
- `docs/knowledge-pipeline/README.md` describes the manual pipeline.

Human-readable wiki content, implementation plans, runbooks, follow-ups, and state files must be written in Russian. Do not translate paths, commands, file names, API names, types, identifiers, package names, or code.

Manual wiki workflow:

1. Morning: run `/sync-vision`, check `memory/project-state.md`, check new files in `RAW_inputs/`, then run `/ingest` for new raw inputs.
2. Before a model discovery meeting: run `/discover --context ... --phase ...`; it must inspect the current `Wiki/DDD_Wiki` model and conflicts, generate 150 candidate questions internally, then present the top 15.
3. Before sprint planning: run `/plan-sprint`; it must inspect current code, `Code_wiki`, `Wiki/DDD_Wiki`, conflicts, and the 14-day sprint frame, generate 150 planning questions internally, then present the top 15.
4. After a meeting: put the transcript in `RAW_inputs/meetings/`, run `/ingest`, update `Wiki/DDD_Wiki` first, keep `Vision_wiki` as legacy/source knowledge, record conflicts/follow-ups, and update `memory/project-state.md`.
5. Weekly: run `/lint-wiki`, run `/sync-vision`, and produce a wiki health report.
6. Weekly: run `/audit-memory`; present cleanup candidates and wait for confirmation before deleting or merging anything.

When `/ingest` is run without parameters, process 1-5 unambiguous newly added RAW inputs sequentially. Do not reread old already processed raw files automatically; changed old raw files are ambiguity and require confirmation. Process any new raw file, not only files with questions or answers. If there are more than 5 RAW candidates or any ambiguity, list the candidates and ask for confirmation before processing. If there are no new RAW inputs, do not edit files; report that ingest was not performed and suggest an explicit path, `/ingest repository-snapshot`, or `/ingest repository-change` if appropriate.

Use `/ingest repository-snapshot` through `.agents/skills/source-command-ingest/SKILL.md` when existing unchanged repository content needs to be added to `Code_wiki`: initial technical inventory, large external changes, or stale Code_wiki. Snapshot writes only knowledge documentation and must not edit code, configuration, migrations, or tests.

Invoke `/ingest repository-change` only when completed work contains new durable technical knowledge that needs to be reflected in `Code_wiki`. Repository Change Ingest itself must inspect the knowledge and its sources, determine whether to create a new node or update existing nodes, make those changes, and update the compact registry. If there is no new durable technical knowledge, do not invoke the mode. Task size, plan completion, commits, and successful tests are not triggers. Pre-commit must not run or check repository-change ingest. Repository-change ingest writes only knowledge documentation in `Code_wiki`; it must not edit code, configuration, migrations, or tests.

Do not edit `C:\Repositories\ai-po-template-experiments`. It is a read-only reference for template/methodology ideas only. Do not copy project-specific facts from it.

If new knowledge conflicts with old documentation, `/ingest` must record the conflict or follow-up. After `/ingest`, old documentation may be corrected only for conflicts that already exist in `Vision_wiki/decisions/followups/index.md`, are related to `Code_wiki`, and can be resolved from new knowledge. Code, configuration, migrations, and tests require a separate explicit implementation task.
