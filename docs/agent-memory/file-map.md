# File Map

Compact topic-to-file map for agent retrieval. Keep entries short and update only when durable relationships change.

## Agent Memory

- agent memory protocol workflow: `AGENTS.md`, `docs/agent-memory/protocol.md`
- agent memory quick file lookup: `docs/agent-memory/file-map.md`
- agent memory design spec: `docs/superpowers/specs/2026-05-30-agent-memory-design.md`
- implementation plans language rule: `docs/agent-memory/patterns/2026-05-30-russian-implementation-plans.md`, `docs/superpowers/plans/`
- project knowledge wiki pipeline: `index.md`, `RAW_inputs/`, `Vision_wiki/`, `Code_wiki/`, `memory/`, `Общие_принципы/`, `docs/knowledge-pipeline/README.md`, `.agents/skills/source-command-*/`
- wiki checks: `scripts/lint-wiki.py`, `scripts/check-memory-needed.py`
- repository-change ingest workflow: `.agents/skills/source-command-ingest/SKILL.md`, `Code_wiki/состояние_проекта/repository_change_ingest.md`
- repository-snapshot ingest workflow: `.agents/skills/source-command-ingest/SKILL.md`, `Code_wiki/состояние_проекта/repository_snapshot.md`
- RAW_inputs batch ingest workflow: `.agents/skills/source-command-ingest/SKILL.md`, `docs/knowledge-pipeline/README.md`, `RAW_inputs/index.md`
- Release 1 RAW requirements ingest: `RAW_inputs/documents/спринт 1.odt`, `Vision_wiki/chats/2026-05-30-release-1-document.md`, `Vision_wiki/concepts/first_release_mvp.md`, `Vision_wiki/solution/USM.md`, `Vision_wiki/solution/roadmap.md`, `Vision_wiki/solution/nfr.md`, `Vision_wiki/solution/architecture_vision.md`, `Code_wiki/архитектура/api_contract_first_release_requirements.md`
- initial GeoService discover context: `Vision_wiki/chats/2026-05-31-initial-discover.md`, `Vision_wiki/concepts/about_project.md`, `Vision_wiki/entities/stakeholders/dmitry_popov.md`, `memory/project-state.md`
- GeoService discover Ф1 why-now research goals: `Vision_wiki/chats/2026-05-31-phase-f1-why-now.md`, `Vision_wiki/concepts/about_project.md`, `Vision_wiki/concepts/product_vision_board.md`, `Vision_wiki/concepts/lean_canvas.md`, `Vision_wiki/decisions/risk_assumption_log.md`
- Code_wiki repository snapshot inventory: `Code_wiki/архитектура/backend.md`, `Code_wiki/архитектура/frontend.md`, `Code_wiki/архитектура/api_and_realtime.md`, `Code_wiki/архитектура/data_model.md`, `Code_wiki/dev_setup/local_development.md`, `Code_wiki/deployment/docker_compose.md`, `Code_wiki/сборка/ci_and_quality.md`, `Code_wiki/правила_и_стиль/testing_strategy.md`, `Code_wiki/глоссарий/technical_terms.md`
- Obsidian wiki graph config: `.obsidian/app.json`, `.obsidian/appearance.json`, `.obsidian/core-plugins.json`, `.obsidian/graph.json`, `.obsidian/templates.json`
- discover startup mode and wiki filling phases: `.agents/skills/source-command-discover/SKILL.md`, `Общие_принципы/Вопросы стейкхолдеру.md`, `Общие_принципы/Фазы наполнения wiki.md`, `Vision_wiki/solution/USM.md`, `Vision_wiki/solution/roadmap.md`, `Vision_wiki/solution/nfr.md`, `Vision_wiki/solution/architecture_vision.md`

## Project Documentation

- product requirements planning: `docs/requirements/geoservice-prd-v1.md`, `docs/requirements/geoservice-requirements.md`, `docs/requirements/action-plan.md`
- sprint 1 implementation plans: `docs/requirements/sprints/sprint-1/sprint-1-plan.md`, `docs/requirements/sprints/sprint-1/day-8-plan.md`
- project overview: `README.md`, `docs/project-description.md`

## Backend

