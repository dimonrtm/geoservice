# День 13: результат реализации сквозной проверки

Дата: 2026-10-25. Основание: принятые [спецификация](2026-10-25-day-13-smoke-design.md) и [план](2026-10-25-day-13-smoke-plan.md). Детали исполнения и RED→GREEN — в [журнале](2026-10-25-day-13-execution-ledger.md).

## Результат

Существующий API smoke расширен фазами `save` и `verify-retry-revert`. Прежний вызов без параметров сохранён. CI связывает фазы экспортированным state, перезапускает штатный backend, проверяет новый StartedAt и readiness, затем собирает evidence до cleanup. Browser suite остаётся локальным.

Сценарные изменения выполняются через публичный API; SQL observer независимо читает current/baseline, revision, registry и history в read-only repeatable-read транзакции. Новый локальный Compose override удаляет fixed container names/ports и использует tmpfs вместо пользовательского volume. Код приложения, API-контракт и migrations не менялись.

## Фактическая проверка

| Проверка | Результат |
| --- | --- |
| Backend `pytest -o addopts= -q -p no:cacheprovider` | 647 passed, 270 skipped (DB-only), exit 0 |
| Smoke unit tests | 47 passed, входят в backend suite |
| `infra/db-tests.cmd` | 271 passed, exit 0; отдельная geo_test, cleanup выполнен |
| Frontend `npm.cmd test -- --maxWorkers=2` | 323 passed, 44 suites, exit 0 |
| Frontend typecheck/lint/format/build | Все exit 0 |
| Backend Black/Ruff | Полный check прошёл; после review-fix повторены Black для изменённой области и полный Ruff |
| Browser `npm.cmd test` из `infra/m4` | 7 passed, retries=0, exit 0; project geoservice-m4-ce6b959f очищен |
| Live API smoke на fresh БД | Прежний open-path и обе новые фазы exit 0, настоящий restart между фазами |
| Fail-closed на live БД | Неверный runId и завершённый state дали exit 1, SQL snapshot не изменился |
| Workflow/Compose | YAML разобран js-yaml; config валиден; проверено отсутствие fixed names, ports и persistent DB volume в локальном override |
| Wiki lint | 37 известных missing_frontmatter только в RAW; новых замечаний нет |

Backend сохраняет прежние deprecation warnings `crypt` и `BlockingPortal`. Frontend build сообщает о chunk больше 500 kB; это не новая регрессия Дня 13. Первичный запуск frontend в sandbox получил esbuild EPERM, успешный прогон выполнен с эскалацией. Docker pipe также требовал штатного разрешения.

## Доказательство live сценария

Финальный runId: `5c3f2279-c3e0-475a-a3b5-1c074ced1303`, изолированный project `geoservice-day13-final`. Он создан заново после исправлений review. [Save](evidence/day-13/api-5c3f2279/save.json), [restart](evidence/day-13/api-5c3f2279/restart.json), [verify](evidence/day-13/api-5c3f2279/verify.json), [fail-closed](evidence/day-13/api-5c3f2279/failclosed.json).

| Граница | Revision | Command records | Events |
| --- | --- | --- | --- |
| Fresh workspace | 1 | 0 | 0 |
| Save | 2 | 1 succeeded | 1 persisted |
| Restart и replay | 2 | 1 succeeded | 1 persisted |
| Четыре отрицательных запроса | 2 | 1 succeeded + 3 rejected | 1 persisted |
| Revert | 3 | 2 succeeded + 3 rejected | 1 persisted + 1 cleared |

Отказы дали соответственно 409 DRAFT_VERSION_STALE, 409 COMMAND_ID_REUSED, 422 GEOMETRY_INVALID и 422 GEOMETRY_OUTSIDE_AOI. Reused request не изменил исходную terminal command. Baseline EWKB L-003 совпал на всех проверяемых границах; финальный current EWKB совпал с baseline. Restart manifest подтверждает смену backend StartedAt при неизменном PostGIS StartedAt. Повторный startup действительно включает migrations и seeds; ручной reset между фазами не выполнялся.

Browser JSON сохранены отдельно в `evidence/day-13/m4-ce6b959f/`. Исторические артефакты S2-X01, которые штатный M4 runner перезаписывает, возвращены к исходному содержимому после архивации новых JSON. Старый verification.json не перенесён как доказательство нового запуска. Проверка browser zoom/ручное UI-demo не заявляются.

## Review и исправления

Независимое read-only review выявило два Important, Critical/Minor не выявлены:

1. Smoke принимал 201/202 с правильным body вместо обязательного 200. Три regression tests наблюдались RED→GREEN; Save, replay и Revert проверяют точный HTTP status.
2. Failure evidence терял текущий этап/причину при неверном отказе. Regression test наблюдался RED→GREEN; теперь сохраняются active stage, безопасные expected/actual status/code, SQL snapshots до assertions и причина harness-authored проверки. Произвольный server message, exception text и credentials не пишутся.

После исправлений выполнены полный backend suite и новый fresh live сценарий. Повторное review не подменяло регрессионные проверки. Отдельно в первом preflight обнаружена ошибка тестовой fixture: workspace не содержит ownerId; она исправлена сравнением login JWT subject с SQL owner. Первоначальный неуспешный запуск до PUT не считается приёмкой.

## Решения исполнения и ограничения

- Сохранён существующий checkout `first-edit-save`; новые worktree/ветка не создавались. Изменения оставлены unstaged.
- Журнал ведётся в docs/sprint_2, а не в commit-based scratch workflow: staging/commit/push запрещены пользователем. Восстановление исполнения опирается на журнал и рабочие файлы.
- Для локальной изоляции вместо обязательной VM выбран разрешённый спецификацией ограниченный Compose override. Цена — зависимость от поддержки `!reset`/`!override`; config проверяется до запуска.
- Readiness выделен в общий stdlib helper для CI/runbook. Цена — небольшой дополнительный тестовый модуль; выигрыш — проверка старого healthy и timeout без текстового grep workflow.
- GitHub Actions с remote runner не запускался: push запрещён. Проверены локальные suites, YAML/Compose и фактические команды двух фаз/restart. Remote CI результат остаётся доступен после действий пользователя.
- Не проверяются crash БД, уничтожение storage, все baseline features или все поля baseline. Это согласованные границы задачи.
- Узкий repository-change ingest создал техническую ноду о фазовом smoke и обновил registry/index. Прежнее расхождение CI-ноды о запуске DB integration внутри demo записано в новой ноде, старый текст не исправлялся. Agent memory не дублирует runbook и отчёт.

Воспроизведение: [runbook](2026-10-25-day-13-smoke-runbook.md). Итоговая приёмка всего Sprint 2 и ручной demo остаются Дню 14.
