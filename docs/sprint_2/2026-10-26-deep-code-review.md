# Глубокое ревью GeoService после Sprint 2

Дата: 2026-10-26. Проверенный HEAD: `374853c5ca6a70477bba0f07cc9fe7ab1901bf85`. Рабочее дерево перед ревью было чистым. Ревью охватывает текущий код приложения, а не только последний commit.

## Вывод

В реестре **10 открытых проблем: 0 P1, 5 P2, 5 P3**. **INF-01 и INF-02 решены 2026-10-26 в согласованных границах** и сохранены в таблице для истории со ссылками на проверки. **FE-01 решена 2026-10-27 в узком согласованном сценарии**. **AR-01 решена 2026-10-28 в согласованных границах: локальные gates, итоговый review и re-review исправлений пройдены**; native BFCache/OS suspend не подтверждены. **FE-02 исправлена 2026-10-31: сообщение об ошибке первоначального запуска доступно во всех режимах, команды скрыты до готовности карты**. Всего зарегистрировано 16 находок, включая 3 проблемы структуры и сопровождаемости кода (CQ-01–CQ-03). Четыре runtime-дефекта относятся только к отключённому по умолчанию legacy GIS. BE-01 и BE-04 остаются снятыми по решению пользователя от 2026-10-26: разбор 100 000 вершин за 578 мс приемлем для редкого случая, а влияние синхронного bcrypt при login пользователь считает недостаточно существенным для списка проблем. Измерение parser сохранено как справочный результат. Дополнительно перечислены условные риски и наблюдения; они не включены в подсчёт доказанных дефектов.

Безопасный старт API и production-маршрут frontend → API/WebSocket исправлены и подтверждены локальными проверками INF-01/02. HTTPS остаётся внешним условием, чистота произвольного frontend build context — отдельной INF-03. Гонки восстановления сессии FE-01/AR-01 исправлены в согласованных границах; FE-02 и FE-03 также исправлены: первоначальная ошибка карты видна, watcher не пишет до готовности, удаление прекращает отложенную инициализацию. Подтверждённого обхода assignment или нарушения атомарности Save не установлено; это не гарантия отсутствия таких дефектов.

Прежняя приёмка Sprint 2 не отменяется этим документом: она проверяла согласованные сценарии. Новые пограничные сценарии и production deployment требуют отдельных исправлений. Отсутствующие функции будущих спринтов не оценивались как ошибки.

## Реестр и приоритеты

P1 — исправить до использования соответствующего deployment; P2 — существенный дефект для планового исправления; P3 — локальная проблема качества/доступности. P0 не выявлены. Приоритет учитывает достижимость: legacy отключён и не является блокером Utility workflow.

