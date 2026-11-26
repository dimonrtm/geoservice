---
title: Network Association
type: entity
status: active
created: 2026-06-24
updated: 2026-11-26
source: "RAW_inputs/documents/utility_gis_editor_domain_dictionary.md; docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md; RAW_inputs/meetings/persisted_edit_slice_EditVersion.md; RAW_inputs/documents/2026-11-26-field-evidence-answers.md; RAW_inputs/documents/2026-11-26-field-evidence-analysis.md"
tags: [domain-knowledge, entity, utility-network, association]
confidence: high
related: [Wiki/entities/network_feature, Wiki/entities/feeder, DDD_Wiki/bounded_contexts/utility_network]
---

# Network Association

## Identity

`NetworkAssociation` имеет стабильный `id`, `fromFeatureId`, `toFeatureId` и `associationType`.

## Lifecycle

Association входит в workspace только если оба endpoint feature попали в рабочую область.

## Responsibilities

Представляет nonspatial направленную связь между двумя `NetworkFeature`: connectivity, containment или attachment.

## Invariants

Association не ссылается на отсутствующий feature, а оба endpoint принадлежат тому же `Feeder`, что и association.

First persisted edit slice не меняет `NetworkAssociation` и не двигает endpoints линии; association mutation остается отдельным downstream rule set.

## На каком уровне различима связь

В наряде на исправление связи редактор указывает, какие именно окончания различает авторитетная запись. Пара кабельных объектов А–Б может остаться прежней при изменении сварки с А7–Б7 на А7–Б8. В таком случае подробное исправление принимает держатель инженерной ведомости. GeoService связывает его принятую редакцию с нарядом и представлением кабелей. Проверяющий воспроизводит изменение пути по ведомости для указанных окончаний. Основание для изменения связи между самими кабелями проверяют отдельно. [[RAW_inputs/documents/2026-11-26-field-evidence-answers#DISC-2026-11-26-01]], [[DDD_Wiki/use_cases/correct_recorded_network_connection]].
