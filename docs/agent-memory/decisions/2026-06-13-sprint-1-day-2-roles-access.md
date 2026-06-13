# Роли И Доступ Дня 2 Спринта 1

Date: 2026-06-13
Type: decision
Tags: sprint-1, roles, access, rbac, editor, reviewer, demo-users
Related files:

- `docs/sprint_1/2026-06-13-sprint-1-day-2-roles-access-design.md`
- `docs/sprint_1/README.md`
- `apps/backend/app/models/user.py`
- `apps/backend/app/api/auth.py`
- `apps/backend/app/services/demo_user_seed_service.py`
- `apps/frontend/src/api/auth.ts`

## Summary

Для Utility Workflow принята строгая взаимоисключающая модель ролей
`Editor`/`Reviewer`. Legacy `Viewer` должен быть удален из DB enum, API,
frontend и demo seed. Автоматическое преобразование `Viewer` в `Reviewer`
запрещено.

## Context

Текущий generic foundation использует роли `viewer/editor`, а новый Release 1
требует separation of duties. День 2 фиксирует целевой контракт до
реализации: `Editor` работает только с назначенными work orders, `Reviewer`
имеет общую очередь review и в будущих спринтах выполняет approve/reject и
последующий `post`.

## Actions

- 2026-06-13: Выбрана одна enum-роль на пользователя вместо permission-флагов
  или many-to-many RBAC.
- 2026-06-13: Зафиксировано удаление legacy `Viewer`; связанные неизвестные
  значимые данные должны останавливать миграцию.
- 2026-06-13: Зафиксированы demo users `alexey.editor`, `bolat.editor` и
  `marina.reviewer`.
- 2026-06-13: Зафиксирована общая reviewer queue без назначения reviewer.
- 2026-06-13: Зафиксировано, что `Reviewer` выполняет approve/reject и
  отдельный `post`.
- 2026-06-13: Ошибка доступа к существующему чужому `WorkOrder` уточнена как
  `403 WORK_ORDER_NOT_ASSIGNED`; риск раскрытия идентификатора допустим только
  для local demo и должен быть пересмотрен перед production.
- 2026-06-13: Все существующие CI jobs, backend/frontend Docker targets и
  Compose-сценарии `backend`, `dev`, `prod` зафиксированы как обязательные
  regression gates. Миграция проверяется на чистой БД и поверх legacy volume;
  отдельный CD workflow не добавляется.

## Verification

Design проверен на placeholders, внутренние противоречия и границы scope.
Реализация и тесты в рамках brainstorming не выполнялись.

## Retrieval Hints

Sprint 1 Day 2, Editor Reviewer, separation of duties, Viewer removal,
WORK_ORDER_NOT_ASSIGNED, demo users, reviewer queue, approve post
