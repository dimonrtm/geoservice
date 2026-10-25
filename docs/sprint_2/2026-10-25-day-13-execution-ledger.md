# Журнал исполнения — план: docs/sprint_2/2026-10-25-day-13-smoke-plan.md

Пользователь разрешил реализацию. Спецификация принята. Исполнение в текущем чате.

- Ruling: сохраняется checkout `first-edit-save` с документами обсуждения — пользователь не просил новый worktree, правила окружения предпочитают текущий подходящий checkout; риск изоляции ограничивается существующей веткой, чужие изменения не перезаписываются.
- Ruling: журнал ведётся в docs/sprint_2 вместо commit-based scratch scripts skills — пользователь запретил staging/commit/push и назначил папку артефактов; восстановление прогресса опирается на этот журнал и рабочие файлы.
- Pre-flight: задачи 1→2→3 используют единые HTTP/state/observer interfaces; задача 4 использует CLI задачи 1. Конфликтов нет.
- Исходная проверка: `pytest tests/smoke -q` в отдельном контейнере с read-only исходниками — 10 passed. Предупреждение pytest cache связано с read-only mount; дальнейшие запуски используют `-p no:cacheprovider`.
- Пользовательский demo stack обнаружен, не изменяется и не перезапускается.

## Задачи

- 1: complete — HTTP error decoding/state RED→GREEN; CLI завершён вместе с задачей 3.
- 2: complete — observer integration RED→GREEN; Save phase RED→GREEN.
- 3: complete — verify/replay/rejections/revert RED→GREEN; после review-fix 47 smoke tests passed, включая CLI и restart wait.
- 4: complete — CI steps/runbook, fresh live Save → restart → verify/retry/revert exit 0; fail-closed live проверки exit 1 с неизменным SQL snapshot; remote GitHub Actions не запускался.
- 5: complete — backend 647 passed/270 skipped после review-fix; frontend 323 passed, typecheck/lint/format/build exit 0; isolated DB 271 passed; M4 7 passed. Итоговые данные — в implementation report.

## Решения и диагностика

- Ruling: локальная изоляция через небольшой `infra/docker-compose.smoke.yml`, разрешённый спецификацией, вместо требования отдельной VM — удаляет fixed names/ports и использует tmpfs; риск неверного merge ограничивается проверкой config и отдельным project. Это не второй полный runner.
- Ruling: restart predicate выделен в stdlib helper `restart_backend_smoke.py`, общий для CI/runbook — позволяет проверить отказ на прежний healthy и timeout без brittle grep YAML; дополнительные файлы ограничены тестовым harness.
- Live preflight выявил неверное поле ownerId в тестовой workspace fixture. Реальный workspace его не возвращает; ошибка до PUT. Regression RED на точной форме, затем проверка JWT subject ↔ SQL owner GREEN; product API не менялся.
- Первый live run 1301 не принят (KeyError до PUT). Для следующего полного прогона создана fresh БД; результаты 1301 не выдаются за success.
- Sandbox esbuild EPERM и Docker pipe access denied устранены предусмотренной эскалацией, не обходом ограничений.
- Final review: отдельный агент выявил два Important: любые 2xx вместо 200 для успешного PUT и потеря текущей причины в failure evidence. Оба воспроизведены четырьмя RED tests, затем исправлены: 47 smoke tests GREEN. Critical/Minor и declined-to-judge отсутствуют.
- Исправления review: exact 200 для Save/replay/Revert; checkpoint перед запросом, безопасные expected/actual status/code, SQL snapshots до assertions и текст только harness-authored assertion. Произвольный exception/message не сериализуется.
- Backend до review-fix: 643 passed, 270 skipped (DB-only), 2 прежних warnings. Frontend 323/323, DB 271/271, M4 7/7. После review-fix повторяются backend и live API smoke; frontend/product/DB observer не изменялись.
- Финал: backend 647 passed/270 skipped; fresh live run 1303 прошёл обе фазы и restart. Неверный runId и completed state проверены на живой БД с неизменным snapshot. Контейнеры geoservice-day13-final, geoservice-db-tests и M4 удалены их собственным lifecycle; обычный demo остался запущен.
- Артефакты: 32 изменённых/новых текстовых файла проверены на UTF-8/LF, git diff --check чистый; evidence проверен по runId/counters/baseline/StartedAt, скан credentials чистый. Индекс Git не менялся.
- Завершение по правилам репозитория: текущая ветка и unstaged изменения сохранены для review пользователя; меню merge/push из finishing skill не применяется из-за прямого запрета Git-операций. Agent memory не обновляется: уникальные контракты сохранены в runbook/Code_wiki.
