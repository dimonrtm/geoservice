# AR-01: сводка проверок

Фактическая дата: 2026-10-28, Asia/Qyzylorda. JSON timestamps сохраняют UTC
2026-10-27T19:xxZ, что соответствует 2026-10-28T00:xx+05:00.

## Итоговые прогоны

| Scope | Evidence | Итог |
| --- | --- | --- |
| Основные 12 cases, Chrome/Edge/Playwright Firefox | [geoservice-ar01-d19c8b14](geoservice-ar01-d19c8b14/verification.json) | 36/36 PASS, cleanup PASS |
| Дополнительный настоящий history back, все три browsers | [geoservice-ar01-2650573a](geoservice-ar01-2650573a/verification.json) | 3/3 PASS, BFCache=false, cleanup PASS |
| Уточнение logout/lost-marker SLA от dispatch, все три browsers | [geoservice-ar01-fa950f3c](geoservice-ar01-fa950f3c/verification.json) | 6/6 PASS, cleanup PASS, hashes использованных runner files |
| Backend полные gates контроллера | [backend-final-checks.md](backend-final-checks.md) | prod image, Black/Ruff, 675 standard + 310 DB PASS |

Основной запуск: `node docs/sprint_2/ar-01/run.mjs chrome msedge firefox`.
Дополнения используют `AR01_CASE=real_history_resume` и затем
`AR01_CASE=logout_revokes,lost_marker`; `scope` сохраняется в каждом browser JSON.
13 различных cases проверены в каждом из трёх браузеров. Повторные SLA cases
не прибавляются к этому числу. Browser versions/executables и runner hashes
содержатся в JSON; Firefox157.0 — сборка Playwright revision1555, не stock.

Обычный logout, консервативная верхняя граница dispatch→login UI:
Chrome1994 ms, Edge1976 ms, Firefox161 ms. Потерянный marker + старый active:
Chrome2647 ms, Edge3036 ms, Firefox2549 ms. Во всех наблюдаемых status flows
max concurrent=1, protected requests до свежего resume gate=0.

Final frontend: `npm test` → 52 files, 438 passed, 53.50 s;
typecheck/lint/build PASS. Prettier проверил все 26 изменённых TS/Vue files,
включая untracked. Два новых mjs отформатированы локальным Prettier; Node syntax
checks PASS. Build сохраняет baseline chunk warning >500 kB. npm печатал
собственное уведомление об обновлении CLI.

Focused PostgreSQL lane в собственном tmpfs harness: отдельная `_test` DB,
PostGIS extension, repository/races → 18 passed, 0 skipped, ~8.8 s; один
passlib/crypt warning. Deferred revoked parent expiry assertion включён.
Black/Ruff этого test file PASS. Полные backend gates не повторялись после
неизменённого production backend; их происхождение явно приведено выше.

Wiki lint после отдельного repository-change ingest и post-ingest correction:
37 baseline `missing_frontmatter` только в старых RAW; новых ошибок нет.
`git diff --check` PASS. Байтовая проверка изменённых tracked/untracked текстов:
UTF-8, без BOM/CR (LF). `git ls-files --eol` дополнительно подтверждает LF
tracked paths. JSON privacy check: 21 files, raw credential/body/header keys
и JWT strings не обнаружены; содержимое дополнительно просмотрено по schema.
Все изменения unstaged, staged diff пуст; git add/commit/push не выполнялись.

## Промежуточные результаты

Неудачные manifests сохранены для воспроизводимости; они не включены в PASS:

- `geoservice-ar01-c05286d6`: sandbox subprocess failure до Docker; cleanup
  первоначально не подтверждён. Оставшийся exact temporary path проверен и
  отдельно удалён; Docker resources не создавались.
- `geoservice-ar01-6f7b08db`: неверный targeted test path, cleanup PASS.
- `geoservice-ar01-041d07d9`: `_test` DB-name isolation guard, cleanup PASS.
- `geoservice-ar01-689b51d1`: PostGIS extension отсутствовала во второй DB,
  setup исправлен, cleanup PASS.
- `geoservice-ar01-f62505b1`: начальные ошибки assertions runner, включая
  route.fetch shared cookie side effect; cleanup PASS.
- `geoservice-ar01-1f5a62d9`: production RED lock-timeout message и ещё
  неисправленные runner assertions; cleanup PASS. Production issue согласован
  и исправлен TDD, основной финальный browser gate зелёный.
- `geoservice-ar01-9041e474`: supplemental setup остановлен неверной проверкой
  tmpfs через `.Mounts`; проверка исправлена на `.HostConfig.Tmpfs`, cleanup PASS.

Первый full frontend до Task8 delta: 436/436 PASS. TDD согласованного delta:
1 failed/14 passed → 25/25 focused GREEN; финальный полный suite — 438/438.
Sandbox `spawnSync git EPERM` byte-check повторён с escalation и прошёл.
Ошибочная попытка root `npx prettier` закончилась npm cache EEXIST; dependency
install не выполнен, затем использован установленный локальный executable.

## Явные границы

Fresh-resume fence: injected pageshow в настоящем document + настоящие status
HTTP. History back: настоящая browser navigation с пересозданием document.
Native BFCache прежнего runtime/OS suspend не доказаны. Один static diagnostic
с отключением Chromium BFCache-disable argument остановился на Playwright
ожидании load; отсутствие load не доказывает провал BFCache и не является
результатом application acceptance. Видимый GUI и пользовательские profiles
не использовались.

Localhost вместо внешнего HTTPS; нагрузочное измерение и production deployment
не выполнялись. Single-worker active WebSocket close описан в runbook; новые
проверки sid подтверждены DB/API/browser evidence. AR-02 и WorkOrder lock вне scope.

## Проверка review correction runner — 2026-10-28

`node --test docs/sprint_2/ar-01/acceptanceResult.test.mjs`: RED 5 failed/2 passed,
GREEN 7/7, skipped0. Проверены сохранённый JSON после успешного case и ошибки
следующего setup/context cleanup/browser cleanup/persist, а также stale PASS
при catch recovery. Аварийный результат теперь всегда failed, даже если
накопленные cases были успешны. Existing complete browser manifests остаются
evidence своих завершённых запусков; их hashes не подменялись. Полные suites
по scope review не повторялись. Новых credential artifacts не создано.

## Проверка final review minor — 2026-10-28

`node --test docs/sprint_2/ar-01/acceptanceSignals.test.mjs`: первоначально
3 assertion failures до появления helper; затем функциональный RED с прежним
неограниченным ожиданием — 1 test timeout (1000 ms)/2 passed, exit1.
`node --test docs/sprint_2/ar-01/acceptanceResult.test.mjs docs/sprint_2/ar-01/acceptanceSignals.test.mjs`:
GREEN 10 passed, 0 failed/cancelled/skipped, exit0. Это новые focused Node
проверки lifecycle/сигналов; Playwright/browser suites заново не выполнялись.

Production bound сигнала — 15000 ms; тест отсутствующего сигнала использует
10 ms и проверяет safe error, failed outcome и освобождение route barrier до
cleanup. Также проверены значение успешного сигнала и все barriers при ошибке
action. Node syntax checks трёх изменённых mjs и локальный Prettier PASS.
Post-ingest correction по `FU-2026-10-28-001` меняет только устаревшее объяснение
restoreGeneration/sessionEpoch в `Code_wiki/архитектура/frontend.md`.
Прежние browser manifests/hashes сохранены. Итоговый review и scoped re-review исправлений завершены без открытых замечаний; [отчёт ревью](../../2026-10-27-ar-01-browser-session-final-review.md).
