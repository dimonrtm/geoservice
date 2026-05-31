---
title: Testing Strategy
type: note
status: active
created: 2026-05-30
updated: 2026-05-30
source: repository-snapshot:2026-05-30
tags: [testing, backend, frontend, quality]
---

# Testing Strategy

В репозитории есть backend pytest suite, frontend Vitest suite и отдельные тесты knowledge-pipeline scripts.

## Backend Tests

Backend tests находятся в `apps/backend/app/tests`.

Покрытые области:

- auth service, password service и demo user seed;
- settings security validation;
- bbox validation;
- exception handlers;
- feature service CRUD/version behavior;
- feature realtime publisher;
- websocket auth, websocket role checks и layer websocket endpoint;
- realtime connection manager.

## Frontend Tests

Frontend tests находятся рядом с TypeScript modules:

- `stores/auth.test.ts`
- `stores/edit.test.ts`
- `contracts/geojson.test.ts`
- `contracts/realtime.test.ts`
- `map/feature-grid.test.ts`
- `composables/map/useFeatureTileCache.test.ts`
- `composables/map/useLayerRealtime.test.ts`

Тесты покрывают contract guards, auth/edit stores, feature grid/tile cache и realtime reconnect/event parsing.

## Pipeline Tests

Scripts tests лежат в `scripts/tests`:

- `test_lint_wiki.py`
- `test_check_memory_needed.py`

Они защищают wiki frontmatter/wikilinks и правило обязательной agent memory для durable process changes.

## Команды

Backend:

```powershell
cd apps/backend/app
pytest
black --check .
ruff check .
```

Frontend:

```powershell
cd apps/frontend
npm run format:check
npm run lint
npm run typecheck
npm test
npm run build
```

Wiki:

```powershell
python scripts/lint-wiki.py --root .
python scripts/check-memory-needed.py --check
```

## Связанные Ноды

- [[../сборка/ci_and_quality]]
- [[../архитектура/backend]]
- [[../архитектура/frontend]]
