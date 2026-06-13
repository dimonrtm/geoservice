# План Реализации Ролей И Доступа Дня 2

Date: 2026-06-13
Type: session
Tags: sprint-1, planning, roles, access, editor, reviewer
Related files:

- `docs/sprint_1/2026-06-13-sprint-1-day-2-roles-access-design.md`
- `docs/sprint_1/2026-06-13-sprint-1-day-2-roles-access-implementation-plan.md`
- `apps/backend/app/models/user.py`
- `apps/backend/app/api/auth.py`
- `apps/backend/app/services/demo_user_seed_service.py`
- `apps/frontend/src/api/auth.ts`
- `apps/frontend/src/App.vue`

## Summary

Подготовлен TDD-план Дня 2 для перехода с legacy `Viewer`/`Editor` на
взаимоисключающие `Editor`/`Reviewer`. План сохранен вместе с остальными
артефактами Спринта 1 и разбит на шесть исполнимых инкрементов.

## Context

Фактический код использует `VARCHAR + CHECK`, а не native PostgreSQL enum.
`get_current_user` доверяет JWT и не загружает актуального пользователя из БД.
Frontend всегда показывает editor map. План учитывает эти факты и не пытается
реализовать отсутствующие `WorkOrder` или reviewer queue раньше их backlog
items.

## Actions

- 2026-06-13: Запланирована миграция CHECK constraint и добавление `is_active`.
- 2026-06-13: Запланированы DB-backed auth dependency и взаимно исключающие
  guards `require_editor`/`require_reviewer`.
- 2026-06-13: Зафиксированы стабильные UUID и demo credentials для двух
  editors и одного reviewer.
- 2026-06-13: Assignment authorization отложена до появления `WorkOrder` в
  S1-05; reviewer queue и решения review остаются вне Дня 2.
- 2026-06-13: По прямому указанию пользователя реализация выполняется в
  текущей ветке без worktree, `git add`, `git commit` и изменения уже
  существующего staging.
- 2026-06-13: Demo users создаются через существующую цепочку
  `seed_demo_users.py -> run_demo_user_seed() -> DemoUserSeedService`; новый
  seed-механизм не создаётся.
- 2026-06-13: Все текущие jobs `.github/workflows/ci.yml`, backend/frontend
  Docker targets и Compose-сценарии `backend`, `dev`, `prod` являются
  обязательными regression gates. Перед изменениями сохраняется legacy
  volume, чтобы проверить upgrade существующего deployment, а не только clean
  install.
- 2026-06-13: Отдельного CD workflow в репозитории нет; план не выдумывает
  новый pipeline и сохраняет текущий локальный Compose deployment.
- 2026-06-13: План требует TDD, Docker migration/login smoke и финальный
  `/ingest repository-change`.

## Verification

План проверяется на покрытие design, отсутствие placeholders и согласованность
ролей/имен. Код и тесты приложения на этапе планирования не изменялись.

## Retrieval Hints

Sprint 1 Day 2 implementation plan, Editor Reviewer migration, DB-backed auth,
stable demo users, reviewer placeholder, roles access plan
