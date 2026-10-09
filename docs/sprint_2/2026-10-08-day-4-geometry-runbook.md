# Обновление geometry policy

Policy фиксируется в `EditVersion` при создании. Изменение конфигурации влияет только на новые версии. Reopen сохраняет прежние значения; прямой UPDATE policy запрещён триггером.

Перед миграцией остановить API. В одном и том же окружении для `migrate` и `utility_service` задать `UTILITY_GEOMETRY_XY_RESOLUTION` и `UTILITY_GEOMETRY_ROUNDING_MODE`. Например, grid `0.00000025` и `ROUND_HALF_AWAY_FROM_ZERO`. Значения по умолчанию: `0.0000001` и `ROUND_HALF_AWAY_FROM_ZERO`. JWT migrator не требуется.

Из корня репозитория, с обычным для развёртывания env-файлом:

```powershell
docker compose --env-file infra/demo.env -f infra/docker-compose.yml stop utility_service
docker compose --env-file infra/demo.env -f infra/docker-compose.yml --profile migrate run --rm --build migrate
```

Проверить успешное завершение миграции до запуска новой версии API:

```powershell
docker compose --env-file infra/demo.env -f infra/docker-compose.yml up -d --build utility_service
```

`infra/demo.env` предназначен только для demo; для другого окружения использовать соответствующий env-файл. Rolling deployment старого API с новой схемой не поддерживается: старый код не заполняет обязательные поля.

Revision `c8e3f0a5b7d9` выполняет однократный backfill всех существующих версий значениями окружения migrator. Геометрия, revision и история команд не пересчитываются. Неверные параметры останавливают migration до DDL; транзакция PostgreSQL защищает от частичного обновления.

Downgrade до `b7d2e9f4a6c8` удаляет сохранённые policy. Последующий upgrade повторно назначает всем версиям policy текущего окружения: это потеря прежнего контекста fingerprint, а не безопасное восстановление. Перед downgrade необходима резервная копия. Этот порядок следует выполнять при остановленном API.
