# Backlog Исправлений По Ревью Спринта 1

Дата: 2026-06-28

Источник: [Глубокое ревью кода Спринта 1](2026-06-28-sprint-1-deep-code-review.md)

## Quick Wins

| Приоритет | Задача | Проверка |
|---|---|---|
| P1 | Добавить `workOrders.reset()` и вызывать при `auth.logout()`/смене user id | Frontend test на logout/login другого editor без stale `activeWorkspace` |
| P1 | Обработать concurrent open `EditVersion` через lock/upsert/`IntegrityError` recovery | Backend test на два параллельных open или simulated `IntegrityError` |
| P2 | Унифицировать invalid login и workflow errors в `{code,message,correlationId}` | API tests + frontend `parseApiError` tests |
| P2 | Lazy-load `MapView` и не монтировать MapLibre в empty state | `npm run build`, chunk budget ниже текущих `1,167.86 kB` |
| P3 | Добавить `aria-live`, `role="alert"`, `aria-current/pressed` для списка нарядов и ошибок | Vue component tests на ARIA attributes |

## Security Hardening

| Приоритет | Задача | Проверка |
|---|---|---|
| P1 | Разделить demo/dev compose и production-safe defaults для `DEV_MODE`/`JWT_SECRET` | Startup tests/settings tests |
| P1 | Заменить JWT query string в WebSocket на short-lived ticket или cookie auth | Realtime tests без `token=` в URL |
| P1 | Убрать долговременный access token из `localStorage` или сократить риск до in-memory/session strategy | Auth store tests |
| P2 | Ограничить legacy `/layers` и `/ws/layers` по role/scope или feature flag | Reviewer/editor access regression tests |

## Architecture And Data

| Приоритет | Задача | Проверка |
|---|---|---|
| P2 | Добавить операционные проверки согласованности для cross-context UUID links, намеренно не закрепленных FK | Seed-chain/preflight tests без добавления cross-context FK |
| P2 | Переписать destructive demo migrations перед production-like средой | Migration upgrade/downgrade test plan |
| P2 | Оптимизировать workspace aggregate query перед ростом dataset | DB integration test + explain plan на larger fixture |
| P3 | Типизировать auth user и workspace aggregate вместо `Any` | `ruff check`, `mypy/pyright` если будет добавлен |

## UX/UI Polish

| Приоритет | Задача | Проверка |
|---|---|---|
| P2 | Добавить workspace details panel вместо длинного map badge | Component test + ручная проверка desktop/mobile |
| P3 | Добавить actionable error messages с `correlationId` | Component tests для structured errors |
| P3 | Заменить ключевые текстовые controls на icon+text/icon buttons с tooltip | Visual review + accessibility checks |
| P3 | Зафиксировать размеры кнопок/loading labels, чтобы не дергать layout | Component screenshot/manual check |
