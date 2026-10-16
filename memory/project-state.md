---
title: Состояние Проекта GeoService
type: state
status: active
created: 2026-05-30
updated: 2026-10-16
source: null
tags: [project-state, geoservice]
---

# Состояние Проекта GeoService

## Живое состояние

GeoService — исследовательский pet-проект. Агент через 02_expert_oldman_ufa представляет условную организацию; реальные сотрудники, интервью и регламенты не требуются. Внешние факты, решения модели и гипотезы различаются. Режим — [решение](../docs/agent-memory/decisions/2026-10-13-simulated-domain-organization.md).

Канонический слой — Wiki/DDD_Wiki, техническое знание — Code_wiki; Vision_wiki хранит legacy/source summaries. Ближайший срез остаётся ограниченным persisted edit одной линии/внутренней вершины с immutable baseline и явным POSITIONAL_ACCURACY_UNVERIFIED. Review/post остаётся downstream.

- Последний `/sync-vision`: 2026-10-16 20:07 +05:00 (Asia/Qyzylorda).
- Последний RAW ingest: [[../RAW_inputs/research_results/2026-10-16-utility-gis-editor-network-semantics-research]]. 17 веб-источников и 15 ответов о смысле правки, сетевых последствиях и передаче; правила условной организации приняты, реализация не заявлена.
- RAW: 44 источника, все отражены в индексе; новых необработанных нет.
- Открыты 19 follow-up’ов и 2 вопроса metadata/fixture. Новых blocking conflicts нет; в каноническом Wiki активных blocking conflicts 0. Legacy conflict о старом Release 1 остаётся active до отдельной docs-синхронизации.
- Stale-нода: [[../DDD_Wiki/model_health]]. Технические stale-описания Save/recovery исправлены; доменная очередь реализации и metadata/fixture требуют отдельной сверки.
- Lint 2026-10-16: 37 известных missing_frontmatter в неизменяемых RAW Markdown; новые ноды проверяются тем же lint.

## Требует внимания

[[../Wiki/policies/demo_dataset_qualification_policy]] требует сверки паспорта, фактического набора и правил версии. [[../Wiki/specifications/saved_line_quality_assessment]] связывает заключение с сохранённым состоянием и уточняет доказательство прежнего критерия при численной неопределённости. Два вопроса metadata/fixture остаются открытыми; допуски не изменены.

[[../Wiki/specifications/editing_resumption_allowed]] отделяет безопасный повтор прежнего намерения от допуска к новой записи. Один наряд в одном окне — ограничение учебной эксплуатации, а не реализованный lock. Success без current readback, закрытая работа, смена actor и stale confirmation имеют разные исходы.

Backend Save/registry/replay/history, frontend recovery state и source-level fixture/policy описаны в [[../Code_wiki/архитектура/edit_version_save_orchestration]], [[../Code_wiki/архитектура/frontend_save_recovery]], [[../Code_wiki/архитектура/edit_geometry_fixture_metadata]]. Recovery вызывается косвенно через store open/restore workspace; прямого component-вызова для этого не требуется. Полнота UI Save/Revert, продолжение после access block и S2-X01 не подтверждены.

FU-2026-10-11-001 сохраняет остаток сверки доменной очереди/metadata/fixture и зависимостей. Фактическая БД не опрашивалась; наличие seed L-003 не доказывает её состояние в старом volume. SIM-EVID-001 не является позиционным evidence L-003.

FU-2026-10-13-004 включает реализацию новых recovery-уточнений, evaluator, restart, архив/удержания и доступ. Сохраняются SIM-UGIS-POS-001 и SIM-UGIS-RET-001; автоочистка не включается. Исследование и сценарная матрица не доказывают успешную runtime-приёмку.

Исходные broad vendor/market утверждения с невоспроизводимыми ссылками не признаны подтверждёнными; их проверка остаётся в FU-2026-06-01-002. Конфликт lint с неизменяемыми RAW — FU-2026-06-01-004.

## Следующее действие

Сопоставить S2-X01 с уже существующим open/restore recovery и новыми сценариями RAW; реализовать только недостающие UI/confirmation/Revert границы отдельной задачей. Сверить два вопроса metadata/fixture по техническим источникам и при необходимости фактической БД, затем актуализировать доменную очередь. Обычный ingest без параметров сейчас не требуется.
