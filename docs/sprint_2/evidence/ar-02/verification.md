# Приёмка AR-02 · 2 ноября 2026

## Независимость записи и доставки

До исправления тест с двумя подписчиками завершился по таймауту в ожидании быстрого клиента. После исправления тот же барьер остался закрытым, а быстрый подписчик получил сообщение и вызов публикации завершился.

В изолированной PostGIS выполнены POST, PATCH и DELETE через HTTP-маршруты FastAPI. Один тестовый транспорт заблокирован при первой отправке CRUD. До его освобождения проверены ответы всех трёх операций, данные событий у второго подписчика и независимые GET, включая 404 после удаления. Конфликтующий DELETE вернул 409. Управляемая блокировка делает результат воспроизводимым, численный сетевой SLA не измерялся.

| Проверка | Результат |
| --- | --- |
| Сервисы backend и HTTP API | 357 passed |
| Сквозной legacy CRUD и регрессии отзыва WebSocket-сессий на PostGIS | 9 passed |
| Frontend Vitest | Полный прогон 475/475. После добавления проверки позднего локального HTTP-ответа повторно запущены MapView и кеш тайлов, 31/31 |
| Производственная сборка фронтенда | Успех. Vite предупредил о размере основного чанка |
| ESLint и Ruff изменённых серверных модулей | Успех |
| Общий wiki lint | 37 прежних диагностик об отсутствии frontmatter в исходных материалах RAW_inputs |

Исходники проверок — [менеджер](../../../../apps/backend/utility_service/use_cases/tests/test_realtime_connection_manager.py) и [сквозной тест](../../../../apps/backend/tests/integration_tests/test_legacy_realtime_delivery.py). Для тестового прогона использованы отдельный Compose project и временная БД на tmpfs.

## Восстановление в браузере

Реальный headless Microsoft Edge открыл штатный компонент MapView в режиме editing. Стенд использовал Vite, однопроцессный API, настоящий WebSocket и PostGIS. Тестовая обвязка монтировала компонент напрямую и подавляла внешние растровые запросы подложки. Значения слоя проверялись в GeoJSON source MapLibre.

- Для пустой очереди с тестовым бюджетом 2048 байт другой клиент создал видимый объект со свойством длиной 3072 ASCII-символа. Запись вернула 201, браузер получил 1013.
- Браузерный перехватчик вернул 503 на пять последовательных запросов билета. Пока карта была отключена, другой HTTP-клиент создал, изменил и удалил ещё один объект.
- После снятия 503 карта получила новый билет, перечитала слой и показала крупный объект. Удалённый объект отсутствовал. Следующее небольшое обновление дошло по WebSocket, версия в источнике карты стала равна 2. Страница во время сценария не перезагружалась.

Результат повторного прогона: `{"temporaryTicketFailures":5,"closeCode":1013,"readback":true,"liveVersion":2}`. Тесты менеджера отдельно проверяют прохождение кадра ровно на границе байтового бюджета, превышение на один байт, переполнение по количеству, deadline, заблокированный session read и отзыв sid.

## Как повторить

Из корня репозитория в PowerShell задать уникальное имя Compose project, а также тестовые email и пароль через переменные окружения. Для браузера нужны установленные зависимости `apps/frontend`, `infra/m4` и Microsoft Edge. Использовать свободный loopback-порт 18762 и отдельную тестовую БД.

```powershell
$project = 'ar02-' + [guid]::NewGuid().ToString('N').Substring(0,8)
$env:AR02_EDITOR_EMAIL = "$project@example.com"
$env:AR02_EDITOR_PASSWORD = [guid]::NewGuid().ToString('N')
$compose = @('compose','-p',$project,'-f','infra/docker-compose.test.yml')
$fixture = (Resolve-Path 'docs/sprint_2/ar-02').Path
try {
    docker @compose run --build --rm backend_db_tests python -m pytest tests/integration_tests/test_legacy_realtime_delivery.py tests/integration_tests/test_browser_auth_websocket_revocation.py --tb=short
    if ($LASTEXITCODE) { throw 'Не пройдены интеграционные тесты' }
    docker @compose run -d --rm --name "$project-browser" -p 127.0.0.1:18762:8000 -e AR02_EDITOR_EMAIL -e AR02_EDITOR_PASSWORD -e LEGACY_GIS_API_ENABLED=true -e PYTHONPATH=/app:/fixture -v "${fixture}:/fixture:ro" backend_db_tests uvicorn browser_fixture:api --host 0.0.0.0 --port 8000 --no-access-log --log-level error
    if ($LASTEXITCODE) { throw 'Не запущен тестовый API' }
    $ready = $false
    foreach ($attempt in 1..60) {
        try { $ready = (Invoke-WebRequest http://127.0.0.1:18762/openapi.json -TimeoutSec 2).StatusCode -eq 200 } catch {}
        if ($ready) { break }
        Start-Sleep -Seconds 1
    }
    if (!$ready) { throw 'API не готов' }
    node docs/sprint_2/ar-02/browser.mjs
    if ($LASTEXITCODE) { throw 'Не пройдена браузерная проверка' }
} finally {
    docker stop "$project-browser"
    docker @compose down
}
```

## Проверка после ревью

Проверены защита от повторного появления удалённого UUID после подтверждённого 404, отсечение старого результата локальной записи, перенос между тайлами при опережающей странице bbox, чтение после первого connected и при быстрой смене слоя, ошибки фоновых страниц и завершение зависшего закрытия при shutdown. Ревьюер повторно проверил исправления и не обнаружил блокеров в этих сценариях. Область приёмки — локальный legacy GIS с одним процессом API.
