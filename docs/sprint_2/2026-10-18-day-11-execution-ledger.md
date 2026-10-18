# Журнал исполнения — docs/sprint_2/2026-10-18-day-11-user-commands-plan.md

Спецификация и план приняты, пользователь поручил начать реализацию. Исполнение последовательное в текущем чате.

## Решения исполнения

- Ruling: используется текущая ветка `first-edit-save` и существующий checkout — пользователь поручил продолжить согласованную работу здесь; developer instructions предпочитают пригодный checkout. Main/master не затрагиваются, новый worktree не нужен.
- Ruling: журнал хранится в `docs/sprint_2/` по указанию пользователя; shell helpers skills для commit-based ledger не используются, поскольку AGENTS.md запрещает staging/commits. Проверки выполняются напрямую, изменения остаются unstaged.
- Pre-flight: задача 1 → 2: поля evidence и getter определены; задача 2 → 3: projection contract определён; задачи 1/3 → 4: единый localDraft сохраняется. Конфликтов интерфейсов при предварительной сверке нет.

## Ход выполнения

- Baseline заблокирован sandbox: esbuild spawn EPERM. Повторные тесты выполнялись с разрешением вне sandbox. Первый успешный полный suite после реализации: 34 suites / 267 tests PASS; не называется чистым baseline.
- Задача 1: RED — отсутствует Cancel с сохранением выбора, повтор unchanged rejected candidate отправляется, no-op getter отсутствует. GREEN — 68 store tests, затем 24 recovery tests с дополнительными сценариями restore/late callback.
- Задача 2: RED — projection module отсутствует. GREEN — 12 tests матрицы состояний.
- Задача 3: RED — отсутствуют компонент и его включение в Editor view. GREEN — 8 panel tests + 22 view tests.
- Задача 4: RED — marker доступен после storage failure, existing dialog не native modal. GREEN — 30 targeted interaction/panel/geometry/map tests.
- Первая сборка выявила только TypeScript ошибки в новых тестах (тип wrappers, Array.at, narrowing после явного null); исправлены без изменения compiler target. Build PASS, существующее предупреждение Vite о chunk > 500 kB. Lint PASS.
- Independent review: read-only `day11_review`, без edits. P2: после возврата к rejected candidate причина disabled Save скрывалась. RED→GREEN: отдельная projection regression.
- Browser подтвердил потерю фокуса после affirmative map discard (activeElement BODY). RED→GREEN: regression закрытия modal до удаления; handler закрывает dialog, watcher ждёт обновления DOM перед focus. Повтор browser-проверки предстоит.
- Final: minor (первоначально отложено, затем исправлено по поручению пользователя): сообщение недоступности Revert оставалось после нового движения/выбора на карте. Добавлено наблюдение за `localDraft`; две component regression checks RED→GREEN, основной статус и геометрия сохранены, HTTP не добавлены.
- Final: Ruling: перечисленные review ограничения (Revert execution, ручной recovery, stale resolution, navigation/relogin, keyboard geometry, смартфоны, backend/storage format) остаются вне реализации — это прямой согласованный scope; их отсутствие не дефект Дня 11, но полный сценарий восстановления пока недоступен.
- Задача 5: заключительные 34 suites / 269 tests PASS, lint PASS, build PASS. Локальный frontend-dev обновлён без backend/DB rebuild и удаления volumes.
- Browser повтор подтвердил возврат фокуса на CANVAS после affirmative discard, Tab/Shift+Tab в modal и Escape без потери dirty. Save выполнен через Enter, Revert placeholder через Space, Cancel через Space/Enter и click. Reload сохраняет изменённую L-003; последующий Cancel возвращает saved current. Несохранённой попытки в конце нет.
- Responsive: 1440×900, 1024×768, 768×1024 проверены. Ctrl+Plus в IAB не изменил масштаб; выполнен дополнительный reflow 720×450, 512×384, 384×512. Настоящий zoom 200% не заявляется проверенным; этот пункт остаётся незакрытым. Screenshot evidence и итоговые ограничения в отчёте.
- Finishing: применено правило AGENTS.md оставить всё unstaged. Commit/push/merge menu skills не используется, поскольку интеграцию выполняет только пользователь. Временный viewport override сброшен, новые worktrees не создавались.
- Проверка исправления сообщения Revert: 34 suites / 271 tests PASS, lint PASS, build PASS (существующее предупреждение о размере chunk). Локальный frontend-dev обновлён; замечание закрыто.
