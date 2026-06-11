# Release 1 Utility Sprint Plan

Date: 2026-06-11
Type: session
Tags: planning, release-1, utility-gis-editor, compliance, sprints
Related files:

- `docs/requirements/release-1-utility-code-compliance.md`
- `docs/superpowers/plans/2026-06-11-release-1-utility-workflow-sprints.md`
- `docs/superpowers/specs/2026-06-11-release-1-utility-workflow-design.md`
- `Vision_wiki/decisions/followups/index.md`
- `memory/project-state.md`

## Summary

Новый Release 1 разложен на 7 двухнедельных спринтов крупного уровня: foundation, isolated editing, validation, reconcile/conflicts, review/post, audit/demo operations, acceptance/hardening.

## Context

Code compliance matrix показала, что текущий код пригоден как generic GIS foundation, но доменные gates utility workflow отсутствуют. План сохраняет legacy API и вводит отдельную utility schema, change-set workflow и единственный authoritative mutation path через transactional post.

## Actions

- 2026-06-11: Составлена code compliance matrix по backend/frontend/infra/tests.
- 2026-06-11: Зафиксированы 7 спринтов по 2 недели с целями, крупными блоками, продуктовыми результатами и критериями завершения.
- 2026-06-11: По уточнению пользователя удалена преждевременная техническая декомпозиция по файлам, миграциям, тестам и командам; она должна готовиться отдельно перед каждым спринтом.
- 2026-06-11: `FU-2026-06-11-001` закрыт; docs synchronization остается открытой до фактической реализации.

## Verification

- План содержит 7 спринтов, 7 продуктовых результатов и 7 крупноуровневых критериев завершения.
- `scripts/check-memory-needed.py --check`: passed.
- Wiki lint: только 11 известных `missing_frontmatter` в RAW Markdown из `FU-2026-06-01-004`.
- `git diff --check`: passed.

## Retrieval Hints

Release 1 high-level sprint plan, code compliance matrix, 7 sprints, utility workflow roadmap
