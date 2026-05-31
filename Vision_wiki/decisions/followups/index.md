---
title: Follow-ups
type: index
status: active
created: 2026-05-30
updated: 2026-05-31
source: null
tags: [followups, conflicts]
---

# Follow-ups

Контролируемая очередь открытых вопросов, документационных конфликтов и кандидатов на post-ingest correction.

## Открытые Follow-up'ы

| ID | Статус | Область | Источник | Требуемое действие |
|---|---|---|---|---|
| FU-2026-05-30-001 | resolved | Product discovery | [[../../solution/USM]], [[../../solution/roadmap]], [[../../solution/nfr]], [[../../solution/architecture_vision]], [[../../chats/2026-05-30-release-1-document]] | RAW source `RAW_inputs/documents/спринт 1.odt` добавлен и использован для заполнения solution-артефактов. |
| FU-2026-05-30-002 | open | Code_wiki | [[../../../Code_wiki/состояние_проекта/repository_snapshot]] | Отдельной implementation/docs-задачей решить, нужны ли непустые `infra/docker-compose.full.yml`, `scripts/dev.cmd`, `scripts/docker_full.cmd`, `scripts/infra_dev.cmd` и более полный `infra/.env.example`. |
| FU-2026-05-30-003 | resolved | Product validation | [[../../chats/2026-05-30-release-1-document]], [[../../chats/2026-05-31-initial-discover]], `RAW_inputs/documents/спринт 1.odt` | Актуальность подтверждена 2026-05-31. Документ описывает план первого релиза, а не план спринта. |
| FU-2026-05-31-001 | open | Product discovery | [[../../concepts/about_project]], [[../../chats/2026-05-31-initial-discover]], [[../../chats/2026-05-31-phase-f1-why-now]] | Ф1 завершена. Пройти Ф2-Ф3: уточнить пользователей и боль, альтернативы и контекст использования; затем проверить точный тип продукта. |
| FU-2026-05-31-002 | open | Product discovery | [[../../chats/2026-05-31-phase-f1-why-now]], [[../../decisions/risk_assumption_log]] | На Ф2-Ф4 заменить критерий первого релиза "все типа работает" на проверяемый demo-script и acceptance criteria. |
| FU-2026-05-31-003 | open | Product discovery | [[../../concepts/product_vision_board]], [[../../concepts/lean_canvas]] | Уточнить приоритет результата: demo, portfolio, применение в реальной работе или основа будущего продукта. |

## Правило Post-Ingest Correction

После `/ingest` можно исправлять старую документацию только по конфликтам, которые уже перечислены здесь и связаны с `Code_wiki`. Нельзя менять код, конфигурацию, миграции или тесты как часть post-ingest correction.
