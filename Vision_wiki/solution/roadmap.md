---
title: Roadmap
type: solution
status: active
created: 2026-05-30
updated: 2026-06-23
source: "RAW_inputs/documents/спринт 1.odt; Vision_wiki/chats/2026-06-04-phase-f4-solution-scope.md; RAW_inputs/documents/utility_gis_editor_walking_skeleton_and_dataset.md; Vision_wiki/chats/2026-06-05-phase-f5-business-rollout.md; Vision_wiki/chats/2026-06-06-phase-f6-constraints-and-nfr.md; Vision_wiki/chats/2026-06-07-phase-f7-metrics-and-risks.md; user answers to /discover --phase Ф8, 2026-06-11; RAW_inputs/meetings/geometry_association_conflict_f4.md; RAW_inputs/meetings/geometry_association_conflict_f7.md; RAW_inputs/meetings/geometry_association_conflict_f8.md"
tags: [solution, roadmap, release-1]
---

# Roadmap

Активный roadmap нового Release 1 после Ф8. Старый 14-дневный generic plan ниже сохраняется как исторический foundation, а не текущая продуктовая последовательность.

## Ф8 Release 1 Delivery Order

| Порядок | Vertical Capability | Проверяемый Результат |
|---:|---|---|
| 1 | Code compliance matrix и utility schema | Ясно, что переиспользуется, добавляется и superseded. |
| 2 | Synthetic seed, roles, work orders и edit versions | `Editor` открывает назначенный work order и workspace. |
| 3 | Feature/association change set и validation | Изменения не затрагивают `Default`; critical issue блокирует workflow. |
| 4 | Reconcile, prepared conflict и resolution | Видны `Base / Mine / Default`; unresolved conflict блокирует review. |
| 5 | Reviewer queue, approve/reject и transactional post | Separation of duties соблюдена; safe post меняет `Default`. |
| 6 | Audit, reset/`full-clean`, demo UX и tests | Полный workflow воспроизводим и доказуем. |
| 7 | UX test, conflict drill и benchmark | Проверены comprehension и обязательные safety/performance gates. |

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

## Release 2 Ф4 Demo Roadmap

Этот раздел фиксирует planned next-release demo, а не текущий Release 1.

| Горизонт | Scope | Критерий Готовности |
|---|---|---|
| Now | Canonical transformer terminal association scenario: conflict package, consequence summary, `Normal/High/Critical` routing, stale/failure case и audit object | Demo показывает за 1-2 минуты, меняется ли authoritative network behavior, и предлагает safe next step без полноценной замены native resolve/post workflow |
| Next | Live validation с реальными `Editor`/`Reviewer`, сравнение с `ArcGIS native + SOP + expert handoff`, проверка language/UI comprehension | Измерены external trace/check opens, notes/screenshots, handoff и time-to-confident-decision |
| Later | `Simple` tier, batch review, SLA queue, dual-control workflow и production-grade utility rules | Возвращаться только после validation, что consequence package реально снижает uncertainty и не создает false-safe decisions |

## Release 2 Ф7 Experiment Roadmap

Этот раздел фиксирует порядок проверки consequence package после Ф7. Он не
создает внешний product claim до реальных `Editor`/`Reviewer`.

| Порядок | Эксперимент | Критерий |
|---:|---|---|
| 1 | Scripted golden walkthrough canonical transformer terminal case | Package объясняет network consequence, affected path, association delta, dirty/validation state, subnetwork status и safe next step за 1-2 минуты scripted review. |
| 2 | 10 deterministic repeats canonical scenario | `contract readiness pass rate` проходит по package build, evidence completeness, blocker detection, stale detection и audit completeness; `false-safe verdict count = 0`. |
| 3 | 10 mutated stale / blocker / pre-post failure variants | Previous package/approval становится stale, `post` blocked, пользователь видит reason/delta, repeat review идет от нового delta-context; false-block не появляется на clean native state. |
| 4 | Optional 30 automated runs | Проверена стабильность package build, blocker detection, P95 и run-data schema для developer confidence. |
| 5 | Manual baseline и user validation | Сравнить с `ArcGIS native Conflicts view + SOP + expert handoff`; реальные `Editor`/`Reviewer` проверяют risk tier, evidence sufficiency, blocker trust, sample review для `Normal`, specialist escalation и audit usefulness. |

Course-change criteria: package не объясняет consequence за 1-2 минуты, человек
сразу уходит во внешний GIS или expert handoff, blockers не воспроизводятся из
authoritative state, audit не помогает repeat review после stale или появляется
хотя бы один false-safe на hard-block case.

## Release 2 Ф8 Closeout Roadmap

Этот раздел фиксирует следующий план после закрытия discovery Ф1-Ф8 по
`geometry/association conflict`.

| Порядок | Артефакт / шаг | Критерий |
|---:|---|---|
| 1 | Implementation contract v0.1 | ADR-style Markdown contract с machine-readable appendices: scope, actors, states, events, package schema, audit schema, blockers, stale rules, non-goals, acceptance gates, API/events, fixture manifest, P95 targets и observability fields. |
| 2 | Canonical walking skeleton | Один transformer/service-device association case плюс stale/pre-post failure sidecar; computed evidence, hard blockers, `approve package` / `can post` и audit object воспроизводимы. |
| 3 | Real validation mini-round | Отдельный checklist с `Editor`/`Reviewer` проверяет risk wording, authority matrix, sample review для `Normal`, evidence sufficiency, repeat-review UX и trust к blocker verdict. |

Первый implementation contract не должен включать новый topology engine, full
ArcGIS parity, full in-product conflict editing UI, batch review/SLA routing,
production-grade on-prem hardening или claims про authoritative-safe `post` без
real validation.

## Источники

- `RAW_inputs/documents/спринт 1.odt`
- `Vision_wiki/chats/2026-06-04-phase-f4-solution-scope.md`
- `Vision_wiki/chats/2026-06-05-phase-f5-business-rollout.md`
- `Vision_wiki/chats/2026-06-06-phase-f6-constraints-and-nfr.md`
- `RAW_inputs/documents/utility_gis_editor_walking_skeleton_and_dataset.md`
- `Vision_wiki/chats/2026-06-07-phase-f7-metrics-and-risks.md`
- `Vision_wiki/chats/2026-06-20-geometry-association-conflict-f4.md`
- `Vision_wiki/chats/2026-06-23-geometry-association-conflict-f7.md`
- `Vision_wiki/chats/2026-06-23-geometry-association-conflict-f8.md`
- [[USM]]
- [[../concepts/first_release_mvp]]
- [[../decisions/release_1_utility_workflow]]
- [[../chats/2026-06-11-phase-f8-release-1-closeout]]
