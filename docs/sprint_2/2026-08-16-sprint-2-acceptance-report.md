# Sprint 2: отчёт о приёмке

**Вердикт: Sprint 2 принят, M5 выполнена в согласованных границах.**

Фактическая дата проверок и подтверждения пользователя: 2026-10-26. Дата 2026-08-16 в имени — календарный День 14. Проверенный HEAD: `700888bda0fe2aaa6b7990b4a46ab6f72cf3ee0f`, ветка `first-edit-save`. Продуктовый код в ходе приёмки не менялся. Исходное постороннее изменение `.obsidian/graph.json` не затрагивалось.

Основания: [ТЗ](2026-07-31-sprint-2-technical-requirements.md), [спецификация Дня 14](2026-10-26-day-14-acceptance-design.md), [уточнения](2026-10-26-day-14-acceptance-analysis.md), [журнал исполнения](2026-10-26-day-14-execution-ledger.md).

## Ручная приёмка и происхождение свидетельства

Пользователь подтвердил в текущем чате: «Я провел ручную проверку кейс работает». Подтверждение дано после явного перечисления полного кейса: WO-001 → L-003 → drag внутренней вершины → Save → refresh → restart backend → readback → Revert. Оно принято как ручное подтверждение AC-10 и ручной части durable readback.

Это свидетельство пользователя, а не завершённый UI-прогон агента. Точное время, браузер, fingerprint окружения и скриншоты пользовательского прогона не предоставлены; они не выдумываются. Последующее подтверждение пользователя заменяет ранее выбранного исполнителя ручного demo и снимает прежнее состояние «приёмка не завершена».

Попытка агента остановилась до редактирования: встроенный браузер показал [недоступность recovery storage](evidence/day-14/ui-a1787253/iab-storage-unavailable.png), затем Computer Use прекратил работу при переходе к Chrome, поскольку не смог надёжно определить URL. Причина сообщения storage не установлена; оно не объявляется доказанным дефектом приложения или исправленным ограничением браузера. Успешный M4 и ручное подтверждение пользователя дают основания для приёмки согласованного сценария, но не подтверждают совместимость со встроенным браузером.

## Полный локальный regression

[Сводка результатов команд](evidence/day-14/local-suites.json) записана агентом по фактическому выводу команд; это не исходный машинный лог тестового runner.

| Проверка | Команда / место запуска | Результат |
| --- | --- | --- |
| Backend image | `docker build --target dev -t geoservice-day14-check apps/backend` | exit 0 |
| Backend format | В image: `black --check .` | 320 files unchanged, exit 0 |
| Backend lint | В image: `ruff check .` | exit 0 |
| Backend tests | В image: `pytest` | 647 passed, 270 DB-only skipped, exit 0 |
| Изолированная БД | `infra\db-tests.cmd` | 271 passed, exit 0; cleanup прошёл |
| Frontend tests | `apps/frontend`: `npm.cmd test -- --maxWorkers=2` | 323 passed, 44 suites, exit 0 |
| Frontend quality/build | `npm.cmd run typecheck`, `lint`, `format:check`, `build` | Все exit 0 |
| Recovery/доступность | `infra/m4`: `npm.cmd test` | 7 passed, retries=0, exit 0 |

DB suite включает migration upgrade/downgrade/upgrade, в том числе `test_first_save_populated_upgrade_downgrade_upgrade`, а также атомарность geometry policy migration. Backend/DB suites включают settings, seeds, fixture upgrade idempotency/rollback и startup-order checks. Пропуски DB tests обычного pytest покрыты отдельным DB suite.

Первичные frontend test/build получили sandbox `spawn EPERM` от esbuild; повтор с разрешённой эскалацией прошёл. Docker также потребовал штатной эскалации доступа к named pipe. Сохранились deprecation warnings `crypt`/`BlockingPortal` и предупреждение frontend о chunk >500 kB; это не failures проверок.

## Fresh setup, restart и baseline

RunId: `1d02f61f-38a5-47ec-a877-d7f18652c41c`. Project: `geoservice-day13-1d02f61f` — шаблон имени сохранён ради guard существующего runbook. Запуск выполнен на новой tmpfs БД с migrations и штатной seed/fixture startup chain; пользовательский demo volume не использовался.

Доказательства: [Save](evidence/day-14/api-1d02f61f-38a5-47ec-a877-d7f18652c41c/save.json), [restart manifest](evidence/day-14/api-1d02f61f-38a5-47ec-a877-d7f18652c41c/restart.json), [verify/replay/отказы/Revert](evidence/day-14/api-1d02f61f-38a5-47ec-a877-d7f18652c41c/verify.json), [финальный state](evidence/day-14/api-1d02f61f-38a5-47ec-a877-d7f18652c41c/state.json). Save/verify/restart имеют status=passed; state=complete; команды завершились exit 0.

