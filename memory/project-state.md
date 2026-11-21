---
title: Состояние Проекта GeoService
type: state
status: active
created: 2026-05-30
updated: 2026-11-21
source: null
tags: [project-state, geoservice]
---

# Состояние Проекта GeoService

## Живое состояние

Последний `/sync-vision` — 2026-11-21 19:48 +05:00 (Asia/Qyzylorda).

GeoService моделирует условную организацию через экспертную персону `expert_repson`. Доменные решения хранятся в Wiki и DDD_Wiki, их источники — в RAW и Vision, сведения о реализации — в Code_wiki. [Режим работы](../docs/agent-memory/decisions/2026-10-13-simulated-domain-organization.md).

- Все 62 RAW обработаны. Последний `/ingest` от 21.11.2026 связал исследование по 102 документам и три ответа об активах с канонической моделью. В реестре открытых доменных вопросов нет. [[Vision_wiki/chats/2026-11-21-asset-lifecycle-research]], [[Vision_wiki/chats/2026-11-21-asset-lifecycle-answers]], [[../Wiki/_registry/questions]].
- Открыты 20 follow-up’ов. Канонических конфликтов в активном статусе нет. В Vision остаётся один активный конфликт о старом Release 1. [[../Vision_wiki/decisions/followups/index]], [[../Wiki/_registry/conflicts]], [[../Vision_wiki/decisions/conflicts/2026-06-11-old-release-1-vs-utility-workflow]].
- Пять страниц помечены `stale`. Четыре технических описания перечислены в [[../Code_wiki/index#Свежие Repository-Change Знания]]. В [[../DDD_Wiki/context_map/geoservice_context_map]] устарел статус разграничения Reviewer/Publisher. Действующее решение — [[../Wiki/conflicts/2026-06-24-reviewer-vs-publisher]].
- Wiki-lint от 21.11.2026 обнаружил 37 известных `missing_frontmatter` в исходных RAW Markdown. Расхождение между требованиями линтера и неизменяемостью источников отслеживает FU-2026-06-01-004.

## Требует внимания

Сохранение одной внутренней вершины линии, чтение результата и восстановление отправленной команды реализованы. Проверка metadata/fixture относится к локальной revision 49. Статус `POSITIONAL_ACCURACY_UNVERIFIED` блокирует передачу на review. Путь от оценки позиционных доказательств до пакета, review и simulated post, а также restart, удержания, отзыв, коррекция и координация зависимых нарядов остаются в технической очереди FU-2026-10-13-004. [[../DDD_Wiki/model_health#Current Sprint Planning Queue]].

## Следующее действие

Для технической wiki нужен `/ingest repository-change` по FU-2026-11-21-001. Отдельная редакционная задача FU-2026-11-21-002 относится к карте контекстов. Новых RAW для обычного `/ingest` нет.

Следующее доменное действие — `/discover` по соседнему процессу передачи ответственности за ведение данных без физической замены участка. Сначала проверить новизну по прежним решениям о полномочиях, передаче обязанностей и приёмке. Ответы об установках, происхождении участков и предмете наряда уже приняты. [[DDD_Wiki/use_cases/record_physical_asset_change]], [[../DDD_Wiki/model_health#Current Discovery Queue]].
