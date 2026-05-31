# Skill System Completeness

Date: 2026-05-30
Type: bugfix
Tags: wiki, skills, ingest, sync-vision, lint-wiki, templates
Related files:

- `.agents/skills/source-command-discover/SKILL.md`
- `.agents/skills/source-command-ingest/SKILL.md`
- `.agents/skills/source-command-sync-vision/SKILL.md`
- `.agents/skills/source-command-lint-wiki/SKILL.md`
- `Vision_wiki/_templates/`
- `Общие_принципы/Фреймворк работы со стейкхолдером.md`

## Summary

После исправления startup-mode для `/discover` выявлено, что остальные source-command skills тоже были перенесены слишком кратко. Расширены `/ingest`, `/sync-vision`, `/lint-wiki`; добавлены недостающие product discovery templates в `Vision_wiki/_templates/`; восстановлены поведенческие протоколы stakeholder framework.

## Context

Пользователь попросил проверить, все ли скопировано для работы других skill’ов. Сверка с donor `.agents/skills/source-command-*` показала, что имена skill’ов совпадали, но алгоритмы и поддерживающие шаблоны были неполными. Donor использовался только read-only; проектные факты не переносились.

## Actions

- 2026-05-30: Расширен `/ingest`: классификация RAW inputs, mapping в Vision/Code wiki, summary источника, индексы, ограничения.
- 2026-05-30: Расширен `/sync-vision`: сбор изменений, обновление индексов, stale, project-state, отчет.
- 2026-05-30: Расширен `/lint-wiki`: linter, семантический обзор, допустимые структурные исправления, отчет.
- 2026-05-30: Добавлены шаблоны `concept`, `about_project`, `product_vision_board`, `lean_canvas`, `jtbd`, `persona`, `user_story_map`, `adr`.
- 2026-05-30: Расширен `Фреймворк работы со стейкхолдером.md` с 15 поведенческими протоколами.

## Verification

Проверить `python scripts/lint-wiki.py --root .`, `python -m unittest discover -s scripts\tests`, grep на donor-specific terms в измененных skill/template files.

## Retrieval Hints

skills completeness, source-command-ingest, source-command-sync-vision, source-command-lint-wiki, templates, stakeholder framework
