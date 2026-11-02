# BE-03 · Результаты проверки 02.11.2026

Проверено рабочее дерево на базе `cb3179b`. Исполнялся штатный ASGI backend через Uvicorn в одном процессе, с включённым legacy, пулом 5 + 5 и изолированной PostGIS. Клиент открывал реальные сокеты через loopback, получая отдельный ticket по HTTP на каждый. Во время замеров рассылка событий отсутствовала.

| Момент наблюдения | Подписки на слой в менеджере | Выдано из пула | Idle in transaction |
|---|---:|---:|---:|
| После подготовки и чтения исходной геометрии | 0 | 0 | 0 |
| После получения 11 сообщений `connected` | 11 | 0 | 0 |
| После Auth, Save и повторного чтения workspace | 11 | 0 | 0 |

Число выданных соединений получено из `engine.sync_engine.pool.checkedout()` внутри процесса. Состояния транзакций прочитаны отдельным подключением из `pg_stat_activity` для той же БД с исключением собственного PID и фильтром `state LIKE 'idle in transaction%'`.

`GET /api/v1/auth/me` вернул HTTP 200 и идентификатор ожидаемого редактора. PUT геометрии вернул HTTP 200 и `commandState=succeeded`. Исходная геометрия отличалась от отправленной, повторное чтение вернуло отправленную геометрию. Каждый из тех же 11 клиентов получил pong после повторного чтения.

## Регрессия и команды

- На исходном маршруте `test_subscription_releases_db_session_before_connect` упал по порядку событий. Менеджер начал проверку родительской сессии до выхода из DB-контекста. После изменения обе DB-службы получают одну наблюдаемую сессию, а к моменту проверки менеджером она уже закрыта.
- Целевые тесты маршрута, менеджера и ticket — 36 passed. Набор `utility_service/use_cases/tests utility_service/web_api/tests` — 351 passed. Два предупреждения относятся к `passlib/crypt` и `Starlette/BlockingPortal`. Black и Ruff прошли для трёх изменённых Python-файлов.
- Интеграционные проверки отзыва сессии на PostGIS — 8 passed, одно предупреждение `passlib/crypt`. Независимое статическое ревью предложило проверить передачу одного экземпляра сессии обоим сервисам. В тест добавлены обе проверки.

Команды внутри backend dev image, рабочий каталог `/app`:

```sh
python -m pytest -p no:cacheprovider utility_service/web_api/tests/test_ws_layers.py -k releases_db_session_before_connect --tb=short
python -m pytest -p no:cacheprovider utility_service/web_api/tests/test_ws_layers.py utility_service/use_cases/tests/test_websocket_ticket_service.py utility_service/use_cases/tests/test_realtime_connection_manager.py --tb=short
python -m pytest -p no:cacheprovider utility_service/use_cases/tests utility_service/web_api/tests --tb=short
```

Команды стенда из корня репозитория. Разовый сценарий был смонтирован из временной папки хоста. После прогона контейнеры и сеть проекта удалены.

```powershell
docker compose -p geoservice-be03-424924e6 -f infra/docker-compose.test.yml run --build --rm backend_db_tests python -m pytest tests/integration_tests/test_browser_auth_websocket_revocation.py --tb=short
docker compose -p geoservice-be03-424924e6 -f infra/docker-compose.test.yml run --rm -e LEGACY_GIS_API_ENABLED=true -e PYTHONPATH=/app -v C:/Users/dimon/AppData/Local/Temp/geoservice-be03-424924e6-acceptance.py:/tmp/be03.py:ro backend_db_tests python /tmp/be03.py
docker compose -p geoservice-be03-424924e6 -f infra/docker-compose.test.yml down --volumes --remove-orphans
```
