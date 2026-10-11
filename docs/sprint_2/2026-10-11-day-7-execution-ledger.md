# Журнал исполнения — docs/sprint_2/2026-10-11-day-7-rejections-events-revert-plan.md

Спецификация принята, реализация разрешена. Исполнение последовательное.

## Решения до реализации

- Ruling: использовать текущую feature-ветку `first-edit-save` — она содержит код Дня 6 и незакоммиченные согласованные документы; создание другой рабочей копии не требуется для изоляции от main. Пользовательские изменения не удалять. Цена ошибки — общий checkout; проверять diff перед завершением.
- Ruling: журнал ведётся в `docs/sprint_2` вместо git-ignored SDD workspace — пользователь требует сохранять артефакты здесь, commits запрещены и git history не заменяет журнал. Bash commit-oriented scripts заменяются явными проверками и записями результатов.
- Docker sandbox первоначально запретил доступ к engine; разрешённый escalated доступ работает, Server 28.1.1.

## Проверка интерфейсов

| Зависимость | Результат |
| --- | --- |
| 1 -> 3 | FingerprintContext уже содержит stable root provenance и token; новый тип context не требуется |
| 2 -> 3 | reject/resume используют существующий LockedEditVersion и immutable command row |
| 3 -> 4 | Outcome отделён от API exception; event вызывается только на success path |
| 4 -> 5 | GeometryWriteResult содержит before/after, root переживает consume context |
| 1–5 -> 6 | Полная DB-матрица использует isolated runner |

## Прогресс

- Задача 1: начата.
- Исходная регрессия: 40 passed (Save service/replay + geom-v1).
- Задача 1: RED отсутствующий contextless module; GREEN 25 passed с geom-v1 regression. Независимый golden digest рассчитан SHA256 .NET по literal JSON.
- Задача 2: RED 2 failed / 4 passed (нет reject_command); GREEN 45 passed registry repository + command constraints.
- Задача 3: RED 7 failed по отсутствию durable rejection/access retry; GREEN 7 новых scenarios, затем 34 passed включая события и обновлённую use-case regression.
- Дополнительный RED: wrong-type baseline ошибочно попадал в geom-v1. Исправлено: WORK_ORDER_CONTEXT_INVALID при подготовке baseline выбирает contextless для новой команды.
- Задача 4: RED 2 DB event assertions (0 событий); GREEN цепочка и revision 5 -> 6. Сохранены проверки off-grid и immutable baseline.
- Задача 5: промежуточный GREEN 50 passed (DB rejection/atomicity/concurrency + unit rejection).
- Ruling: DB suite переименована в `test_save_geometry_rejections_integration.py` — pytest без package isolation конфликтовал с одноимённым unit module.
- Ruling: DB repair fixture использует несогласованную baseline revision, а неверный geometry type/EWKB проверяется unit-тестом — реальные DB CHECK запрещают такой geometry type; constraints не отключаются.
- Ruling: прежний deferred failure после пропущенной finalization стал падать на event INSERT. Теперь test сначала проверяет реальный INSERT event, затем создаёт отдельную незавершённую команду; deferred trigger падает именно при commit.

## Завершение

- Задачи 1–6 завершены. Независимый review не подтвердил production P1/P2; три пробела acceptance tests закрыты: старая succeeded row без event, успешный access resume с rollback и multiple-feature rejection на БД.
- После дополнений review: 36 passed в events/rejections integration/atomicity.
- Финальная backend regression: 555 passed, 257 skipped (DB отключена), 2 warnings. Полный isolated DB runner отдельно: 258 passed, без skipped, 2 warnings; exit 0 и cleanup завершён.
- Первый финальный DB runner не засчитан: Compose обнаружил параллельный unit-контейнер и прервал DB suite при его завершении. Повторный полный runner выполнен без параллельных Docker-проверок.
- Black: 302 files would be left unchanged. Ruff: All checks passed. Проверки проведены на финальном image после последнего изменения tests.
- Minor review suggestions о дополнительных assertions provenance и комбинациях guards сохранены в отчёте; подтверждённых production-дефектов за ними нет.
- Дополнительные acceptance tests задачи 5 сразу проверяли готовые production-интерфейсы; искусственный RED не создавался. Точные результаты RED/GREEN перечислены выше.
- Отчёт реализации содержит mapping M2-01–24 и границы backend evidence. API/UI/process restart не объявлены выполненными.
- Применён finishing-a-development-branch с приоритетом AGENTS.md: текущий checkout и unstaged изменения сохранены для пользователя, без staging/commit/push.
- Agent memory и Code_wiki не дополнены: отдельного устойчивого знания, не сохранённого принятыми артефактами, не выявлено.

## Исправление форматирования SQL по замечанию пользователя

Отдельная проверка SQL внутри Python-строк была пропущена, хотя существующее правило форматирования её требует. Black/Ruff не обнаруживают такой пропуск. Исправлены INSERT события и запросы трёх Save integration suites: многострочные списки, блоки запросов и ровные отступы. SQL-токены сохранены; для двух новых suites дополнительно сравнён нормализованный Python AST. Повторный полный isolated DB runner: 258 passed, 2 warnings, exit 0. Новая memory-запись не нужна: правило уже явно сохранено.
