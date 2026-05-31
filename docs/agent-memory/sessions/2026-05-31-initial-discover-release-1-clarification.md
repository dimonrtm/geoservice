# Initial Discover And Release 1 Clarification

Date: 2026-05-31
Type: session
Tags: wiki, discover, release-1, raw-inputs, stakeholder
Related files:

- `RAW_inputs/documents/спринт 1.odt`
- `Vision_wiki/chats/2026-05-31-initial-discover.md`
- `Vision_wiki/concepts/about_project.md`
- `Vision_wiki/entities/stakeholders/dmitry_popov.md`
- `Vision_wiki/chats/2026-05-30-release-1-document.md`
- `Vision_wiki/concepts/first_release_mvp.md`
- `Code_wiki/архитектура/api_contract_first_release_requirements.md`
- `memory/project-state.md`

## Summary

Первый `/discover` подтвердил название GeoService, pet-project контекст, стадию идея / прототип и владельца решений. Пользователь уточнил: `RAW_inputs/documents/спринт 1.odt` актуален, но описывает план первого релиза, а не спринта.

## Context

До `/discover` активные wiki-ноды последовательно использовали термин `Sprint 1`. Эта трактовка была исправлена в активной wiki на `Release 1`; исходный RAW-файл не переименован, потому что `RAW_inputs/` хранит неизменяемые материалы. Историческая memory-запись `docs/agent-memory/sessions/2026-05-30-sprint-1-raw-ingest.md` сохранена и помечена как superseded.

## Actions

- 2026-05-31: Созданы `Vision_wiki/chats/2026-05-31-initial-discover.md`, `Vision_wiki/concepts/about_project.md` и `Vision_wiki/entities/stakeholders/dmitry_popov.md`.
- 2026-05-31: Активные product и technical wiki-ноды переименованы с `Sprint 1` на `Release 1`, обновлены wikilinks и индексы.
- 2026-05-31: `FU-2026-05-30-003` закрыт; добавлен `FU-2026-05-31-001` для прохождения фаз Ф1-Ф3.

## Verification

Запустить `python scripts/lint-wiki.py --root .`, `python scripts/check-memory-needed.py --check` и `git diff --check`.

## Retrieval Hints

initial discover, первый discover, GeoService pet project, Release 1, первый релиз, спринт 1 ODT, Попов Дмитрий, Ф1 Ф2 Ф3
