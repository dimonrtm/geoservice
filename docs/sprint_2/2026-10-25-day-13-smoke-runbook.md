# День 13: запуск API smoke

Сценарий проверяет Save L-003 в WO-001, restart штатного backend, readback, точный replay, четыре отказа и Revert. Браузерный M4 остаётся отдельным локальным запуском `npm.cmd test` из `infra/m4`.

## Предусловия

- Docker Compose с поддержкой `!reset`/`!override` (сначала `config --quiet`), Python 3 на host, текущие исходники backend.
- Fresh disposable БД на каждый полный прогон. Не запускать новые фазы на пользовательском demo. Старый вызов без `--phase` по-прежнему только открывает workspace.
- Между Save и verify БД не сбрасывается. Restart только utility_service повторяет штатные Alembic/seeds; SQL observer ничего не пишет.
- Локальный override `infra/docker-compose.smoke.yml` убирает fixed container names и опубликованные порты, заменяет demo volume на tmpfs. Самостоятельно `-p` этого не обеспечивает. CI использует исходные Compose-файлы на новом hosted runner.
- Pre-commit проверяет только этот override отдельным `check-yaml --unsafe`: режим разбирает YAML-синтаксис без создания объектов и допускает Compose-теги. Остальные YAML проходят обычный strict hook. Семантику объединения файлов проверяет `docker compose ... config --quiet`.

## PowerShell: полный локальный прогон

Запуск из корня репозитория. Если `python` указывает на Windows Store alias, заменить только `$pythonExe` на доступный Python 3 executable. Все проверки используют отдельный project; пользовательский demo не останавливается.

```powershell
$pythonExe = 'python'
$runId = [guid]::NewGuid().ToString()
$project = 'geoservice-day13-' + $runId.Substring(0, 8)
$evidenceDir = Join-Path (Get-Location) ('.tmp-tests/day13-' + $runId)
$composeArgs = @('compose', '--env-file', 'infra/demo.env', '-p', $project,
    '-f', 'infra/docker-compose.yml', '-f', 'infra/docker-compose.demo.yml',
    '-f', 'infra/docker-compose.smoke.yml')
function Invoke-SmokeCompose {
    & docker @composeArgs @args
    if ($LASTEXITCODE -ne 0) { throw "Compose exit $LASTEXITCODE" }
}
New-Item -ItemType Directory -Path $evidenceDir -Force | Out-Null
try {
    Invoke-SmokeCompose config --quiet
    Invoke-SmokeCompose up -d --build --wait postgis utility_service
    Invoke-SmokeCompose exec -T utility_service python tests/smoke/full_path_workspace_smoke.py
    Invoke-SmokeCompose exec -T utility_service python tests/smoke/full_path_workspace_smoke.py `
        --phase save --run-id $runId --state-file /tmp/day13-smoke/state.json `
        --evidence-file /tmp/day13-smoke/save.json
    Invoke-SmokeCompose cp utility_service:/tmp/day13-smoke/state.json (Join-Path $evidenceDir 'state.json')
    & $pythonExe apps/backend/tests/smoke/restart_backend_smoke.py `
        --manifest (Join-Path $evidenceDir 'restart.json') --run-id $runId -- docker @composeArgs
    if ($LASTEXITCODE -ne 0) { throw 'Restart/readiness failed' }
    Invoke-SmokeCompose cp (Join-Path $evidenceDir 'state.json') utility_service:/tmp/day13-smoke/state.json
    Invoke-SmokeCompose exec -T utility_service python tests/smoke/full_path_workspace_smoke.py `
        --phase verify-retry-revert --run-id $runId --state-file /tmp/day13-smoke/state.json `
        --evidence-file /tmp/day13-smoke/verify.json
} finally {
    & docker @composeArgs cp utility_service:/tmp/day13-smoke/. $evidenceDir
    & docker @composeArgs logs --no-color --tail=200 utility_service > (Join-Path $evidenceDir 'backend.log')
    if ($project -notmatch '^geoservice-day13-[0-9a-f]{8}$') { throw 'Unsafe cleanup target' }
    & docker @composeArgs down --volumes --remove-orphans
    if ($LASTEXITCODE -ne 0) { throw "Cleanup failed: $project" }
}
```

Не использовать глобальный prune, не удалять `geo_pgdata`, не запускать обычный demo `down -v`. При аварийном завершении убрать только project из конкретного запуска. Файлы `.tmp-tests` остаются локальной диагностикой. При успешной приёмке JSON можно сохранить в `docs/sprint_2/evidence/day-13/<runId>/`; credentials не включать.

## Что считается успешным

- Обе фазы exit 0, `save.json` и `verify.json` имеют status=passed, `state.json` status=complete; все runId одинаковы.
- `restart.json`: status=passed, startedBefore отличается от startedAfter, databaseStartedBefore равен databaseStartedAfter.
- Revision `1 → 2 → 2 → 3`; два события, пять команд: две succeeded и три rejected. Reused CommandId не добавляет строку.
- Коды: DRAFT_VERSION_STALE/COMMAND_ID_REUSED — 409; GEOMETRY_INVALID/GEOMETRY_OUTSIDE_AOI — 422.
- Baseline EWKB L-003 одинаков в стартовом, промежуточных и финальном снимках; после Revert current EWKB равен baseline.

Проверка actor сопоставляет subject полученного login JWT с SQL owner. Access token не сохраняется и может меняться после restart. Промежуточный JSON содержит синтетические geometry/IDs и terminal command results, не credentials.

## Диагностика и повтор

Любая ошибка завершает фазу exit 1. `errorType` не раскрывает exception text SQL/HTTP, который мог содержать секреты. Для внутренних assertions сохраняется безопасная `reason`; HTTP checks записывают expected/actual status/code, SQL checks — контрольные snapshots до assertions. Поле stage указывает текущую границу; status=failed/running не является успехом. Для детального анализа использовать ограниченный backend log и assertions в `tests/smoke/save_geometry_smoke.py`, не публиковать auth/environment dumps.

При ошибке или прерывании verify state больше не `save-complete`; повтор этой фазы запрещён. Начать новый полный прогон с новым project/runId и fresh БД. Повторный Save на изменённой БД также провалит preflight. Повреждённый, чужой, неполный или завершённый state отвергается до mutation.

В CI evidence загружается через `actions/upload-artifact` перед cleanup при успехе и ошибке, срок хранения семь дней. Название `day13-smoke-<github.run_id>-<github.run_attempt>`. Автоматический повтор сценария не используется. Запуск команд локально не доказывает, что GitHub Actions уже прошёл.

## Suites

- Backend: `pytest`, `black --check .`, `ruff check .` в backend dev image.
- Изолированная БД: `infra\db-tests.cmd`; никогда не подменять этим demo DATABASE_URL.
- Frontend из `apps/frontend`: `npm.cmd test -- --maxWorkers=2`, `npm.cmd run typecheck`, `npm.cmd run lint`, `npm.cmd run format:check`, `npm.cmd run build`.
- Browser из `infra/m4`: `npm.cmd test`. При первом запуске `npm.cmd ci` и `npx.cmd playwright install chromium`.
