# RAW Inputs Batch Ingest

Date: 2026-05-30
Type: decision
Tags: wiki, ingest, raw-inputs, batch
Related files:

- `.agents/skills/source-command-ingest/SKILL.md`
- `docs/knowledge-pipeline/README.md`
- `AGENTS.md`
- `RAW_inputs/index.md`

## Summary

`/ingest` без параметров должен обрабатывать несколько новых RAW inputs подряд, если их немного и они однозначны.

## Context

Раньше `/ingest` без параметров при нескольких кандидатах показывал список и спрашивал, с какого начать. Пользователь уточнил желаемое поведение: если новых RAW inputs немного, агент должен обработать их по очереди; если файлов много или есть неоднозначность, нужно запросить подтверждение.

## Actions

- 2026-05-30: В `.agents/skills/source-command-ingest/SKILL.md` добавлено правило batch-обработки 1-5 однозначных RAW-кандидатов.
- 2026-05-30: В `docs/knowledge-pipeline/README.md` добавлен раздел `/ingest` без параметров.
- 2026-05-30: В `AGENTS.md` добавлена короткая инструкция для будущих агентов.
- 2026-05-30: Обновлен `docs/agent-memory/file-map.md`.

## Verification

Проверить `python scripts/lint-wiki.py --root .`, `python -m unittest discover -s scripts\tests`, `python scripts/check-memory-needed.py --check`, `git diff --check`.

## Retrieval Hints

RAW_inputs batch ingest, ingest без параметров, 1-5 файлов, новые RAW inputs, неоднозначность ingest
