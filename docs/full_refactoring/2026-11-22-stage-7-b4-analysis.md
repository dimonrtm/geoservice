# Этап 7 (B4). Граница между публикацией изменений слоя и WebSocket

22 ноября 2026 года. Исходное состояние проверено на `0304fbc`. Пользователь согласовал критерий совместимости и выбрал отдельную функцию формирования сообщений в WebSocket-адаптере. [Принятый дизайн B4](2026-11-22-stage-7-b4-design.md).

Исходные импорты и расположение типов описаны по указанной ревизии. Ссылки на перенесённые файлы ведут к их расположению после B4.

## Что требуется от B4

Порядок рефакторинга задаёт узкую операцию публикации, привязку к существующему менеджеру при сборке приложения и перенос самого менеджера в транспортный адаптер. Критерии готовности включают независимость прикладного издателя от FastAPI WebSocket manager, совместимость протокола и сохранение диагностики, ограничений очереди и закрытия соединений. Доставка остаётся best-effort в пределах одного процесса. [Этап 7](refactoring-order.md#этап-7-переместить-транспорт-realtime--b4), [замечание B4](architecture-review.md#b4-websocket-transport-находится-в-прикладном-слое), [принятый контракт доставки AR-02](../sprint_2/2026-11-02-ar-02-design.md).

В DDD-модели обновления слоя принадлежат поддерживающему поддомену Generic Map Editing. Например, `feature_updated` сообщает карте о новой версии объекта слоя. Открытие рабочей версии наряда имеет собственное доменное событие `Edit Version Opened`, а загрузка workspace описана как чтение по HTTP. Эти материалы не дают основания связывать B4 с Save/Revert, аудитом наряда или изменением модели рабочей версии. [Generic Map Editing](../../DDD_Wiki/subdomains/generic_map_editing.md), [Edit Version Opened](../../Wiki/domain_events/edit_version_opened.md), [Workspace Loaded](../../Wiki/system_events/workspace_loaded.md).

## Путь изменения от записи до сокета

| Участок | Наблюдаемое поведение текущего кода |
| --- | --- |
| Запись слоя | После выхода из успешной транзакции create/update/delete сервис создаёт контекст с `eventId`, слоем, объектом и версией. Если публикация выбрасывает исключение, сервис регистрирует сбой и возвращает результат записи. Для удаления передаётся последняя живая версия объекта. [FeatureService](../../apps/backend/utility_service/use_cases/services/feature_service.py), [интеграционные проверки commit и ошибок](../../apps/backend/tests/integration_tests/test_legacy_realtime_diagnostics.py). |
| Подготовка сообщения | `FeatureRealtimePublisher` импортирует конкретный `WebSocketConnectionManager`. Для трёх видов изменения издатель передаёт ему контекст и функцию построения словаря. В этой функции заданы `eventId`, `occurredAt`, `layerId` и либо `feature`, либо `featureId` и `deletedVersion`. Формат кадра читает frontend. [Издатель](../../apps/backend/utility_service/use_cases/services/feature_realtime_publisher.py), [контракт клиента](../../apps/frontend/src/contracts/realtime.ts). |
| Выбор адресатов | `publish_event` синхронно снимает список подписок конкретного слоя. При пустом списке функция построения сообщения не вызывается. Для остальных сообщение готовится и сериализуется один раз. При исключении в ходе постановки в очередь диагностика охватывает текущего и оставшихся адресатов. Успешно поставленные в очередь кадры сохраняются. [Менеджер](../../apps/backend/utility_service/web_api/realtime/realtime_connection_manager.py), [проверки пустого списка и частичной публикации](../../apps/backend/utility_service/web_api/tests/test_realtime_publication_diagnostics.py). |
| Отправка | У каждого сокета своя FIFO-очередь и задача отправки. Лимит — 32 **ожидающих** кадра и 1 МиБ их суммарного размера в UTF-8. Текущий кадр уже снят с учёта очереди. Перед отправкой каждого кадра, включая `connected`, проверяется активность сессии. Медленный сокет не удерживает HTTP-ответ и отправку быстрому подписчику. [Менеджер](../../apps/backend/utility_service/web_api/realtime/realtime_connection_manager.py), [проверки лимитов](../../apps/backend/utility_service/web_api/tests/test_realtime_connection_manager.py), [сценарий с двумя подписчиками и HTTP CRUD](../../apps/backend/tests/integration_tests/test_legacy_realtime_delivery.py). |

## Кто ещё зависит от менеджера

- **Выдача допуска.** Тип `WebSocketUserContext` объявлен рядом с очередями и сокетами, хотя его создаёт `WebSocketTicketService.consume_ticket`. Его используют также проверка ticket и маршрут подписки. Тип содержит `user_id`, `email`, `role` и `session_id`. После проверки ticket и слоя маршрут освобождает сессию БД до подключения. Менеджер проверяет актуальность браузерной сессии ещё раз до `accept`. Это защищает случай, когда logout успел завершиться между погашением ticket и подключением. [Сервис ticket](../../apps/backend/utility_service/use_cases/services/websocket_ticket_service.py), [проверка ticket](../../apps/backend/utility_service/utils/websocket_ticket_auth.py), [маршрут](../../apps/backend/utility_service/web_api/api/ws_layers.py), [тесты отзыва](../../apps/backend/tests/integration_tests/test_browser_auth_websocket_revocation.py).
- **Сборка и время жизни.** Lifespan создаёт один менеджер в `app.state`. Из него фабрика получает адресата публикации, а подписка и logout — менеджер соединений. После commit отзыва logout ждёт закрытия подписок только данной сессии. При остановке приложения сначала завершается работа менеджера, затем освобождается инфраструктура БД. Два экземпляра менеджера разделили бы издателя и подписчиков, даже если модульные тесты каждого экземпляра проходили бы. [Lifespan](../../apps/backend/utility_service/web_api/api/lifespan.py), [фабрики](../../apps/backend/utility_service/realtime_dependencies.py), [logout](../../apps/backend/utility_service/web_api/api/auth.py).
- **Ограничения импортов.** Фабрики сейчас находятся в `use_cases/deps.py`. Действующие проверки запрещают зависимости `use_cases → web_api`, `web_api → infrastructure` и `infrastructure → use_cases`. Они обходят и тесты этих пакетов. Сейчас даже три теста формата сообщений создают настоящий менеджер с подставным сокетом. Простая смена импортов затрагивает также тестовые помощники, которые используются из нескольких пакетов. [Архитектурные проверки](../../apps/backend/tests/test_architecture_boundaries.py), [проверки издателя](../../apps/backend/utility_service/use_cases/tests/test_feature_realtime_publisher.py), [тесты маршрута и диагностики](../../apps/backend/utility_service/web_api/tests/test_ws_layer_diagnostics.py).

## Что означает совместимость

| Наблюдатель | Что позволяет обнаружить регрессию |
| --- | --- |
| Клиент карты | Одноразовый ticket для активного Editor при включённом legacy GIS. После подписки приходит `connected` для нужного слоя. Create/update передают снимок с версией, delete — идентификатор и последнюю живую версию. Клиент перечитывает актуальные данные по HTTP при восстановлении подписки. [Контракт API и клиента](../../Code_wiki/архитектура/api_and_realtime.md), [тесты маршрутов](../../apps/backend/utility_service/web_api/tests/test_ws_layers.py). |
| Другие подписчики и владелец сессии | Кадр сверх лимита, переполненная очередь, ошибка отправки или дедлайн отправки в 5 секунд приводят к закрытию затронутого соединения с `1013`. Отзыв сессии закрывает её соединения с `1008`. Остановка менеджера инициирует `1001`. Для операции закрытия по умолчанию задан таймаут в 1 секунду. [Менеджер и проверки](../../apps/backend/utility_service/web_api/tests/test_realtime_connection_manager.py), [контракт AR-02](../sprint_2/2026-11-02-ar-02-design.md). |
| Читатель серверных логов | При известных адресатах диагностика различает пары `eventId`/`connectionId`, стадии подготовки, сериализации и очереди. `not_sent` отличается от `send_unconfirmed`; успешная отправка, совпавшая по времени с удалением подписки, не получает ложную запись. Ошибка закрытия регистрируется отдельно. При сбое издателя до определения адресатов возможна запись об изменении без `connectionId`. [Контракт AR-03](../sprint_2/2026-11-08-ar-03-design.md), [проверки отправки и очистки](../../apps/backend/utility_service/web_api/tests/test_realtime_delivery_diagnostics.py), [безопасный состав записи](../../apps/backend/utility_service/utils/realtime_logging.py). |

## Исходная проверка

22 ноября на текущем коде **прошли 85 тестов**. Запуск из `apps/backend` с локальными зависимостями проекта:

```powershell
python -m pytest -p no:cacheprovider `
  utility_service/use_cases/tests/test_feature_realtime_publisher.py `
  utility_service/use_cases/tests/test_realtime_connection_manager.py `
  utility_service/use_cases/tests/test_realtime_publication_diagnostics.py `
  utility_service/use_cases/tests/test_realtime_delivery_diagnostics.py `
  utility_service/use_cases/tests/test_websocket_ticket_service.py `
  utility_service/web_api/tests/test_ws_layers.py `
  utility_service/web_api/tests/test_ws_layer_diagnostics.py `
  utility_service/utils/tests/test_realtime_logging.py
```

Прогон охватил модульные и маршрутные проверки. Интеграционные сценарии PostgreSQL по ссылкам выше изучены по коду. Их выполнение и сетевое соединение с настоящим браузером в этот результат не входят.

## Уточнение пользователя и сравнение двух каналов

22 ноября пользователь подтвердил, что формат WebSocket-сообщения должен допускать изменение без правок в прикладном издателе. Второе требование касается получателей одного изменения. Результат у слушателя должен быть согласован с тем, что получает редактор, выполнивший запись.

Редактор отправляет запрос по HTTP. Если у него также открыта подписка на этот слой, его сокет входит в тот же список адресатов, что и сокеты других подписчиков. Менеджер ставит в их очереди один и тот же сериализованный кадр. Отдельное сравнение требуется между HTTP-ответом и содержимым этого кадра. [HTTP-маршруты](../../apps/backend/utility_service/web_api/api/layers.py), [публикация подписчикам слоя](../../apps/backend/utility_service/web_api/realtime/realtime_connection_manager.py).

| Изменение | Тело успешного HTTP-ответа редактору | Содержимое текущего WebSocket-события |
| --- | --- | --- |
| Создание | Снимок объекта с `id`, `type`, `version`, `geometry` и `properties`. | Тот же снимок в поле `feature` события `feature_created`. |
| Обновление | Объект с полем `feature`, содержащим снимок после записи. | Тот же снимок в поле `feature` события `feature_updated`. |
| Удаление | `status: "deleted"` и `featureId`. Версию редактор указал в запросе. | `type: "feature_deleted"`, тот же `featureId` и `deletedVersion` с последней живой версией. |

Для каждого из трёх событий кадр также содержит `eventId`, `occurredAt` и `layerId`. Интеграционный тест сравнивает полное содержимое снимка по обоим каналам при создании и обновлении. Для удаления AR-02 отдельно закрепил версию в исходящем событии и прежнюю форму HTTP-ответа. [Схема ответа удаления](../../apps/backend/utility_service/use_cases/schemas/feature/delete_feature_response.py), [формирование событий](../../apps/backend/utility_service/use_cases/services/feature_realtime_publisher.py), [интеграционный тест CRUD](../../apps/backend/tests/integration_tests/test_legacy_realtime_delivery.py), [контракт версий AR-02](../sprint_2/2026-11-02-ar-02-design.md).

Пользователь подтвердил, что текущая форма обоих сообщений его устраивает. Для приёмки B4 при создании снимок в поле `feature` события должен совпадать со всем телом успешного POST, при обновлении — с полем `feature` успешного PATCH. При удалении `featureId` в событии совпадает с идентификатором из успешного HTTP-ответа, а `deletedVersion` — с версией из принятого сервером DELETE-запроса. Подписанный на слой автор получает по WebSocket тот же кадр, что и другие подписчики. Служебные поля события сохраняют текущий формат.
