# Discover Startup Mode

Date: 2026-05-30
Type: bugfix
Tags: wiki, discover, skills, discovery
Related files:

- `.agents/skills/source-command-discover/SKILL.md`
- `Общие_принципы/Вопросы стейкхолдеру.md`
- `Общие_принципы/Фазы наполнения wiki.md`
- `Vision_wiki/solution/USM.md`
- `Vision_wiki/solution/roadmap.md`
- `Vision_wiki/solution/nfr.md`
- `Vision_wiki/solution/architecture_vision.md`
- `docs/knowledge-pipeline/README.md`

## Summary

Первый перенос `/discover` был неполным: skill готовил обычный список вопросов, но не восстанавливал startup-mode из PO pipeline. Исправлено: первый `/discover` теперь должен задавать стартовую анкету, создавать пустые solution-артефакты и опираться на фазы наполнения wiki.

## Context

Пользователь указал, что первый вызов `/discover` должен задавать вопросы по проекту, создавать пустые артефакты в `Vision_wiki/solution` и создавать фазы наполнения wiki. Donor-репозиторий использовался только read-only для сверки поведения; проектные факты из него не переносились.

## Actions

- 2026-05-30: Расширен `.agents/skills/source-command-discover/SKILL.md`: добавлен первый запуск, стартовая анкета, режим `--phase`, режим `--context` и ограничения.
- 2026-05-30: Расширен `Общие_принципы/Вопросы стейкхолдеру.md`: добавлены стартовая анкета, артефакты и фазы Ф0-Ф8.
- 2026-05-30: Создан `Общие_принципы/Фазы наполнения wiki.md`.
- 2026-05-30: Созданы пустые стартовые solution-артефакты `USM.md`, `roadmap.md`, `nfr.md`, `architecture_vision.md`.

## Verification

Проверить `python scripts/lint-wiki.py --root .` и убедиться, что новые wiki-ноды валидны.

## Retrieval Hints

discover startup mode, первый discover, фазы наполнения wiki, solution artifacts, USM, roadmap, nfr, architecture vision