| Граница | Revision | Registry/history |
| --- | --- | --- |
| Fresh | 1 | 0 commands, 0 events |
| Save | 2 | 1 succeeded, 1 persisted event |
| Restart и replay | 2 | Без повторной mutation/event |
| Четыре отказа | 2 | Дополнительно 3 rejected; reused не создаёт новую запись |
| Revert | 3 | 2 succeeded + 3 rejected, 2 events: persisted и cleared |

Backend StartedAt изменился с `2026-10-26T14:12:43.674871151Z` на `2026-10-26T14:13:32.088429895Z`. PostGIS StartedAt остался `2026-10-26T14:12:37.798322621Z`. Между фазами БД не сбрасывалась. Read-only SQL observer подтвердил неизменность baseline EWKB L-003 и равенство финального current baseline. Отказы: DRAFT_VERSION_STALE и COMMAND_ID_REUSED — 409, GEOMETRY_INVALID и GEOMETRY_OUTSIDE_AOI — 422.

## Матрица AC и Definition of Done

| Критерий | Подтверждение | Итог |
| --- | --- | --- |
| AC-01: grid/rounding/settings | Settings и domain geometry tests в полном backend suite | Подтверждён |
| AC-02: fresh/upgrade fixture | Seed/fixture/startup tests, DB integration, fresh open-path: 19 features / 9 associations | Подтверждён |
| AC-03: Save | API/service tests, live save.json, ручное подтверждение пользователя | Подтверждён |
| AC-04: атомарность и immutable baseline | `test_save_geometry_atomicity.py`, observer и live verify | Подтверждён |
| AC-05: idempotency | Replay/concurrency tests и live replay после restart | Подтверждён |
| AC-06: stale | Backend/frontend tests, live 409, M4 comparison | Подтверждён |
| AC-07: geometry guards | Structure/canonicalization/PostGIS tests, live invalid/outside | Подтверждён |
| AC-08: durable readback | Новый HTTP session, настоящий restart в API/M4, ручное подтверждение пользователя | Подтверждён |
| AC-09: Cancel/Revert | Frontend tests Cancel; API events, M4 и ручное подтверждение Revert | Подтверждён |
| AC-10: ручной UI-demo | Подтверждение пользователя в этом чате; не выдается за прогон агента | Подтверждён пользователем |
| Backend/frontend format/lint/tests/typecheck/build | Таблица regression выше | Подтверждены |
| Migration cycle и fresh DB/API smoke | Полный DB suite и фазовый live smoke | Подтверждены |
| POSITIONAL_ACCURACY_UNVERIFIED не означает verified | API payload/validation assertions и frontend presentation tests | Подтверждён в согласованном автоматическом покрытии |
| Acceptance report и Git | Этот документ; staging/commit/push не выполнялись | Выполнено |

M4 project `geoservice-m4-e04ad6d4` прошёл все семь существующих сценариев: Save/Revert после потери ответа и restart, восстановление доступа, закрытие/перезапуск браузера, независимые контексты, старый replay, изоляция аккаунтов и IndexedDB CAS/corruption. [Результат](evidence/day-14/m4-e04ad6d4/result.json). Новые изменившиеся evidence архивированы отдельно, исторические файлы восстановлены с проверкой SHA256. Старый verification.json не выдаётся за новый прогон.

## Блокеры, ограничения и cleanup

Подтверждённых блокирующих отклонений обязательного сценария или существующего M4 нет. Исправления продуктового кода не потребовались.

- Remote GitHub Actions не запускался и по решению пользователя не обязателен.
- Настоящий browser zoom 200% не проверен и по решению пользователя не блокирует M5. Recovery и доступность ограничены существующим M4.
- Незавершённый прогон агента и неустановленная причина storage-сообщения встроенного браузера сохранены выше. Совместимость со всеми браузерами этим отчётом не заявляется.
- Baseline proof ограничен геометрией L-003; review/post, topology и positional accuracy verification не входят в Sprint 2.
- Изолированные DB, API smoke, M4 и оставшийся UI project `geoservice-day14-ui-a1787253` очищены. Последний cleanup exit 0, контейнеров этого UI project после него нет. Пользовательский project infra не останавливался.

## Решение об ingest и памяти

`/ingest repository-change` **не требуется**: новой устойчивой технической реализации или установленной новой причины дефекта не появилось. Существующие механизмы уже описаны в Code_wiki и runbook Дня 13; результаты приёмки сохраняются здесь. Сообщение встроенного браузера остаётся наблюдением с неизвестной причиной, а не новой технической закономерностью. Agent memory не дублирует этот отчёт.