| ID | Приоритет | Область | Проблема | Доказательство / подробности |
|---|---|---|---|---|
| INF-01 | P1 — решена 2026-10-26 | Deployment | Исправлена передача Secure cookie; безопасный старт API подтверждён | [Отчёт исправления](2026-10-26-inf-01-production-cookie-implementation-report.md): startup smoke, negative case, demo settings, 51 passed |
| INF-02 | P1 — решена 2026-10-26 | Deployment, UX | Production frontend использует общий origin, nginx передаёт HTTP/WebSocket в API | [Отчёт исправления](2026-10-26-inf-02-production-api-routing-implementation-report.md): browser Save/readback/Revert, auth, WebSocket, 334 passed |
| FE-01 | P2 — решена 2026-10-27 | Auth, UX | Retry удерживает ожидание; старый restore не меняет новый login | [Отчёт](2026-10-27-fe-01-session-restore-implementation-report.md): 368 tests, browser mock API smoke |
| AR-01 | P2 — решена 2026-10-28 | Auth, UX | Координация вкладок и серверный отзыв sid; одноразовый refresh сохранён | [Отчёт](2026-10-27-ar-01-browser-session-implementation-report.md), реальные browser/DB gates и явные ограничения |
| FE-02 | P2 — исправлена 2026-10-31 | UI, UX | Ошибка первоначального запуска видна во всех режимах; команды скрыты до готовности карты | [Отчёт](2026-10-31-fe-02-map-initialization-implementation-report.md): 454 tests, browser WebGL smoke; обновление средствами браузера |
| FE-03 | P2 · исправлена 2026-10-31 | UI, корректность | Watcher ждёт готовности; удаление отменяет запуск | [Отчёт FE-03](2026-10-31-fe-03-workspace-style-readiness-implementation-report.md) |
| INF-03 | P2 | Build, supply chain | Docker context frontend включает host node_modules и локальные env | [Infra](infra-performance-review.md), отсутствие ignore + COPY |
| INF-04 | P2 | CI | Backend-only runner пропускает infra contract tests | [Infra](infra-performance-review.md), CI + skip markers |
| BE-02 | P2 | Legacy correctness | `properties={}` возвращает старые данные либо вызывает rollback | [Backend](backend-review.md), mock-repository воспроизведение |
| BE-03 | P2 | Legacy availability | WebSocket удерживает PostgreSQL connection на срок подписки | [Backend](backend-review.md), lifecycle session/handler |
| AR-02 | P2 | Legacy performance | Медленный WebSocket задерживает остальные события и ответ CRUD | [Сквозные сценарии](architecture-realtime-review.md), детерминированный probe |
| FE-04 | P3 | Accessibility | Русскоязычная страница объявлена `lang=en` | [Frontend](frontend-review.md), HTML |
| AR-03 | P3 | Legacy code quality | Ошибки публикации скрываются без диагностического следа | [Сквозные сценарии](architecture-realtime-review.md), except/pass chain |
| CQ-01 | P3 | Качество кода, архитектура | Доменный слой импортирует ORM и исключения use cases | [Качество кода](architecture-realtime-review.md#cq-01--p3-доменный-слой-зависит-от-инфраструктуры-и-use-cases) |
| CQ-02 | P3 | Качество кода, frontend | WorkOrders store совмещает загрузку, редактирование, recovery, навигацию и auth | [Качество кода](architecture-realtime-review.md#cq-02--p3-workorders-store-совмещает-слишком-много-ответственностей) |
| CQ-03 | P3 | Качество кода, backend | Use case напрямую зависит от SQLAlchemy, ORM, persistence rows и geometry codec | [Качество кода](architecture-realtime-review.md#cq-03--p3-use-case-привязан-к-деталям-postgresql-и-sqlalchemy) |

Каждый тематический отчёт содержит точные пути/строки, условия возникновения, последствия и способ проверки исправления. «Подтверждено кодом» не означает воспроизведено в настоящем браузере или на production БД; способ доказательства указан для каждого случая.

## Порядок устранения

Это рекомендации ревью, а не утверждённый план нового спринта или разрешение менять код.

1. **Исправить изоляцию frontend build и запуск infra tests (INF-03/04)**. INF-01/02 закрыты с локальными проверками старта API и browser → API/WebSocket маршрута; HTTPS и новый CI gate не входили в согласованный объём.
2. **AR-01 закрыта в согласованных границах**: browser/DB/frontend gates, общий review и re-review исправлений пройдены. Проверка replay не ослаблена; native BFCache/OS suspend остаются непроверенной границей. FE-01 сохранена отдельно generation guard и ожиданием retry.
3. **Оставшаяся номерная проблема карты**: FE-04. FE-02 и FE-03 исправлены; отмена ожидания load при удалении включена в FE-03. Timeout, общее управление ошибками загрузки и отказ уже работающей карты остаются отдельными рисками.
4. **До повторного включения legacy**: BE-02/03, AR-02/03. Исправить различение null/пустого объекта, освободить DB session до receive-loop, ограничить fanout и добавить диагностический след.
5. **Упростить границы модулей при их развитии**: CQ-01–CQ-03. Отделить ORM mapping от домена, выделить координацию frontend-переходов и определить минимальный контракт persistence для Save. Сохранить поведение существующими regression-тестами и проверками транзакций.

## Архитектура, code smells и performance-риски

- Качество кода выделено в CQ-01–CQ-03; подавление ошибок уже учтено в AR-03. Подробности, точные ссылки, последствия и проверки исправления — в [архитектурном отчёте](architecture-realtime-review.md). Эти замечания не требуют переписывания приложения целиком.
- SQL workspace читает несколько представлений геометрии и выполняет joins/агрегации; планы, RSS и рост задержки на больших данных пока не измерены. Также требуют измерений списки без пагинации и повторная сериализация GeoJSON при drag. Подробности — [infra/performance](infra-performance-review.md) и [frontend](frontend-review.md).
- Retention auth sessions/tickets, воспроизводимость зависимостей, migration locks, cookie CSRF при специально включённом SameSite=None и административные конкурентные изменения — отдельные условные риски. Не заявляются обнаруженные CVE, нарушение SLA или доказанный взлом.
- Полноценное keyboard-редактирование геометрии исключено из дефектов по прямому решению D11-Q03. Отсутствие собственного ResizeObserver снято после проверки реализации установленного MapLibre.

### Полный перечень дополнительных наблюдений

Ниже собраны наблюдения из тематических отчётов, чтобы они не терялись за ссылками. Это условные риски и пробелы проверки, без отдельного подсчёта как подтверждённых дефектов.

| Область | Наблюдение | Подробности и статус |
|---|---|---|
| Backend, доступность | Durable access rejection создаёт registry rows и захватывает блокировки | [Backend](backend-review.md): принятый контракт; рост и конкуренцию ещё нужно измерить |
| Security | При SameSite=None cookie endpoints не проверяют Origin/CSRF token | [Backend](backend-review.md): условный риск конфигурации, browser exploit не воспроизводился |
| Конкурентность | Будущие команды переназначения/отключения пользователя должны согласовать блокировки с Save | [Backend](backend-review.md): таких публичных команд сейчас нет |
| Хранение | Нет регулярной очистки истёкших auth sessions/tickets | [Backend](backend-review.md), [infra](infra-performance-review.md): определить retention; command history имеет отдельные требования |
| Readback | Spatial passed опирается на предыдущий Save, а не повторную spatial validation | [Backend](backend-review.md): прямые SQL-изменения/AOI требуют отдельного протокола |
| Security | Разная стоимость login существующего и неизвестного пользователя | [Backend](backend-review.md): потенциальный timing channel, статистически не проверен; это отдельное наблюдение от снятого BE-04 |
| SQL performance | Workspace материализует и сериализует несколько представлений геометрии | [Infra](infra-performance-review.md): нужны EXPLAIN, RSS и измерения на разных объёмах |
| API performance | Списки без пагинации растут вместе с данными | [Infra](infra-performance-review.md): нарушение SLA не измерено |
| Frontend performance | Повторная сериализация GeoJSON при drag | [Frontend](frontend-review.md): нужен профиль на репрезентативных данных |
| Сборка | Нет полного backend lock с hashes; часть инструментов и tags изменяемы | [Infra](infra-performance-review.md): риск воспроизводимости, не подтверждённая CVE |
| Миграции | Массовый backfill/NOT NULL может удерживать блокировки | [Infra](infra-performance-review.md): нужна репетиция на целевом объёме |
| Realtime | Подписчики хранятся только в одном процессе | [Архитектура](architecture-realtime-review.md): ограничение для будущих workers/реплик |
| Realtime | Между commit и publish отсутствует durable delivery | [Архитектура](architecture-realtime-review.md): нужен явный best-effort контракт либо надёжная доставка для будущего workflow |
| Map lifecycle | Общая обработка error/timeout остаётся вне исправлений; cancel при удалении реализован в FE-03 | [Отчёт FE-03](2026-10-31-fe-03-workspace-style-readiness-implementation-report.md); не любой отказ tile блокирует load |
| Тесты | Default-worker frontend прогон дал 4 сбоя, повтор с двумя workers прошёл | [Frontend](frontend-review.md): первопричина нестабильности не установлена |

### Ограничение покрытия качества кода

Систематический аудит дублирования, сложности всех методов, полноты типизации, именования, мёртвого кода и качества тестовых assertions не выполнялся. Замечания CQ-01–CQ-03 основаны на проверенных зависимостях и ответственностях; отсутствие находок по остальным категориям не означает, что там нет проблем. Новых runtime-проверок при оформлении этих замечаний не проводилось.

## Выполненные проверки

| Проверка | Фактический результат |
|---|---|
| Backend domain_services/use_cases/web_api/utils pytest | 418 passed, 2 deprecation warnings, 36,66 s |
| Infra security/startup contract tests с полным readonly checkout | 12 passed, 0,34 s |
| Frontend typecheck | exit 0 |
| Frontend tests, default workers | 319 passed / 4 failed; два timeout 5 s и два последующих realtime assertion failures |
| Frontend tests, `--maxWorkers=2` | 44 файлов, 323 passed, 109,38 s |
| Backend probes | 100 000 координат приняты parser; оба сценария пустых properties подтверждены на mocks |
| Realtime probe | Медленный первый сокет блокирует второй, после освобождения событие доставляется обоим |

Зелёный повтор frontend не стирает неудачный первый запуск. Точная причина нестабильности default-worker прогона не установлена; гипотеза о перегрузке runner требует отдельной проверки. Infra tests проходят при наличии checkout, но их существующие assertions не обнаруживают INF-01/02.

Backend запускался в одноразовом локальном образе `geoservice-day14-check:latest`, с `--network none`, readonly mounts и отключённой записью bytecode. Исходники взяты из текущего checkout; зависимости — из имеющегося образа, свежая установка lock/dependencies не выполнялась. Существующие DB integration, миграции, нагрузочные тесты, production deployment, browser UI/zoom/screen reader и CVE scanning в этом ревью не запускались. Чужие и рабочая demo-БД не использовались.

Воспроизводимые команды и результаты: [verification.md](evidence/code-review/verification.md), [backend_probes.py](evidence/code-review/backend_probes.py), [realtime_probe.py](evidence/code-review/realtime_probe.py).

## Изменения и память

Созданы только артефакты ревью в `docs/sprint_2`; README дополнен ссылкой. Код приложения, тесты приложения, конфигурация и БД не изменены. `git add`, `git commit`, `git push` не выполнялись; материалы оставлены для проверки пользователем. Agent memory и wiki не дублируют отчёт: долговечные выводы уже сохранены здесь, отдельный ingest не запускался.
