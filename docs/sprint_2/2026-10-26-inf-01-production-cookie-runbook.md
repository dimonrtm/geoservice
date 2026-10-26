# INF-01: локальная проверка безопасного старта API

## Предварительные условия

- Windows с PowerShell 7 и Docker Desktop в режиме Linux containers.
- Доступ к Docker daemon и Docker Compose v2. Проверено на PowerShell 7.6.5, Docker client/server 28.1.1, Compose 2.35.1-desktop.1.
- Для сборки backend нужны доступ к registry/package sources либо подходящий build cache. Скрипт всегда выполняет build текущего checkout, но не отключает cache.

## Запуск

Из корня репозитория:

```powershell
pwsh -NoProfile -File docs/sprint_2/verify-inf-01.ps1
```

Из другой папки использовать абсолютный путь:

```powershell
pwsh -NoProfile -File C:/Repositories/geoservice/docs/sprint_2/verify-inf-01.ps1 -TimeoutSeconds 60
```

`TimeoutSeconds` допускает 10–300 секунд для ожидания каждого startup-сценария. Отдельная Docker-команда ограничена 30 секундами, HTTP probe — 5 секундами с сетевым timeout=2 внутри Python. Build ограничен 10 минутами. Ожидание startup может превысить заданное значение на длительность последнего Docker-вызова и cleanup.

Exit 0 означает прохождение всей матрицы, включая cleanup. Exit 1 — отказ проверки или очистки. Успешный вывод содержит версии Docker/Compose, уникальный project, prod image ID и строки `PASS` для base startup, отрицательного сценария, demo и cleanup.

## Что проверяется

1. Реальное описание API из base Compose: target `prod`, штатный `start_api.sh`, `DEV_MODE=false`, Secure=true.
2. Сборка production image из текущего backend и запуск через `compose run --no-deps` без переопределения положительного environment.
3. `GET /health` внутри контейнера: HTTP 200 и `{"ok": true}`; настоящий Settings подтверждает production-флаги.
4. Явное Secure=false в отдельном production-контейнере: процесс завершается ненулевым кодом с сообщением обязательной Secure cookie.
5. Объединение base + demo: DEV_MODE=true, Secure=false, target `dev`, прежний demo command. Settings проверяется в одноразовом контейнере production image с объединённым demo environment; demo startup не выполняется.

Проверка относится к API-сервису базового Compose. Это не полный `compose up`: PostGIS, migrations, seeds и frontend не запускаются. `/health` не проверяет БД. Браузерный HTTPS/login/refresh и INF-02/03/04 остаются вне объёма.

## Изоляция и очистка

Скрипт создаёт project `geoservice-inf01-<суффикс>`, уникальные container names и временный каталог с тем же именем. DB URL синтетический: loopback контейнера, порт 1; рабочая БД не используется. Порты не публикуются, volumes не подключаются.

CLI `--env-file` задаёт синтетические значения. Переменные интерполяции YAML, `COMPOSE_*`, `AUTH_SESSION_*` и `DEV_MODE` временно удаляются из process environment и восстанавливаются в `finally`. Приватные `.env` не читаются. Docker connection settings сохраняются, чтобы использовать выбранный пользователем daemon.

Cleanup сверяет project label и имена, удаляет только собственные контейнеры/сеть и два известных временных env-файла. Production images остаются в локальном Docker cache; скрипт печатает ID. Команды общего удаления volumes/images не выполняются.

При принудительном завершении PowerShell или Docker daemon `finally` может не выполниться. Для диагностики использовать точный project из вывода:

```powershell
docker ps -a --filter label=com.docker.compose.project=<project>
docker network ls --filter label=com.docker.compose.project=<project>
```

Перед ручным удалением сверить имя и label каждого ресурса. Не применять `down -v` к рабочему Compose.

## Диагностика

- Ошибка доступа к Docker — проверить запущенный Docker Desktop и разрешение доступа к daemon; это не RED по INF-01.
- Ошибка build — проверить registry/cache/network. Build output хранится только в памяти; вывод ошибки ограничен последними 1500 символами stderr с маскированием синтетических значений.
- `Base startup: AUTH_SESSION_COOKIE_SECURE должно быть true, если DEV_MODE=false` — ожидаемое воспроизведение исходного INF-01, если настройка отсутствует в base YAML.
- Иная ранняя остановка, неверный JSON, timeout или неожиданно работающий insecure API — провал проверки.

На PowerShell 7.6.5 `.NET SetEnvironmentVariable(name, $null)` может оставить пустую переменную вместо её отсутствия. Скрипт удаляет переменные через `Remove-Item Env:...`, иначе пустой host value перекрывает тестовый env-файл.

## Существующие тесты

Из корня репозитория:

```powershell
docker build --target dev -t geoservice-inf01-tests:local apps/backend
docker run --rm --network none --read-only --tmpfs /tmp -e PYTHONDONTWRITEBYTECODE=1 --mount "type=bind,source=$((Get-Location).Path),target=/repo,readonly" -w /repo/apps/backend --entrypoint python geoservice-inf01-tests:local -m pytest -p no:cacheprovider -rs utility_service/utils/tests/test_settings.py utility_service/web_api/tests/test_auth_api.py tests/test_compose_security_contract.py tests/test_compose_startup_contract.py
```

Полный checkout нужен, чтобы infra contract tests не были пропущены. Это отдельная проверка на dev image; production startup smoke использует target `prod`.
