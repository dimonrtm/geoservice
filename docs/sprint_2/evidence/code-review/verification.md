# Проверки ревью 2026-10-26

Исходный HEAD: `374853c5ca6a70477bba0f07cc9fe7ab1901bf85`.

## Backend

Из корня репозитория:

```powershell
docker run --rm --network none --read-only --tmpfs /tmp -e PYTHONDONTWRITEBYTECODE=1 -v C:/Repositories/geoservice/apps/backend:/app:ro -w /app --entrypoint python geoservice-day14-check:latest -m pytest -p no:cacheprovider utility_service/domain_services/tests utility_service/use_cases/tests utility_service/web_api/tests utility_service/utils/tests
```

Exit 0: `418 passed, 2 warnings in 36.66s`. Предупреждения: deprecated `crypt` в passlib и alias `anyio.abc.BlockingPortal` в Starlette TestClient. Это не результаты DB integration suite.

```powershell
docker run --rm --network none --read-only --tmpfs /tmp -e PYTHONDONTWRITEBYTECODE=1 -v C:/Repositories/geoservice:/repo:ro -w /repo/apps/backend --entrypoint python geoservice-day14-check:latest -m pytest -p no:cacheprovider tests/test_compose_security_contract.py tests/test_compose_startup_contract.py
```

Exit 0: `12 passed in 0.34s`. Полный checkout смонтирован только для чтения, чтобы infra tests не были пропущены.

## Изолированные воспроизведения

```powershell
docker run --rm --network none --read-only --tmpfs /tmp -e PYTHONDONTWRITEBYTECODE=1 -e DATABASE_URL=postgresql+asyncpg://unused:unused@localhost/unused -e DEV_MODE=true -e PYTHONPATH=/app -v C:/Repositories/geoservice/apps/backend:/app:ro -v C:/Repositories/geoservice/docs/sprint_2/evidence/code-review:/evidence:ro -w /app --entrypoint python geoservice-day14-check:latest /evidence/backend_probes.py
docker run --rm --network none --read-only --tmpfs /tmp -e PYTHONDONTWRITEBYTECODE=1 -e PYTHONPATH=/app -v C:/Repositories/geoservice/apps/backend:/app:ro -v C:/Repositories/geoservice/docs/sprint_2/evidence/code-review:/evidence:ro -w /app --entrypoint python geoservice-day14-check:latest /evidence/realtime_probe.py
```

Оба exit 0. Backend probe: 100 000 вершин, 800 132 байта, 0,578 s; PATCH передал `{}` в repository, вернул старые properties; PATCH с geometry и `{}` получил BusinessValidationException. Realtime probe: `slow_socket_blocks_fast_socket=true, network_used=false`. Проверяется настоящий код с имитациями внешних зависимостей; подключения к БД и реальной сети нет.

## Frontend

Из `apps/frontend`:

```powershell
npm.cmd run typecheck
npm.cmd run test -- --reporter=dot
npm.cmd run test -- --reporter=dot --maxWorkers=2
```

Typecheck exit 0. Первый sandbox test запуск не стартовал из-за `spawn EPERM`; после разрешённого запуска вне sandbox default workers дали 319/323 passed (4 failures). Повтор с двумя workers: exit 0, 44/44 файлов, 323/323 tests, 109,38 s. Список классов исходных сбоев и ограничения — в [frontend-review.md](../../frontend-review.md).

Числа здесь фиксируют реальные локальные запуски. Они не являются новым CI, браузерной приёмкой или нагрузочным benchmark. Новые regression tests из рекомендаций отчёта ещё не реализованы.
