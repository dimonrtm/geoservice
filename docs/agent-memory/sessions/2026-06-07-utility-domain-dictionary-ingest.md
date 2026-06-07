# Utility Domain Dictionary RAW Ingest

Date: 2026-06-07
Type: session
Tags: wiki, ingest, utility-network, domain-language
Related files:

- `RAW_inputs/documents/utility_gis_editor_domain_dictionary.md`
- `Vision_wiki/chats/2026-06-07-utility-gis-editor-domain-dictionary.md`
- `Vision_wiki/concepts/utility_gis_editing_domain.md`
- `Vision_wiki/entities/personas/utility_gis_editor.md`
- `Code_wiki/глоссарий/technical_terms.md`
- `RAW_inputs/index.md`
- `memory/project-state.md`

## Summary

Обработан новый RAW source со словарем `Utility GIS editing`. Зафиксированы канонические термины, workflow от work order до post и важное различие между save в edit version и публикацией в `Default`.

## Context

Источник описывает домен шире текущего Release 1. Wiki сохраняет его как язык анализа и проектирования, но не трактует domain commands как утвержденные endpoint names и не расширяет Ф4 scope до production branch versioning или topology engine.

## Actions

- 2026-06-07: Созданы source summary и атомарный domain concept.
- 2026-06-07: Persona связана с каноническим словарем.
- 2026-06-07: `Code_wiki/глоссарий/technical_terms.md` дополнен desired utility demo vocabulary с явной границей current/desired.
- 2026-06-07: Обновлены индексы, live state и `FU-2026-06-01-004` для шестого RAW Markdown source.

## Verification

- `scripts/lint-wiki.py --root .`: только 6 ожидаемых `missing_frontmatter` для неизменяемых RAW Markdown sources, включая новый dictionary.
- `scripts/check-memory-needed.py --check`: passed.
- `git diff --check`: passed.

## Retrieval Hints

utility domain dictionary, save vs post, edit version, Default, network feature, association, reconcile, domain commands
