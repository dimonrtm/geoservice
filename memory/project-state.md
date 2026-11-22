---
title: Состояние Проекта GeoService
type: state
status: active
created: 2026-05-30
updated: 2026-11-22
source: null
tags: [project-state, geoservice]
---

# Состояние Проекта GeoService

## Живое состояние

Последний `/sync-vision` — 2026-11-21 23:51 +05:00 (Asia/Qyzylorda).

GeoService моделирует условную организацию через экспертную персону `expert_repson`. Доменные решения хранятся в Wiki и DDD_Wiki, их источники — в RAW и Vision, сведения о реализации — в Code_wiki. [Режим работы](../docs/agent-memory/decisions/2026-10-13-simulated-domain-organization.md).

- Все 64 RAW обработаны. Последний `/ingest` от 22.11.2026 включил исследование по 101 документу и 15 ответов. В реестре 61 вопрос со статусом `answered`, открытых нет. [[../RAW_inputs/index]], [[Wiki/_registry/questions#Обзор всей доменной модели — 21 ноября]].
- Открыты 20 follow-up’ов. Канонических конфликтов в активном статусе нет. В Vision остаётся один активный конфликт о старом Release 1. [[../Vision_wiki/decisions/followups/index]], [[../Wiki/_registry/conflicts]], [[../Vision_wiki/decisions/conflicts/2026-06-11-old-release-1-vs-utility-workflow]].
- Пять страниц помечены `stale`. Четыре технических описания перечислены в [[../Code_wiki/index#Свежие Repository-Change Знания]]. В [[../DDD_Wiki/context_map/geoservice_context_map]] устарел статус разграничения Reviewer/Publisher. Действующее решение — [[../Wiki/conflicts/2026-06-24-reviewer-vs-publisher]].
- Wiki-lint от 21.11.2026 обнаружил 37 известных `missing_frontmatter` в исходных RAW Markdown. Расхождение между требованиями линтера и неизменяемостью источников отслеживает FU-2026-06-01-004.

## Требует внимания

Сохранение одной внутренней вершины линии, чтение результата и восстановление отправленной команды реализованы. Проверка metadata/fixture относится к локальной revision 49. Статус `POSITIONAL_ACCURACY_UNVERIFIED` блокирует передачу на review. Путь от оценки позиционных доказательств до пакета, review и simulated post, а также restart, удержания, отзыв, коррекция и координация зависимых нарядов остаются в технической очереди FU-2026-10-13-004. [[../DDD_Wiki/model_health#Current Sprint Planning Queue]].

## Следующее действие

Для четырёх технических страниц нужен `/ingest repository-change` по FU-2026-11-21-001. Актуализация карты контекстов ведётся отдельно в FU-2026-11-21-002. [[../Vision_wiki/decisions/followups/index]].

Следующее доменное действие — `/discover` по всей модели и её межконтекстным связям. При отборе свериться с 15 принятыми решениями от 22.11.2026 и прежними ответами о физических преобразованиях и зависимых нарядах. [[DDD_Wiki/use_cases/reconcile_field_and_inventory_records]], [[../DDD_Wiki/model_health#Current Discovery Queue]].
