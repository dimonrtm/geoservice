# Sprint 1 Day 7 Documentation Reserve Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Do not create a git commit unless the user explicitly asks for it after review.

**Goal:** Execute the accepted Day 7 documentation-and-reserve design by producing a concrete Sprint 1 baseline audit before `EditVersion` work begins.

**Architecture:** This is a documentation-only implementation. It creates a focused audit result document, updates the Sprint 1 README, and verifies that Day 7 did not introduce production code, migrations, API, frontend, or `EditVersion` scope.

**Tech Stack:** Markdown, PowerShell, ripgrep, existing Sprint 1 documentation.

---

## File Structure

- Create: `docs/release_1/sprint_1/2026-06-19-sprint-1-day-7-documentation-reserve-audit.md` - final audit result for contracts, data model, tests, blockers, and Day 8 prerequisites.
- Modify: `docs/release_1/sprint_1/README.md` - add links to the Day 7 implementation plan and audit result.
- Existing source: `docs/release_1/sprint_1/2026-06-19-sprint-1-day-7-documentation-reserve-design.md` - accepted design/spec for Day 7.

## Task 1: Verify Audit Sources

**Files:**
- Read: `docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-acceptance-design.md`
- Read: `docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-api-contract-design.md`
- Read: `docs/release_1/sprint_1/2026-06-13-sprint-1-day-2-roles-access-design.md`
- Read: `docs/release_1/sprint_1/2026-06-14-sprint-1-day-3-network-model-design.md`
- Read: `docs/release_1/sprint_1/2026-06-15-sprint-1-day-4-utility-dataset-design.md`
- Read: `docs/release_1/sprint_1/2026-06-17-sprint-1-day-5-work-orders-design.md`
- Read: `docs/release_1/sprint_1/2026-06-18-sprint-1-day-6-integration-check-design.md`
- Inspect: `apps/backend/scripts/start_utility_service.sh`
- Inspect: `apps/backend/seeds/specs/seed_work_order_specs.py`
- Inspect: `apps/backend/utility_service/use_cases/services/work_order_service.py`
- Inspect: `apps/backend/tests/integration_tests/test_work_order_seed_chain_integration.py`

- [ ] **Step 1: Search current docs and code for Day 7 audit anchors**

Run from repo root:

```powershell
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new(); rg -n "WO-001|synthetic_utility_feeder_01|alexey.editor|marina.reviewer|seed_work_orders|WORK_ORDER_NOT_ASSIGNED|WORK_ORDER_STATE_CONFLICT|EditVersion|legacy-generic-plan" docs\release_1\sprint_1 apps\backend
```

Expected: matches show the current Sprint 1 documents, work order seed, startup script, work order service/tests, and historical `legacy-generic-plan` references. No edits are made in this step.

- [ ] **Step 2: Confirm Day 6 startup chain includes work orders**

Run from repo root:

```powershell
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new(); rg -n "seed_demo_users|seed_utility_dataset|seed_work_orders|uvicorn" apps\backend\scripts\start_utility_service.sh apps\backend\tests\test_compose_startup_contract.py
```

Expected: both files show `seed_work_orders` after `seed_utility_dataset` and before `uvicorn`.

## Task 2: Write Day 7 Audit Result

**Files:**
- Create: `docs/release_1/sprint_1/2026-06-19-sprint-1-day-7-documentation-reserve-audit.md`

- [ ] **Step 1: Create audit result document**

Create the audit document with these sections:

```markdown
# Спринт 1, День 7: Результат Сверки Документации И Резерва

Дата: 2026-06-19
Статус: выполнено
Расположение: `docs/release_1/sprint_1`

## Назначение

...
```

The document must include:

- contract alignment table for Acceptance, API, Roles, Network Data, Work Orders, Integration;
- data baseline before Day 8;
- test baseline grouped by unit, metadata, integration smoke, sprint acceptance;
- blocker decision table;
- explicit statement that `legacy-generic-plan/day-7-plan.md` is historical and not active;
- explicit statement that no production code, migrations, public API, frontend, or `EditVersion` were added by Day 7.

- [ ] **Step 2: Check audit document for draft markers**

Run from repo root:

```powershell
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new(); rg -n "TBD|TODO|FIXME|заглуш|уточнить позже|implement later" docs\release_1\sprint_1\2026-06-19-sprint-1-day-7-documentation-reserve-audit.md
```

Expected: no matches.

## Task 3: Update Sprint README

**Files:**
- Modify: `docs/release_1/sprint_1/README.md`

- [ ] **Step 1: Add Day 7 execution links**

Add these links immediately after the Day 7 design link:

```markdown
- [План реализации документации и резерва Дня 7](2026-06-19-sprint-1-day-7-documentation-reserve-implementation-plan.md)
- [Результат сверки документации и резерва Дня 7](2026-06-19-sprint-1-day-7-documentation-reserve-audit.md)
```

- [ ] **Step 2: Verify all Day 7 link targets exist**

Run from repo root:

```powershell
Test-Path docs\release_1\sprint_1\2026-06-19-sprint-1-day-7-documentation-reserve-design.md
Test-Path docs\release_1\sprint_1\2026-06-19-sprint-1-day-7-documentation-reserve-implementation-plan.md
Test-Path docs\release_1\sprint_1\2026-06-19-sprint-1-day-7-documentation-reserve-audit.md
```

Expected:

```text
True
True
True
```

## Task 4: Final Verification

**Files:**
- No additional file edits.

- [ ] **Step 1: Verify Day 7 result files do not claim forbidden scope**

Run from repo root:

```powershell
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new(); rg -n "production-код добавлен|migration добавлена|endpoint добавлен|frontend добавлен|EditVersion реализован" docs\release_1\sprint_1\2026-06-19-sprint-1-day-7-documentation-reserve-design.md docs\release_1\sprint_1\2026-06-19-sprint-1-day-7-documentation-reserve-audit.md
```

Expected: no matches.

- [ ] **Step 2: Verify no code/config files changed by Day 7 implementation**

Run from repo root:

```powershell
git diff --name-only -- apps infra .github
```

Expected: no output from this Day 7 implementation.

- [ ] **Step 3: Check repository status**

Run from repo root:

```powershell
git status --short
```

Expected: modified or added Sprint 1 docs are visible; unrelated `.obsidian/graph.json` may remain present if it was already changed by the user. Do not stage or commit unless explicitly requested.

## Self-Review

- Spec coverage: Tasks 1-3 implement the accepted Day 7 design by verifying sources, writing an audit result, linking it from README, and keeping forbidden scope out.
- Placeholder scan: The audit result check rejects `TBD`, `TODO`, `FIXME`, `заглуш`, `уточнить позже`, and `implement later`.
- Scope check: The plan creates Markdown documentation only and explicitly verifies that no code, migrations, public API, frontend, or `EditVersion` were added.