- FastAPI app entry lifecycle: `apps/backend/app/main.py`, `apps/backend/app/api/lifespan.py`
- backend settings configuration: `apps/backend/app/core/settings.py`
- backend database migrations: `apps/backend/app/db/session.py`, `apps/backend/app/alembic/env.py`, `apps/backend/app/alembic/versions/0d9dcd16a92c_add_all_types_features.py`, `apps/backend/app/alembic/versions/431fdb240d56_feature_lines.py`
- backend schemas: `apps/backend/app/schemas/create_feature_in.py`, `apps/backend/app/schemas/feature_out.py`, `apps/backend/app/schemas/feature_collection_out.py`, `apps/backend/app/schemas/layer_out.py`, `apps/backend/app/schemas/auth_success_out.py`
- auth login users jwt: `apps/backend/app/api/auth.py`, `apps/backend/app/services/auth_service.py`, `apps/backend/app/repositories/user_repository.py`, `apps/backend/app/models/user.py`
- demo user seed: `apps/backend/app/seed_demo_users.py`, `apps/backend/app/services/demo_user_seed_service.py`
- layers API service repository: `apps/backend/app/api/layers.py`, `apps/backend/app/services/layer_service.py`, `apps/backend/app/repositories/layer_repository.py`, `apps/backend/app/models/layer.py`
- feature CRUD storage: `apps/backend/app/services/feature_service.py`, `apps/backend/app/domain/feature_registry.py`, `apps/backend/app/models/feature_point.py`, `apps/backend/app/models/feature_line.py`, `apps/backend/app/models/feature_polygon.py`, `apps/backend/app/models/feature_multipoint.py`, `apps/backend/app/models/feature_multiline.py`, `apps/backend/app/models/feature_multipolygon.py`
- websocket layer realtime auth: `apps/backend/app/api/ws_layers.py`, `apps/backend/app/api/websocket_auth.py`, `apps/backend/app/services/realtime_connection_manager.py`
- realtime feature publishing: `apps/backend/app/services/feature_realtime_publisher.py`
- backend tests auth realtime features: `apps/backend/app/tests/test_auth_service.py`, `apps/backend/app/tests/test_websocket_auth.py`, `apps/backend/app/tests/test_ws_layers.py`, `apps/backend/app/tests/test_feature_service.py`

## Frontend

- Vue app entry: `apps/frontend/src/main.ts`, `apps/frontend/src/App.vue`, `apps/frontend/src/pinia.ts`
- auth login state API: `apps/frontend/src/stores/auth.ts`, `apps/frontend/src/api/auth.ts`, `apps/frontend/src/components/LoginScreen.vue`
- map page composition: `apps/frontend/src/components/MapPageView.vue`, `apps/frontend/src/components/MapView.vue`
- map instance style layers: `apps/frontend/src/composables/map/useMapInstance.ts`, `apps/frontend/src/composables/map/mapStyle.ts`, `apps/frontend/src/map/maplibrelayers.ts`
- layer selection loading cache: `apps/frontend/src/composables/map/useLayerSelection.ts`, `apps/frontend/src/composables/map/useFeatureLoading.ts`, `apps/frontend/src/composables/map/useFeatureTileCache.ts`
- frontend realtime websocket: `apps/frontend/src/composables/map/useLayerRealtime.ts`, `apps/frontend/src/contracts/realtime.ts`, `apps/frontend/src/contracts/map-cache.ts`
- polygon editing: `apps/frontend/src/composables/map/usePolygonEditing.ts`, `apps/frontend/src/map/polygon-editing.ts`, `apps/frontend/src/stores/edit.ts`
- frontend API contracts: `apps/frontend/src/contracts/api.ts`, `apps/frontend/src/contracts/geojson.ts`, `apps/frontend/src/api/http.ts`, `apps/frontend/src/api/layers.ts`
- frontend tests realtime auth editing: `apps/frontend/src/composables/map/useLayerRealtime.test.ts`, `apps/frontend/src/stores/auth.test.ts`, `apps/frontend/src/stores/edit.test.ts`

## Infra

- ci workflows: `.github/workflows/ci.yml`
- docker compose local dev: `infra/docker-compose.yml`, `infra/docker-compose.override.yml`, `infra/dev-up.cmd`, `scripts/dev.cmd`
- postgis init: `infra/docker/postgis/init/01-postgis.sql`
- frontend tooling config: `apps/frontend/package.json`, `apps/frontend/vite.config.ts`, `apps/frontend/tsconfig.json`, `apps/frontend/tsconfig.app.json`, `apps/frontend/tsconfig.node.json`
- backend tooling config: `apps/backend/pyproject.toml`
