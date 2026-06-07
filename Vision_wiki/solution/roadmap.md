---
title: Roadmap
type: solution
status: active
created: 2026-05-30
updated: 2026-06-07
source: "RAW_inputs/documents/спринт 1.odt; Vision_wiki/chats/2026-06-04-phase-f4-solution-scope.md; RAW_inputs/documents/utility_gis_editor_walking_skeleton_and_dataset.md; Vision_wiki/chats/2026-06-05-phase-f5-business-rollout.md; Vision_wiki/chats/2026-06-06-phase-f6-constraints-and-nfr.md; Vision_wiki/chats/2026-06-07-phase-f7-metrics-and-risks.md"
tags: [solution, roadmap, release-1]
---

# Roadmap

Roadmap извлечен из 14-дневного Release 1 source document. Он отражает план источника, а не факт завершения работ.

## Now

| Направление | Почему Сейчас | Критерий Готовности |
|---|---|---|
| Days 1-2: требования и acceptance criteria | Сначала зафиксировать scope совместного редактирования и API baseline | PRD v1.0, Release Backlog, DoD, criteria для login, bbox, edit, realtime, conflicts. |
| Days 3-4: skeleton, migrations, CI/dev env | Нужен воспроизводимый vertical slice и guardrails | Модульная структура backend/frontend, Alembic, Docker Compose, lint/test/build/smoke commands. |
| Days 5-7: auth, geodata model, map loading | Подготовить чтение данных на карте | JWT/dev login, roles, layers/features endpoints, GiST, MapLibre bbox loading. |
| Days 8-10: edit, realtime, conflicts | Главная ценность Release 1 - совместное редактирование | Один пользователь редактирует; два клиента получают WebSocket events; `409` не допускает silent overwrite. |

## Next

| Направление | Зависимости | Что Нужно Проверить |
|---|---|---|
| Days 11-12: history, observability, small analytics, 3D demo | Стабильный edit/realtime contract | Достаточность audit log, request id, PostGIS operations, минимального 3D value demo. |
| Day 13: packaging, tests, docs | Готовый vertical slice | CRUD tests, `409` test, WS test, frontend smoke, run docs, API docs, WS protocol docs. |
| Day 14: review, retro, backlog следующего релиза | Проходящий demo script | Acceptance criteria отмечены, известны ограничения MVP и backlog следующего релиза. |

## Later

| Направление | Условие Возврата | Примечания |
|---|---|---|
| CRDT/OT или advanced locking | Когда optimistic concurrency перестанет хватать | Явно non-goal Release 1. |
| Offline mode / sync later | Когда появится validated need для offline workflow | Явно non-goal Release 1. |
| Rich permissions ACL | Когда нужны права глубже `Viewer`/`Editor` | Release 1 держит только две роли. |
| Large imports и форматы SHP/GeoPackage | Когда нужен production import pipeline | Release 1 import ограничен SYNC GeoJSON <=20MB. |
| Полноценная модель Projects/Layers | Когда потребуется масштабирование на проекты и устойчивое управление слоями | В Release 1 может быть registry/simple table без breaking API. |

## Ф4 Demo Roadmap

Этот раздел уточняет product-scope после Ф4 и не отменяет технический Release 1 source plan выше.

| Горизонт | Scope | Критерий Готовности |
|---|---|---|
| Now | Demo focused conflict/review layer для `Utility GIS editor`: work order, working version, change set, demo validation, compare with `Default`, conflict explanation, reviewer decision, publish to authoritative layer | Walking skeleton доказывает безопасную публикацию сетевой правки без silent overwrite; `Reviewer` видит объяснение конфликта и принимает решение; dataset `synthetic_utility_feeder_01` воспроизводит `Update/Update`, `Geometry/Geometry`, `Update/Delete`, `Association conflict` |
| Next | Второй сценарий `edit after reconcile`, расширение synthetic conflict library, compact audit/review UX, улучшение demo-script | Сценарий воспроизводится без закрытых данных, использует audit trail и не требует production topology engine |
| Later | Full branch versioning, topology engine, offline sync, CRDT/OT, rich ACL, production utility network model | Возвращаться только после подтверждения ценности focused demo |

Scope creep сигнал: появление новых незапланированных на релиз фич.

## Ф5 Rollout Roadmap

Этот раздел фиксирует внедрение первого demo, а не коммерческий go-to-market.

| Горизонт | Scope | Критерий Готовности |
|---|---|---|
| Now | Локальное developer demo через Docker Compose: `Editor flow`, `PostGIS seed`, JWT `auth`, `import GeoJSON`, synthetic dataset, README, seed/reset/`full-clean` scripts, demo сценарий, troubleshooting и observability minimum | Разработчик может локально запустить demo и увидеть, что pipeline сетевой правки стал проще и понятнее |
| Next | `Reviewer` decision flow и polish conflict review UI | Conflict review UI не вызывает когнитивного провала и поддерживает Ф4 promise |
| Later | Hosted demo, CI demo data reset, external GIS integrations, `ArcGIS`/`QGIS` export, production deployment story | Возвращаться только после стабильного local demo |

Главный rollout-риск Ф5: непонятный UI conflict review.

## Ф7 Validation Roadmap

| Порядок | Эксперимент | Критерий |
|---:|---|---|
| 1 | Workflow prototype | 3-5 представителей роли понимают Save/Post, edit version/`Default` и момент authoritative state. |
| 2 | Validation trap test | Обнаружено >=80% подготовленных ошибок; 100% critical errors блокируют post. |
| 3 | Two-editors conflict drill | 100% подготовленных conflicts обнаружены; silent overwrite невозможен; stale post сохраняет edits и требует reconcile. |
| 4 | Manual baseline | 10-20 work orders low/medium/high измерены по времени, errors, returns, rework и touch count. |
| 5 | Product evaluation | 200 started work orders, `Safe Authoritative Post Rate >=95%`, 7-дневное окно и абсолютный veto safety blockers. |

## Источники

- `RAW_inputs/documents/спринт 1.odt`
- `Vision_wiki/chats/2026-06-04-phase-f4-solution-scope.md`
- `Vision_wiki/chats/2026-06-05-phase-f5-business-rollout.md`
- `Vision_wiki/chats/2026-06-06-phase-f6-constraints-and-nfr.md`
- `RAW_inputs/documents/utility_gis_editor_walking_skeleton_and_dataset.md`
- `Vision_wiki/chats/2026-06-07-phase-f7-metrics-and-risks.md`
- [[USM]]
- [[../concepts/first_release_mvp]]
