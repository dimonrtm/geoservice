# Discover Phase F8 New Release 1

Date: 2026-06-11
Type: session
Tags: wiki, discover, phase-f8, release-1, utility-gis-editor
Related files:

- `docs/superpowers/specs/2026-06-11-release-1-utility-workflow-design.md`
- `Vision_wiki/chats/2026-06-11-phase-f8-release-1-closeout.md`
- `Vision_wiki/decisions/release_1_utility_workflow.md`
- `Vision_wiki/concepts/first_release_mvp.md`
- `Vision_wiki/solution/USM.md`
- `Vision_wiki/decisions/followups/index.md`
- `memory/project-state.md`

## Summary

Ф8 заменила старое generic GIS определение Release 1 полным `Utility GIS editor` workflow до authoritative post и audit. Существующие JWT, PostGIS, MapLibre, bbox, CRUD, `version`/`409` и WebSocket сохраняются как внутренний foundation.

## Context

После Ф2-Ф7 utility workflow был подробно описан, но wiki продолжала смешивать его со старым Release 1 из `спринт 1.odt`. Пользователь подтвердил новый product boundary, domain model, API/storage, frontend UX, errors/tests и migration approach.

## Actions

- 2026-06-11: Подтвержден полный path: work order -> edit version -> validation -> reconcile -> conflict resolution -> review -> post -> audit.
- 2026-06-11: Созданы design spec, Ф8 session-нода и активное decision.
- 2026-06-11: Пересобраны `first_release_mvp.md` и верхний authoritative section `USM.md`.
- 2026-06-11: Добавлены follow-up'ы на code compliance matrix и синхронизацию старых requirements.

## Verification

- `scripts/lint-wiki.py --root .` через bundled Python: только 11 ожидаемых `missing_frontmatter` для неизменяемых RAW Markdown sources.
- `scripts/check-memory-needed.py --check`: passed.
- `git diff --check`: passed.
- Follow-up count: 11 open, 7 resolved.

## Retrieval Hints

Ф8, new Release 1, Utility GIS editor, full workflow, authoritative post, generic foundation, compliance matrix
