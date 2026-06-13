# Реализация Ролей И Доступа Дня 2

Date: 2026-06-13
Type: session
Tags: sprint-1, roles, access, auth, seed, realtime, frontend, docker
Related files:

- `apps/backend/app/alembic/versions/b82a5f2d91c3_editor_reviewer_roles.py`
- `apps/backend/app/models/user.py`
- `apps/backend/app/api/auth.py`
- `apps/backend/app/api/websocket_auth.py`
- `apps/backend/app/services/demo_user_seed_service.py`
- `apps/frontend/src/domain/authRole.ts`
- `apps/frontend/src/components/ReviewerHome.vue`
- `Code_wiki/dev_setup/local_development.md`
- `Code_wiki/deployment/docker_compose.md`

## Summary

День 2 реализован: active role model содержит только `editor` и `reviewer`,
HTTP и WebSocket auth повторно загружают актуального пользователя из БД,
demo seed создаёт трёх пользователей со стабильными UUID, а Reviewer не видит
editor workspace.

## Context

Migration `b82a5f2d91c3` удаляет legacy `viewer`, меняет CHECK constraint и
добавляет `is_active`. JWT больше не является source of truth для текущей роли:
после проверки token shape используется роль и active status записи `User`.
Seed расширяет существующий `DemoUserSeedService`, а не вводит второй механизм.

## Actions

- 2026-06-13: Добавлены mutually exclusive guards `require_editor` и
  `require_reviewer`, а также structured errors `AUTH_REQUIRED`,
  `USER_INACTIVE`, `ROLE_NOT_ALLOWED`.
- 2026-06-13: Read-only realtime разрешён `editor` и `reviewer`; legacy token
  role и inactive user отклоняются.
- 2026-06-13: Stable demo UUID закреплены за двумя Editors и одним Reviewer;
  повторный seed восстанавливает role, password и `is_active`.
- 2026-06-13: Frontend получил общий role helper и `ReviewerHome`; карта
  рендерится только для Editor.
- 2026-06-13: В `tests/conftest.py` добавлены test-only settings defaults,
  необходимые для чистого CI container после появления DB-backed auth imports.
- 2026-06-13: Работа выполнена в текущей ветке без worktree, staging и commits.

## Verification

Backend: `63 passed`, Black и Ruff прошли, targets `dev` и `prod` собраны.
Frontend: `29 passed`, format, lint, typecheck и build прошли, production nginx
image собран. Подтверждены base Compose CI smoke, upgrade существующего volume,
изолированный clean install, профили `dev` и `prod`, login обеих ролей,
отклонение legacy Viewer и идемпотентный seed.

## Retrieval Hints

Sprint 1 Day 2 implementation, Editor Reviewer auth, b82a5f2d91c3,
stable demo UUID, ReviewerHome, CI clean container, Compose upgrade smoke
