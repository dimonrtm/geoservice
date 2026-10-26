# INF-01: отчёт реализации

Дата: 2026-10-26. Основание: [принятая спецификация](2026-10-26-inf-01-production-cookie-design.md), [план](2026-10-26-inf-01-production-cookie-plan.md).

## Результат

В base `utility_service.environment` добавлено `AUTH_SESSION_COOKIE_SECURE: "true"`; в demo override — `"false"`. Production API запускается со штатным Settings/startup; явная insecure production-конфигурация по-прежнему отклоняется. Backend-код, миграции, seeds, frontend и CI не менялись.

Добавлен [локальный smoke](verify-inf-01.ps1) и [runbook](2026-10-26-inf-01-production-cookie-runbook.md). Все проверки выполнялись самим агентом в текущем чате, без субагентов. Изменения не staged и не committed.

## Выполненные проверки

Команда RED/GREEN из корня checkout:

```powershell
pwsh -NoProfile -File docs/sprint_2/verify-inf-01.ps1
```

Среда: PowerShell 7.6.5, Docker client/server 28.1.1, Compose 2.35.1-desktop.1. Сборки выполнены из текущего checkout с обычным Docker cache; это не доказательство воспроизводимости всех внешних зависимостей.

| Проверка | Результат |
| --- | --- |
| RED до изменения YAML, project `geoservice-inf01-f778e82e7292` | Exit 1; настоящий API остановился с `AUTH_SESSION_COOKIE_SECURE должно быть true, если DEV_MODE=false`; cleanup прошёл |
| GREEN после изменения YAML, project `geoservice-inf01-79b1b6cace1c` | Exit 0; вся матрица smoke прошла |
| Base API HTTP | `/health` вернул HTTP 200 и `{"ok": true}` |
| Runtime Settings | DEV_MODE=false, Secure=true |
| Отрицательный startup | Secure=false привёл к ненулевому завершению и ожидаемой ошибке валидатора |
| Demo merge и Settings | DEV_MODE=true, Secure=false; target dev и demo command сохранены; Settings валиден |
| Cleanup | Контейнеры и сеть проверки удалены после RED и GREEN |
| Существующая regression | 51 passed, 2 warnings, 5.36 s; skips отсутствуют |
| Иной cwd и конфликтующие host env | Повторная полная матрица прошла; исходные переменные вызывающего процесса восстановлены |

Prod image ID RED: `sha256:c9b315ff68bf6c9e21c49c0af8293e1a98f02005e159d65b223177cc2e275148`.

Prod image ID GREEN: `sha256:4df8d86652f4eb223d155a5025db611b26b7df5bf5b3fdbd9cb06cc88f00eb57`.

Повтор из временной папки, project `geoservice-inf01-3583bd3fc743`, prod image ID: `sha256:a090710cf273ee2d002714f6d9e698a755bf559e62f51fb92400df5096b09aa2`.

Для последнего запуска намеренно заданы конфликтующие `DB_NAME`, `DATABASE_URL`, `AUTH_SESSION_COOKIE_SECURE=false`, `COMPOSE_FILE=missing-host-compose.yml`, `CORS_ORIGINS=*`. После smoke отдельно проверено восстановление всех пяти значений. Полные environment и config не сохранялись.

Regression запускалась после `docker build --target dev -t geoservice-inf01-tests:local apps/backend`:

```powershell
docker run --rm --network none --read-only --tmpfs /tmp -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=C:/Repositories/geoservice,target=/repo,readonly -w /repo/apps/backend --entrypoint python geoservice-inf01-tests:local -m pytest -p no:cacheprovider -rs utility_service/utils/tests/test_settings.py utility_service/web_api/tests/test_auth_api.py tests/test_compose_security_contract.py tests/test_compose_startup_contract.py
```

Предупреждения относятся к deprecated alias `anyio.abc.BlockingPortal` в Starlette и `crypt` в passlib. Эти зависимости в INF-01 не менялись.

## Диагностика при разработке проверки

Первый sandbox-запуск не имел доступа к Docker; дальнейшие проверки выполнены с разрешённым доступом. Затем выявлено, что очистка env через `.NET SetEnvironmentVariable(name, $null)` в PowerShell 7.6.5 оставляет пустое значение, которое перекрывает test env-file. Независимая проверка показала наличие ключа после этого вызова и отсутствие после `Remove-Item Env:...`; скрипт исправлен. Эти неудачные попытки не засчитывались как RED приложения.

## Границы доказательства и документация

Это фактический запуск API из base Compose через `run --no-deps`, а не приёмка всего стека `up`. PostGIS, migrations, seeds и frontend не запускались; рабочие БД/volumes не использовались. Demo проверен по merged config и Settings, без браузерного сценария. HTTPS/login/refresh и новый CI gate не входят в согласованный результат.

Самопроверка подтвердила: положительный запуск не подставляет Secure через CLI; отрицательный проверяет конкретную причину отказа; cleanup ограничен уникальными именами и project labels; текстовые файлы имеют LF. Исходные материалы ревью и изменения README сохранены.

Отдельная agent-memory запись и repository-change ingest не выполнялись: новая политика непосредственно выражена двумя строками YAML, существующий auth-контракт уже описан в Code_wiki; уникальные эксплуатационные детали локальной проверки сохранены в runbook.
