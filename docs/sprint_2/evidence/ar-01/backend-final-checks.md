# AR-01: итоговые backend gates

Проверены контроллером 2026-10-28 после финального Task4; перенесены в публичное
evidence из `.superpowers/sdd/2026-10-27-ar-01-browser-session-plan/backend-final-checks.md`.
Task8 не меняет production backend и не повторяет неизменённые полные lanes.

| Команда / проверка | Результат |
| --- | --- |
| `docker build --target prod -t geoservice-ar01-backend-prod apps/backend` | PASS; image `sha256:c43e949bbf6a85e4321b0b6ffff2e3412612dd2b55d31c35ab16fb977e2dbab1` |
| `docker run --rm -v C:/Repositories/geoservice/apps/backend:/app --entrypoint python utility_service:dev -m black --check .` | 333 files unchanged, exit 0 |
| Та же dev-среда, `python -m ruff check .` | All checks passed, exit 0 |
| Та же dev-среда, `python -m pytest --tb=short` | 675 passed, 309 skipped, 1 warning, 30.26 s |
| `cmd /c infra\db-tests.cmd` | Fresh build/tmpfs, миграции от пустой и legacy схемы, 310 passed, 0 skipped, 2 warnings, 58.86 s; cleanup/exit 0 |

309 skipped в стандартном pytest — opt-in DB lane, который отдельно выполнен
штатной командой, а не пропущен. Warnings: passlib/crypt DeprecationWarning;
в свежем DB image также Starlette testclient: deprecated
`anyio.abc.BlockingPortal` alias, использовать `anyio.from_thread.BlockingPortal`.
Ожидаемые отрицательные constraint/lock-timeout сценарии прошли.

Task8 дополнительно усиливает один repository assertion: после попытки продлить
отозванного parent `expires_at` должен остаться прежним `extended`. На новой
отдельной tmpfs `_test` БД реально выполнены
`test_browser_auth_session_repository.py` и
`test_browser_auth_session_races.py`: 18 passed, 0 skipped, passlib warning.
Результаты конкретных запусков — в `verification.json` browser harness.
Black/Ruff этого единственного изменённого backend test — PASS.
