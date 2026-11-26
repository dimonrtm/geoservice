---
title: Состояние Проекта GeoService
type: state
status: active
created: 2026-05-30
updated: 2026-11-24
source: null
tags: [project-state, geoservice]
---

# Состояние Проекта GeoService

## Живое состояние

Последний `/sync-vision` — 2026-11-24 22:05 +05:00 (Asia/Qyzylorda).

GeoService моделирует условную организацию через экспертную персону `expert_repson`. Доменные решения хранятся в Wiki и DDD_Wiki, их источники — в RAW и Vision, сведения о реализации — в Code_wiki. [Режим работы](../docs/agent-memory/decisions/2026-10-13-simulated-domain-organization.md).

- Все 69 RAW обработаны. В реестре 76 отвеченных вопросов, открытых нет. [[../RAW_inputs/index]], [[Wiki/_registry/questions#Обзор всей доменной модели — 24 ноября]], [[DDD_Wiki/model_health#Current Discovery Queue]].
- Открыты 20 follow-up’ов. Канонических конфликтов в активном статусе нет. В Vision остаётся один активный конфликт о старом Release 1. [[../Vision_wiki/decisions/followups/index]], [[../Wiki/_registry/conflicts]], [[../Vision_wiki/decisions/conflicts/2026-06-11-old-release-1-vs-utility-workflow]].
- Пять страниц помечены `stale`. Четыре технических описания перечислены в [[../Code_wiki/index#Свежие Repository-Change Знания]]. В [[../DDD_Wiki/context_map/geoservice_context_map]] устарел статус разграничения Reviewer/Publisher. Действующее решение — [[../Wiki/conflicts/2026-06-24-reviewer-vs-publisher]].
- Wiki-lint от 24.11.2026 обнаружил 36 известных `missing_frontmatter` в исходных RAW Markdown. Расхождение между требованиями линтера и неизменяемостью источников отслеживает FU-2026-06-01-004.

- В каталоге DDD 20 самостоятельных сценариев. По 18 кандидатам из практики операторов зафиксированы девять принятых сценариев, три варианта, два отложенных предложения и четыре задачи смежных служб. [Решения и основания](../DDD_Wiki/use_cases/candidates/_info.md).

## Требует внимания

Текущая продуктовая очередь начинается с полного редактирования рабочей сети. Позиционное доказательство для L-003 понадобится при переходе к review. Пакет и публикация следуют после приёмки редактора. [Очередь реализации](../DDD_Wiki/model_health.md#current-sprint-planning-queue).

## Следующее действие

Ближайшая задача для разработки — сохранить в одной рабочей версии изменения двух линий, повторно открыть наряд и откатить одну правку с сохранением другой. Далее — геометрия без учебных лимитов, полный цикл объектов и атрибутов, редактирование соединений и сквозная приёмка. [План редактора и проверочные примеры](../docs/planning/network-editor-backlog.md).

Для четырёх технических страниц нужен `/ingest repository-change` по FU-2026-11-21-001. В описании backend сверить в том числе сборку зависимостей WebSocket после B4. В карте контекстов исправить статус границы Reviewer/Publisher по FU-2026-11-21-002. [[../Code_wiki/index#Свежие Repository-Change Знания]], [[../Vision_wiki/decisions/followups/index]].

При следующем `/discover` выбирать новые доменные развилки с учётом решений по DISC-2026-11-24-01…15. [[Wiki/_registry/questions#Обзор всей доменной модели — 24 ноября]], [[DDD_Wiki/model_health#Current Discovery Queue]].
