---
title: Состояние Проекта GeoService
type: state
status: active
created: 2026-05-30
updated: 2026-11-09
source: null
tags: [project-state, geoservice]
---

# Состояние Проекта GeoService

## Живое состояние

GeoService — исследовательский pet-проект. Агент через expert_repson представляет условную организацию; реальные сотрудники, интервью и регламенты не требуются. Внешние факты, решения модели и гипотезы различаются. Режим — [решение](../docs/agent-memory/decisions/2026-10-13-simulated-domain-organization.md).

Канонический слой — Wiki/DDD_Wiki, техническое знание — Code_wiki; Vision_wiki хранит legacy/source summaries. Ближайший срез ограничен persisted edit одной линии/внутренней вершины с immutable baseline и явным POSITIONAL_ACCURACY_UNVERIFIED. Review/post остаётся downstream.

- Последний `/sync-vision`: 2026-11-09 18:47 +05:00 (Asia/Qyzylorda).
- Последний `/ingest`: 2026-11-09 — исследование и ответы об отзыве/коррекции публикации, общий корпус 88 документов (66 новых нормализованных URL); [[../Vision_wiki/chats/2026-11-09-publication-research]] и [[../Vision_wiki/chats/2026-11-09-publication-answers]].
- RAW: 58 источников, все отмечены обработанными в индексе; новых необработанных нет.
- Открыты 18 follow-up’ов; открытых вопросов 0. DISC-2026-11-09-01/02 answered по решениям условной организации. Metadata/fixture отвечены отдельной фактической проверкой. Активных канонических конфликтов 0; legacy-конфликт о старом Release 1 остаётся active.
- Сверка кода 2026-11-09: [[../DDD_Wiki/model_health]] актуален, stale снят; FU-2026-10-11-001 resolved. [Матрица реализации](../docs/verification/2026-11-09-model-health-code-reconciliation.md): first-save/API/UI/recovery существуют, 105 выбранных frontend-тестов прошли; DB/M4 заново не запускались.
- Lint 2026-11-09: 37 известных missing_frontmatter только в неизменяемых RAW Markdown; других замечаний нет.

## Требует внимания

FU-2026-10-11-001 закрыт после сверки кода и технической очереди 09.11.2026. Активная discovery-очередь согласована с реестром: закрытая проверка first-save/metadata/fixture вынесена из её таблицы с основанием. Два вопроса [[../Wiki/_registry/questions]] отвечены для локального экземпляра revision 49. Технические основания: [[../Code_wiki/архитектура/edit_geometry_fixture_metadata]], [[../Code_wiki/архитектура/edit_version_api_readback]] и [[../Code_wiki/архитектура/frontend_save_recovery]]. Фактическая БД проверена 08.11.2026: L-003 имеет три вершины; current/baseline совпадают по всем 19 объектам и 9 связям. [Протокол](../docs/verification/2026-11-08-demo-dataset-runtime-check.md). SIM-EVID-001 не является позиционным evidence L-003.

Текущие технические основания восстановления и доступа — [[../Code_wiki/архитектура/frontend_save_recovery]] и [[../Code_wiki/архитектура/browser_auth_sessions]]. Техническая очередь сверена с ними и [отчётом S2-X01](../docs/sprint_2/2026-10-23-s2-x01-recovery-implementation-report.md): first-save и S2-X01 повторно не планируются. Следующий незавершённый путь — evidence/readiness → package → review/gate → simulated post; фактическая реализация evaluator и публикации отсутствует.

FU-2026-10-13-004 требует сопоставить остальные принятые правила условной организации с реализацией: evaluator, restart, архив/удержания, доступ и принятые правила withdrawal/correction. Завершение S2-X01 не закрывает весь follow-up. Сохраняются SIM-UGIS-POS-001 и SIM-UGIS-RET-001; автоочистка не включается. Ручные процедуры оценки и заключения не доказывают runtime-приёмку.

Исходные broad vendor/market утверждения с невоспроизводимыми ссылками не признаны подтверждёнными; проверка остаётся в FU-2026-06-01-002. Конфликт lint с неизменяемыми RAW — FU-2026-06-01-004.

## Следующее действие

Следующее действие: /discover проверяет покрытие взаимодействия нескольких зависимых нарядов на связанных участках по context map и прежним ответам. Это кандидат направления, не заранее открытые вопросы. DISC-2026-11-09-01/02 закрыты: [[../Wiki/policies/review_package_withdrawal_policy]], [[../Wiki/policies/published_result_correction_policy]]. Не повторять принятые правила из-за отсутствия кода. First-save scope не расширяется. Сверка FU-2026-10-11-001 завершена; реализация остатка FU-2026-10-13-004 ведётся отдельно. Metadata/fixture подтверждены для revision 49; позиционное evidence не получено.

Правила ручной квалификации приняты условной организацией. Обычный `/ingest` без параметров не нужен: все RAW уже обработаны. Решений пользователя для синхронизации не требуется.
