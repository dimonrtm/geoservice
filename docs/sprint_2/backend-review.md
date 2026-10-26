# Ревью backend Спринта 2

Дата: 2026-10-26. Проверен текущий код `apps/backend/utility_service`; старые отчёты не использовались как источник находок. Продуктовый код, конфигурация и БД не изменялись. Ниже отделены подтверждённые дефекты от архитектурных ограничений и рисков. P1 — срочное исправление; P2 — плановое исправление; P3 — низкий приоритет. Подтверждённых P1 в рассмотренном backend нет.

## Подтверждённые находки

### BE-02 · P2 · Очистка properties в legacy PATCH даёт неверный ответ либо откатывается

- Место: `apps/backend/utility_service/use_cases/services/feature_service.py:165`–`:170`; условие загрузки старого объекта — `:150`–`:152`. Запись repository корректно различает `{}` и `None`: `apps/backend/utility_service/infrastructure/postgresql/repositories/layer_repository.py:86`.
- Условие доступности: legacy API включён через `LEGACY_GIS_API_ENABLED=true`; по умолчанию он выключен. Utility Save не использует этот метод.
- Сценарий A: PATCH с `geometry=null, properties={}`. Repository получает `{}`, но `request.properties or current_feature.properties` выбирает старое содержимое. Ответ и realtime event содержат старые свойства при новом номере версии, хотя в БД записан пустой объект.
- Сценарий B: PATCH одновременно с новой geometry и `properties={}`. Старый объект не читается, выражение даёт `None`, возникает `BusinessValidationException`; транзакция откатывает корректный запрос.
- Подтверждение: mock-repository probe получил `db_argument={}`, `response_properties={"name":"old"}`; второй вариант завершился `BusinessValidationException`. Подключения к БД не было.
- Рекомендация: выбирать новое значение по `is not None`, а не по истинности словаря; одинаково использовать его в ответе и публикации события.
- Проверка исправления: отдельно обновление только `properties={}`, одновременно geometry и `{}`, сохранение свойств при `properties=None`; ответ и event должны совпадать с записанным значением. Интеграционную проверку проводить только в disposable test-БД.

### BE-03 · P2 · Legacy WebSocket удерживает соединение PostgreSQL весь срок подписки

- Места: `apps/backend/utility_service/use_cases/services/websocket_ticket_service.py:99`; `apps/backend/utility_service/web_api/api/ws_layers.py:52`, `:59`–`:60`; `apps/backend/utility_service/infrastructure/postgresql/session.py:6`, `:15`–`:20`.
- Условие доступности: legacy realtime включён. Это дефект legacy-пути, не текущего Utility Save.
- Сценарий: `consume_ticket()` завершает явный transaction для ticket, затем читает User вне этого блока. SQLAlchemy начинает новую транзакцию. Route дополнительно читает Layer, после чего переходит в неограниченный `websocket.receive()`. Общая dependency `get_session` закрывает session только после выхода из WebSocket handler; явного завершения транзакции до receive нет.
- Последствие: открытая подписка удерживает одно подключение к PostgreSQL, даже когда не передаются события. Пул настроен на `pool_size=5, max_overflow=5`; десять таких подписок могут занять все подключения процесса и блокировать другие DB-запросы, включая auth и Utility API. Это вывод из жизненного цикла session и кода; конкурентный DB-сценарий в этом ревью не запускался.
- Рекомендация: закончить все проверки и закрыть короткоживущую DB-session до входа в цикл WebSocket; передать туда только detached DTO. Простое увеличение пула не устраняет причину.
- Проверка исправления: в отдельной test-БД открыть больше десяти подписок и убедиться, что число занятых DB-подключений после handshake возвращается к исходному, отсутствуют длительные idle-in-transaction, а auth/Save продолжают отвечать. Добавить проверку завершения session до первого receive.

## Проверенные сильные стороны и границы вывода

- Save использует одну внешнюю транзакцию; current geometry, revision, terminal command и change event записываются до её commit. Ошибки после начала записи не преобразуются в доменный отказ, который мог бы закоммитить частичный результат.
- `lock_version()` выбирает колонки, а не устаревший ORM-объект из identity map; проверка draft revision и registry replay выполняется после получения блокировки.
- Workspace SQL формирует состояние и draft token одним statement. Новое чтение не собирается из нескольких несогласованных запросов к current geometry/revision.
- API повторно проверяет действующего пользователя в БД; роль JWT не служит единственным основанием доступа. Session и WebSocket ticket хранят хеши токенов.
- Решение сохранять access-rejected command для чужой существующей версии **не объявляется багом**: это прямо принято в `2026-10-11-day-7-rejections-events-revert-design.md:105`, `:116`, `:149`–`:155`. Оно нужно для согласованного retry после изменения assignment.
- Не установлены потеря атомарности Save, нарушение optimistic locking или обход assignment в штатном API. Это ограниченный вывод ревью и unit tests, не доказательство отсутствия любых дефектов.

