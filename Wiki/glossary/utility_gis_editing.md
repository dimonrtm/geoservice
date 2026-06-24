---
title: Utility GIS Editing
type: glossary
status: active
created: 2026-06-24
updated: 2026-06-24
source: "RAW_inputs/documents/utility_gis_editor_domain_dictionary.md; Vision_wiki/concepts/utility_gis_editing_domain.md"
tags: [domain-knowledge, glossary, utility-network]
confidence: high
related: [DDD_Wiki/subdomains/utility_authoritative_editing, DDD_Wiki/bounded_contexts/work_order]
---

# Utility GIS Editing

`Utility GIS editing` - управляемое изменение инженерной сети через рабочие версии, проверки сетевых правил, обнаружение конфликтов и контролируемую публикацию в authoritative state.

Это не CRUD по геометрии карты: изменение geometry, attributes или association может нарушить connectivity, trace, topology, downstream use или trust к authoritative layer.

## Language Boundary

Канонический workflow: `WorkOrder` -> `EditVersion` -> editing -> validation -> reconcile -> conflict resolution -> review -> post -> audit.

См. [[DDD_Wiki/use_cases/utility_editor_workflow]] и [[DDD_Wiki/invariants/release1_safety_invariants]].
