---
title: Состояние Проекта GeoService
type: state
status: active
created: 2026-05-30
updated: 2026-10-22
source: null
tags: [project-state, geoservice]
---

# Состояние Проекта GeoService

## Живое состояние

GeoService — исследовательский pet-проект. Агент через 02_expert_oldman_ufa представляет условную организацию; реальные сотрудники, интервью и регламенты не требуются. Внешние факты, решения модели и гипотезы различаются. Режим — [решение](../docs/agent-memory/decisions/2026-10-13-simulated-domain-organization.md).

Канонический слой — Wiki/DDD_Wiki, техническое знание — Code_wiki; Vision_wiki хранит legacy/source summaries. Ближайший срез остаётся ограниченным persisted edit одной линии/внутренней вершины с immutable baseline и явным POSITIONAL_ACCURACY_UNVERIFIED. Review/post остаётся downstream.

- Последний `/sync-vision`: 2026-10-22 18:16 +05:00 (Asia/Qyzylorda).
- RAW: 50 источников, все отражены в индексе; новых необработанных нет.
- Открыты 19 follow-up’ов и 2 вопроса metadata/fixture. Новых blocking conflicts нет; в каноническом Wiki активных blocking conflicts 0. Legacy conflict о старом Release 1 остаётся active до отдельной docs-синхронизации.
- Stale-нода: [[../DDD_Wiki/model_health]]. Технические stale-описания Save/recovery исправлены; доменная очередь реализации и metadata/fixture требуют отдельной сверки.
- Lint 2026-10-22: 37 известных missing_frontmatter только в неизменяемых RAW Markdown; других замечаний нет.

Осознанная подготовка и критерий завершения — [[../Wiki/policies/intentional_line_editing_policy]], [[../Wiki/specifications/line_edit_exercise_completed]]. Новые понятия — [[../Wiki/concepts/field_observation_acceptance]], [[../Wiki/concepts/network_representation_and_operational_state]]. Они не расширяют реализацию до field sync, asset lifecycle или расчётов.

Применимость основания после revision/отзыва — [[../Wiki/policies/change_basis_revision_policy]], [[../Wiki/specifications/line_edit_basis_applicable]], [[../DDD_Wiki/use_cases/reassess_line_edit_basis]]. Происхождение копий и время наблюдения раскрываются в ручной карточке; новые серверные статусы и guards не введены.

Выпуск и применимость заключения — [[../Wiki/policies/assessment_issue_and_correction_policy]], [[../Wiki/specifications/assessment_statement_usable]], [[../DDD_Wiki/use_cases/issue_and_correct_line_assessment]]. Правила различают документ и pass, исторический/частичный scope, спор, исправления и передачу; корпус 84 внешних документа сохранён в RAW. Это ручная модель без новых server states. Реализация остаётся в FU-2026-10-13-004.

## Требует внимания

[[../Wiki/policies/demo_dataset_qualification_policy]] требует сверки паспорта, фактического набора и правил версии. [[../Wiki/specifications/saved_line_quality_assessment]] связывает заключение с сохранённым состоянием и уточняет доказательство прежнего критерия при численной неопределённости. Два вопроса metadata/fixture остаются открытыми; допуски не изменены.

[[../Wiki/specifications/editing_resumption_allowed]] отделяет безопасный повтор прежнего намерения от допуска к новой записи. Один наряд в одном окне — ограничение учебной эксплуатации, а не реализованный lock. Success без current readback, закрытая работа, смена actor и stale confirmation имеют разные исходы.

Технические основания Save/recovery и fixture — [[../Code_wiki/архитектура/edit_version_save_orchestration]], [[../Code_wiki/архитектура/frontend_save_recovery]], [[../Code_wiki/архитектура/edit_geometry_fixture_metadata]]. Save/Revert controls и ручные retry/readback подключены. [Отчёт M4](../docs/sprint_2/2026-10-21-day-12-m4-report.md) фиксирует два успешных сценария Save/Revert с потерей ответа после commit, restart API, refresh, replay и GET; при синхронизации они повторно не запускались. Это не подтверждает восстановление после потери sessionStorage, crash БД или повторного входа после потери доступа. S2-X01 остаётся открытым.

FU-2026-10-11-001 сохраняет остаток сверки доменной очереди/metadata/fixture и зависимостей. Фактическая БД не опрашивалась; наличие seed L-003 не доказывает её состояние в старом volume. SIM-EVID-001 не является позиционным evidence L-003.

FU-2026-10-13-004 включает реализацию новых recovery-уточнений, evaluator, restart, архив/удержания и доступ. Сохраняются SIM-UGIS-POS-001 и SIM-UGIS-RET-001; автоочистка не включается. Исследование и сценарная матрица не доказывают успешную runtime-приёмку.

Исходные broad vendor/market утверждения с невоспроизводимыми ссылками не признаны подтверждёнными; их проверка остаётся в FU-2026-06-01-002. Конфликт lint с неизменяемыми RAW — FU-2026-06-01-004.

## Следующее действие

Решений пользователя для текущей синхронизации не требуется. Открытые вопросы относятся к сверке технических источников и реализации, а не к поиску реальных сотрудников или регламентов.

Сверить два вопроса metadata/fixture по техническим источникам и при необходимости фактической БД, затем актуализировать доменную очередь. Отдельной задачей уточнить остаток S2-X01 с учётом подключённых controls и отчёта M4: продолжение после потери доступа, переход на другой наряд при незавершённом recovery, сравнение/перенос отклонённой попытки. Обычный ingest без параметров сейчас не требуется.
