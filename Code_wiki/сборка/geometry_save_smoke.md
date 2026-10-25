---
title: Двухфазный API smoke сохранения геометрии
type: runbook
status: active
created: 2026-10-25
updated: 2026-10-25
source: "apps/backend/tests/smoke/save_geometry_smoke.py; apps/backend/tests/smoke/save_geometry_observer.py; apps/backend/tests/smoke/restart_backend_smoke.py; .github/workflows/ci.yml; infra/docker-compose.smoke.yml"
tags: [ci, smoke, edit-version, restart, idempotency]
---

# Двухфазный API smoke сохранения геометрии

## Контракт

`full_path_workspace_smoke.py` без параметров проверяет открытие workspace. Режимы `--phase save` и `--phase verify-retry-revert` образуют единый сценарий на fresh database. Между ними сохраняется та же БД и выполняется настоящий restart штатного backend с migrations/seeds. Browser recovery остаётся локальным M4, не частью этого CI gate.

Save работает через публичный API и сохраняет JSON schemaVersion=1 с runId, target, исходными CommandId/token/geometry, terminal response и SQL snapshots. Verify использует тот же запрос, а не новый CommandId с текущим token. После readback/replay выполняет четыре отказа по одному разу и Revert по baselineGeometry из HTTP readback.

Успех Save/replay/Revert требует HTTP 200. Stale/reused возвращают 409, invalid/outside — 422 с `{code,message,correlationId}`. Сценарий завершается revision=3, двумя change events, двумя succeeded и тремя rejected commands. Reused request/replay не добавляют записи. No-op/concurrency/rollback покрываются отдельными suites, не скрытыми подготовительными mutations этого smoke.

## Независимое доказательство

`save_geometry_observer.py` использует отдельную `REPEATABLE READ, READ ONLY` транзакцию. Он проверяет связь WorkOrder/EditVersion/DefaultState/feature, current и baseline EWKB, revision, полные command records и append-only события с before/after geometry. Проверяется геометрия baseline L-003; сравнение всех baseline features не заявляется.

Observer не выполняет сценарные записи. HTTP 200 сам по себе не доказывает отсутствие duplicate event: terminal result и SQL/history проверяются раздельно. Actor коррелируется через subject полученного login JWT и SQL owner; access token не сохраняется.

## Lifecycle и диагностика

`restart_backend_smoke.py` исполняется на host и использует stdlib + Docker CLI. Он требует новый StartedAt backend, его healthy и `/health`; StartedAt PostGIS должен остаться прежним. Прежний healthy не подтверждает restart.

CI экспортирует state на host до restart, затем передаёт его verify-фазе. Чужой, неполный или завершённый state блокируется до PUT. При начале verify статус меняется на verify-running; ошибка не разрешает незаметно повторить весь сценарий на накопленной БД. Следующий полный прогон требует нового окружения и runId.

Evidence сохраняет текущий этап до запроса, безопасные expected/actual HTTP status/code, контрольные SQL snapshots и причины внутренних assertions. Произвольный exception text, auth headers, пароли и environment dumps не публикуются. `actions/upload-artifact` выполняется перед cleanup также при ошибке; старый success-файл не доказывает новый прогон.

Для локального запуска `infra/docker-compose.smoke.yml` убирает fixed container_name и ports, заменяет persistent demo volume на tmpfs. Он применяется после base + demo Compose с уникальным project name. Один `-p` без override не обеспечивает изоляцию. Пользовательский demo не очищается и не перезапускается. Команды и диагностика: [runbook](../../docs/sprint_2/2026-10-25-day-13-smoke-runbook.md).

## Связи и обнаруженное расхождение

- [[архитектура/edit_version_save_orchestration]] — проверяемые транзакционные гарантии.
- [[архитектура/edit_version_api_readback]] — wire-контракт и baseline projection.
- [[сборка/ci_and_quality]] — общий CI; историческое описание в этой ноде говорит о DB integration внутри utility_service. Текущий workflow запускает их в отдельном geoservice-db-tests, что подтверждается `infra/docker-compose.test.yml` и `infra/db-tests.cmd`. Старую инструкцию нельзя использовать против пользовательского demo. Это обнаруженное расхождение требует отдельной синхронизации старой ноды; её текст в данном ingest не изменён.
- [[правила_и_стиль/testing_strategy]] — уровни проверок; описание прежнего smoke относится к вызову без фаз.
