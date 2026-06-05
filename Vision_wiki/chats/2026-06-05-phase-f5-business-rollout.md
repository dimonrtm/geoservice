---
title: Ф5 Бизнес-Модель И Внедрение
type: session
status: draft
created: 2026-06-05
updated: 2026-06-05
source: "user answers to /discover --phase Ф5, 2026-06-05"
tags: [discovery, phase-f5, rollout, business-model, demo]
---

# Ф5 Бизнес-Модель И Внедрение

## Контекст

Ф5 уточняет внедрение и бизнес-модель после Ф4 demo-scope. Для GeoService сейчас нет внешнего заказчика или бюджетного decision maker: первый принимающий решение - владелец pet-проекта. Поэтому Ф5 фиксирует rollout как локальное developer demo, а не commercial go-to-market.

## Ответы Ф5

| Вопрос | Ответ |
|---|---|
| Кто принимает решение | Владелец pet-проекта. |
| Формат первого rollout | Локальное demo. |
| Первый пользователь demo | Разработчик. |
| Объяснение пользы | Показать на demo, что pipeline действительно стал проще. |
| ROI / польза без денег | `learning value`. |
| Роли для первого внедрения | `Editor`, `Reviewer`. |
| Данные | Demo должно запускаться полностью на synthetic dataset, без реальных данных и внешних сервисов. |
| Нужные интеграции | `PostGIS seed`, `auth`, `import GeoJSON`. |
| Не нужны | External GIS, `ArcGIS`/`QGIS` export, CI demo data reset. |
| Самый дорогой риск внедрения | Непонятный UI conflict review. |
| Поддержка после запуска | README, seed/reset script, demo сценарий, troubleshooting. |
| Техническое место запуска | Local Docker Compose. |
| Ограничения по времени | Особых ограничений нет. |
| Первый audience-specific сценарий | Показать `Editor flow`. |

## Что Не Обещать В Demo

Чтобы demo не превратилось в production utility network platform, нельзя обещать:

- замену `ArcGIS Enterprise + Utility Network`;
- production-grade branch versioning;
- полноценный topology engine или trace engine;
- работу с реальными utility data;
- hosted/SaaS rollout;
- enterprise ACL, compliance и audit guarantees;
- offline sync, CRDT/OT или multi-site collaboration;
- интеграции с external GIS и export в `ArcGIS`/`QGIS`;
- доказанный business ROI для внешнего заказчика.

Корректная формулировка обещания: GeoService показывает локальный developer demo, где `Editor` проходит более понятный pipeline сетевой правки, а conflict review становится проще для понимания и проверки.

## Follow-up'ы Для Ф6

- Зафиксировать NFR для local Docker Compose demo: startup time, resetability, seed reproducibility, browser/backend requirements.
- Уточнить минимальные security/access requirements для `Editor`/`Reviewer` в demo.
- Определить объем synthetic data и допустимые performance expectations.
- Зафиксировать observability/troubleshooting minimum: logs, errors, demo script checkpoints.
- Уточнить, нужен ли `import GeoJSON` в первом walking skeleton или может быть Next после seed.

## Связи

- [[../concepts/lean_canvas]]
- [[../solution/roadmap]]
- [[../decisions/risk_assumption_log]]
- [[../decisions/constraints]]
- [[../decisions/followups/index]]
- [[2026-06-04-phase-f4-solution-scope]]
- [[2026-06-05-utility-gis-editor-walking-skeleton-and-dataset]]
