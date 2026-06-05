---
title: Utility GIS Editor Walking Skeleton And Dataset
type: session
status: draft
created: 2026-06-05
updated: 2026-06-05
source: RAW_inputs/documents/utility_gis_editor_walking_skeleton_and_dataset.md
tags: [ingest, utility-network, walking-skeleton, dataset, phase-f4]
---

# Utility GIS Editor Walking Skeleton And Dataset

## Контекст Источника

Источник уточняет Ф4 demo-scope для `Utility GIS editor`: как должен выглядеть walking skeleton от login до authoritative state и какой минимальный synthetic utility dataset нужен, чтобы сценарий был маленьким, но не игрушечным.

## Главные Тезисы

- Walking skeleton должен доказывать полный поток `Login -> Work order -> Edit version -> Network edit -> Save change set -> Validate topology -> Reconcile with Default -> Resolve conflict -> Reviewer approve -> Post to Default -> Authoritative state updated`.
- Главный риск сценария: параллельная правка инженерной сети не должна теряться молча, а authoritative state должен обновляться только после validation, reconcile и approve.
- Минимальная предметная модель: `User`, `Role`, `WorkOrder`, `NetworkVersion`, `NetworkFeature`, `NetworkAssociation`, `ChangeSet`, `Conflict`, `ValidationIssue`, `AuthoritativeSnapshot`, `AuditLog`.
- Минимальные роли: `Utility GIS editor`, `Reviewer`, `Admin`, `Read-only consumer`.
- Для skeleton достаточно demo-validation правил: orphan device, line endpoints, distance/association validity, junction delete guard, unresolved dirty areas / validation issues before post.
- Conflict view должен показывать `Base`, `Mine`, `Default` и варианты решения: `Use my version`, `Use Default version`, `Manual merge`.
- Минимальный frontend: `Login`, `My work orders`, `Map editor`, `Reconcile/conflict view`, `Review/post result`.

## Synthetic Utility Dataset

Рекомендуемый dataset называется `synthetic_utility_feeder_01` и моделирует маленький electric feeder.

| Область | Минимум |
|---|---:|
| Service area / AOI | 1 |
| Subnetwork / feeder | 1 |
| Junctions | 7 |
| Line segments | 6 |
| Devices | 6 |
| Associations | 8-10 |
| Work orders | 2 |
| Users | 3 |
| Versions | `Default` + 2 edit versions |
| Conflict-сценарии | 4 |

Ключевые объекты: `J-001..J-007`, `L-001..L-006`, `D-001..D-006`, `A-001..A-010`, `WO-001`, `WO-002`, `alexey.editor`, `bolat.editor`, `marina.reviewer`.

Четыре conflict-сценария: `Update/Update`, `Geometry/Geometry`, `Update/Delete`, `Association conflict`.

## Решения И Ограничения

- Dataset должен быть маленьким по количеству объектов, но настоящим по типам риска: topology, associations, invalid state, parallel editing, conflict detection, review, post, audit trail.
- Не стоит опускаться ниже нижней границы: 1 AOI, 1 feeder, 5 junctions, 4 lines, 4 devices, 6 associations, 2 work orders, 2 editors, 1 reviewer, `Default` + 2 edit versions.
- В первой версии не нужны full utility network topology, trace engine, сложные dirty areas, offline sync, 3D, full version history, bulk edits, advanced geometry diff и полная схема `ArcGIS` branch versioning.

## Технические Следствия

- Desired backend surface для demo: `/auth/login`, `/work-orders/assigned-to-me`, `/work-orders/{workOrderId}/versions`, `/versions/{versionId}/features`, `/versions/{versionId}/associations`, `/versions/{versionId}/validate`, `/versions/{versionId}/reconcile`, `/conflicts/{conflictId}/resolve`, `/versions/{versionId}/submit-review`, `/versions/{versionId}/approve`, `/versions/{versionId}/post`, `/authoritative/features/{featureId}`.
- Desired storage skeleton: `users`, `roles`, `work_orders`, `network_features_default`, `network_associations_default`, `network_versions`, `network_feature_changes`, `network_association_changes`, `validation_issues`, `reconcile_runs`, `conflicts`, `conflict_resolutions`, `audit_log`.
- Working version можно хранить как change-set от `base_version_id`, а не как полную копию сети.

## Связи

- [[../solution/USM]]
- [[../solution/roadmap]]
- [[../solution/architecture_vision]]
- [[../decisions/risk_assumption_log]]
- [[../decisions/followups/index]]
- [[2026-06-04-phase-f4-solution-scope]]