## Риски, требующие отдельных решений

1. **Нагрузка от отказов.** Принятый durable access rejection допускает создание registry rows и захват блокировки чужой известной версии. Рост registry и конкуренция за блокировки при частых отказах требуют отдельного измерения. Любое изменение должно сохранить принятый recovery-контракт; просто удалить durable rejection нельзя.
2. **Cookie endpoints при SameSite=None.** Settings разрешает `AUTH_SESSION_COOKIE_SAMESITE=none` с Secure, но `/logout` и `/session/refresh` не проверяют Origin/CSRF token. Простой cross-site POST может достичь server-side mutation; CORS сам по себе не запрещает выполнение такого POST. Для развёртывания с этим режимом проверить CSRF-сценарии в браузере и принять защиту. Это условный риск конфигурации, не подтверждённая атака на текущую demo.
3. **Границы параллельных административных изменений.** Save блокирует EditVersion, но не User/WorkOrder/AOI; административное отключение или переназначение может пересечься с уже начатым Save. Текущий публичный API таких изменений не предоставляет. При добавлении команд переназначения/закрытия определить общую стратегию блокировок, не считать нынешнее чтение контекста достаточным автоматически.
4. **Срок жизни auth/command history.** В просмотренном runtime нет регулярной очистки истёкших auth sessions/tickets. Registry/history имеет осмысленные требования replay и не должен очищаться тем же простым TTL. До длительного использования нужны отдельные retention-политики и измерение роста таблиц.
5. **Фактический readback и повреждённые данные.** Workspace выводит `geometry_status/aoi_status=passed` из наличия корректного структурного diff, не повторяет spatial validation. Для штатной записи через Save это опирается на предыдущую проверку. Прямые SQL-изменения и изменение AOI требуют отдельного протокола, иначе UI может показывать устаревшую оценку.
6. **Timing enumeration login.** Отсутствие пользователя пропускает bcrypt, тогда как существующий пользователь с неправильным паролем запускает дорогую проверку. Это создаёт потенциальный timing channel для определения существования аккаунта. Измерение статистической различимости ответов не проводилось; взлом паролей не утверждается. Проверить одинаковую по стоимости проверку неизвестного пользователя и ограничение частоты запросов.

## Снятые замечания

**BE-01 снято по решению пользователя от 2026-10-26.** Разбор **100 000 вершин / 800 132 байта за 0,578 секунды** признан приемлемым для редкого случая. Замечание исключено из реестра проблем и рекомендаций к исправлению. Измерение и probe сохранены как справочные данные; код не изменялся. Идентификаторы остальных находок сохранены.

**BE-04 снято по решению пользователя от 2026-10-26.** Пользователь считает влияние синхронного bcrypt при login на производительность недостаточно существенным для включения в список проблем. Замечание и рекомендации к его исправлению исключены. Код не изменялся; нагрузочное измерение влияния login не проводилось.

## Проверки и воспроизведение

Общий read-only прогон координатора: **418 passed, 2 warnings, 36,66 s** для `domain_services`, `use_cases`, `web_api`, `utils`. DB integration suite этим не покрыт.

Дополнительные воспроизведения: [backend_probes.py](evidence/code-review/backend_probes.py). Контейнер `geoservice-day14-check:latest` запускался с `--network none --read-only --tmpfs /tmp`, readonly mounts исходного кода и evidence, `PYTHONDONTWRITEBYTECODE=1`; repositories подменены mock-объектами. Команда:

```powershell
docker run --rm --network none --read-only --tmpfs /tmp -e PYTHONDONTWRITEBYTECODE=1 -e DATABASE_URL=postgresql+asyncpg://unused:unused@localhost/unused -e DEV_MODE=true -e PYTHONPATH=/app -v C:/Repositories/geoservice/apps/backend:/app:ro -v C:/Repositories/geoservice/docs/sprint_2/evidence/code-review:/evidence:ro -w /app --entrypoint python geoservice-day14-check:latest /evidence/backend_probes.py
```

Unit tests не заменяют проверку блокировок на PostGIS. Повторять destructive integration tests можно только через изолированный runner с test-БД. Общая demo-БД в этом ревью не использовалась.

Agent memory не обновлялась: новые выводы полностью сохранены этим отчётом, дублирование в памяти не требуется.
