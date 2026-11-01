# INF-05: план реализации

> **Для исполнителя:** применять `superpowers:executing-plans` при исполнении
> в текущем чате либо `superpowers:subagent-driven-development`, если пользователь
> выберет делегирование. Выполнять задачи последовательно, отмечая пункты `[ ]`.

**Цель:** устранить отказ production nginx по размеру тела Save/Revert
для редактируемой линии, сохранив предел остальных API.

**Архитектура:** отдельный regex location geometry path с
`client_max_body_size 0` и прежними proxy-настройками. Самостоятельный локальный
runner проверяет границу маршрута и полный browser Save/readback/Revert
на production targets с временной БД.

**Технологии:** nginx 1.27-alpine, Docker Compose, Node.js ESM, Playwright
из `infra/m4`, PostgreSQL/PostGIS, существующие backend seeds и API.

**Спецификация:** [принятый дизайн](2026-11-01-inf-05-save-size-design.md).

## Общие ограничения

- Только локальная приёмка. Не менять `.github/workflows`, CI jobs, существующие
  test scripts и автоматическое discovery suites ради INF-05.
- Не менять Save API, parser, guards, frontend state machine, recovery, таймауты
  и buffering. Не мигрировать protocol blocks и не вводить конечный новый лимит.
- Внешний HTTPS proxy описывается в runbook; его настройка и проверка вне задачи.
- Рабочие данные и demo seeds не менять. Fixture существует только в disposable БД.
- Артефакты — `docs/sprint_2`, evidence — `docs/sprint_2/evidence/inf-05/<run-id>/`.
- Текст UTF-8/LF; не выполнять `git add`, `git commit`, `git push`.
- Сохранять пользовательские изменения. Использовать подходящий текущий checkout;
  отдельная изоляция требуется для стенда, не обязательно новый Git worktree.

## Фокус проверки

1. Похожий путь или суффикс не получает исключение размера — задача 1.
2. Query string не ломает Save path; полный URI и тело доходят до upstream — задача 1.
3. Авторизация и ошибки backend сохраняются в новом location — задача 2.
4. Большой API Save проходит доменные guards; штатная трёхвершинная линия
   редактируется через настоящий UI — задача 2, согласно поправке пользователя.
5. Ошибка проверки/сборки не оставляет собственные контейнеры и volume и не
   удаляет чужие ресурсы — задачи 1–2, проверка failure path.

## Карта файлов

| Файл | Ответственность |
| --- | --- |
| `apps/frontend/nginx.conf` | Единственное изменение продукта: geometry location |
| `docs/sprint_2/inf-05/proxy-probe.mjs` | Локальная HTTP-проверка маршрутов с диагностическим upstream |
| `docs/sprint_2/inf-05/fixture.mjs` | Генерация большой линии и SQL для изолированной БД |
| `docs/sprint_2/inf-05/smoke.mjs` | Browser Save, reload/readback, Revert |
| `docs/sprint_2/inf-05/run.mjs` | Изоляция, сборка, seed, запуск проверок, evidence и cleanup |
| `docs/sprint_2/verify-inf-05.ps1` | Ручная точка входа, передаёт аргументы и exit code Node |
| `docs/sprint_2/2026-11-01-inf-05-save-size-runbook.md` | Команда запуска и требования внешнего proxy |
| `docs/sprint_2/2026-11-01-inf-05-save-size-implementation-report.md` | Реальные результаты, ограничения, ссылки на evidence |

Последние семь файлов создаются при реализации. В конце обновить статус INF-05
в `README.md`, `infra-performance-review.md`, `2026-10-26-deep-code-review.md`.

## Задача 1. Изолированно доказать границу nginx и внести настройку

**Файлы:** `nginx.conf`, новые `inf-05/proxy-probe.mjs`, `inf-05/run.mjs`,
`verify-inf-05.ps1`.

**Интерфейсы:** `run.mjs --proxy-only` запускает только proxy-проверку;
`proxy-probe.mjs` экспортирует `checkProxy(origin, geometryPath)` → JSON summary
либо assertion error. Диагностический upstream сообщает метод, URI, размер и
SHA-256 тела; runner запускает его в собственной Docker-сети с alias
`utility_service`, не используя рабочий API. Никаких test-only routes в продукте.

- [x] Создать runner с уникальным project/run ID, cleanup в `finally`, ограниченным
  временем дочерних процессов и ненулевым exit при ошибке. Использовать подходы
  `inf-02/run.mjs`, не вынося в этой задаче общую инфраструктуру других runners.
- [x] Создать проверку с телом `Buffer.alloc(1_048_577, 0x61)` и маленьким контролем.
  На каноническом geometry path и том же path с query требовать HTTP 200 upstream,
  точный method/URI, размер и SHA-256 без усечения. На `/api/v1/auth/login`,
  geometry path с `/extra` и `/geometry-extra` требовать 413 для большого тела.
  Маленький запрос к контрольному API path должен достигать upstream.
- [x] Выполнить `node docs/sprint_2/inf-05/run.mjs --proxy-only` до изменения nginx:
  ожидаемый RED — 413 вместо upstream 200 на geometry path. Сохранить evidence;
  startup failure или недоступный Docker не считаются воспроизведением дефекта.
- [x] Добавить в `apps/frontend/nginx.conf` location из принятого дизайна:
  `^/api/v1/work-orders/[^/]+/edit-versions/[^/]+/features/[^/]+/geometry$`.
  Установить `client_max_body_size 0`, повторить все proxy/log directives текущего
  API location. Не добавлять `^~` общему префиксу; `proxy_pass` без URI-части.
- [x] Повторить proxy-only: ожидаемый GREEN по всей матрице, плюс `nginx -t`
  в проверяемом контейнере. Зафиксировать effective config и версию nginx.
- [x] Искусственно завершить probe ошибкой assertion внутри собственного стенда;
  подтвердить ненулевой exit и отсутствие его ресурсов после cleanup. Удалить
  временную инъекцию ошибки; сохранить результат проверки cleanup.

## Задача 2. Большая линия через API и штатная линия через браузер

Уточнение пользователя при реализации: из-за принятого UI guard «ровно три
вершины» большой сценарий выполняется через настоящий API/nginx/БД, обычный
browser cycle остаётся отдельной регрессией. UI не расширяется.

**Файлы:** новые `inf-05/fixture.mjs`, `inf-05/smoke.mjs`, `inf-05/api-smoke.mjs`;
дополнить `run.mjs`.

**Интерфейсы:** `fixture.mjs` экспортирует `buildLargeLine(sourceCoordinates)` →
GeoJSON LineString и `prepareFixture(sql)` → `{workOrderId, featureId, coordinates}`;
`sql(query)` выполняет запрос только в БД данного runner. `smoke.mjs` экспортирует
`checkWorkflow({origin, fixture, evidenceDirectory})` → JSON summary.
`api-smoke.mjs` экспортирует `checkLargeApi({origin, fixture})` → JSON summary.
Без `--proxy-only` runner выполняет proxy probe и оба цикла на последовательно
пересоздаваемых собственных БД.

- [x] Расширить runner по образцу INF-02: отдельная Compose-конфигурация, уникальные
  container names и volume, свободный loopback port frontend, отсутствие API port.
  Собирать production targets из текущих `apps/frontend` и `apps/backend` с их
  `.dockerignore`; не подменять источники Git HEAD или заранее очищенной копией.
  Не передавать секреты в build args/evidence. Записать hash nginx и версии образов.
- [x] В disposable БД выполнить миграции и demo seed chain как в INF-02. До старта
  пользовательского сценария заменить L-003 в подготовленных network/default
  snapshots большой синтетической линией; проверить отсутствие EditVersion.
  Это подготовка fixture, не продуктовая операция изменения immutable baseline.
  Исходники seeds не менять и повторно upgrade fixture после замены не запускать.
- [x] Сохранить первые две координаты исходной линии; уплотнять дальнюю половину
  последнего сегмента (в исходной линии всего три вершины),
  сохраняя порядок, endpoints, простоту и AOI; избегать совпадающих соседних XY.
  Проверить `ST_IsSimple`, `ST_IsValid`, `ST_CoveredBy` и отсутствие нулевых сегментов.
  Подобрать число вершин так, чтобы тело и Save, и Revert было больше 1 MiB
  с запасом; не достигать порога пробелами или фиктивными полями JSON.
- [x] Реализовать API workflow: настоящий login → открытие EditVersion → workspace
  → изменение вершины 1 → PUT через production nginx. Проверить байты тела больше
  1 MiB, успешный результат, commandId и маршрут; не сохранять token/cookie/Authorization.
- [x] Проверить успешный ответ и отдельный GET:
  геометрия соответствует подтверждённому результату, изменилась только вершина 1,
  token изменён, change set существует. Baseline hash совпадает с hash после
  подготовки fixture; снимки authoritative данных не изменились от Save.
- [x] Выполнить Revert через API, проверить размер запроса, успешный ответ и новый
  token. Отдельный GET возвращает baseline, change set пуст. Повтор Save с тем же
  commandId до Revert не создаёт новую mutation.
- [x] Пересоздать собственную тестовую БД и seeds. На обычной трёхвершинной линии
  выполнить browser workflow по паттерну `inf-02/smoke.mjs`: настоящий login,
  выбор наряда/линии, drag вершины 1, Save, reload, Revert и reload. Проверить
  токены, геометрию, change set, отсутствие protocol block и неизменность baseline;
  не подменять store и не заменять browser Save прямым HTTP в этой фазе.
- [x] На настоящем API через nginx проверить отсутствие доступа без авторизации
  и формат backend error для небольшого malformed JSON авторизованного запроса.
  Не интерпретировать эти ошибки как успешный Save.
- [x] Выполнить `& docs/sprint_2/verify-inf-05.ps1`: ожидается exit 0, успешная
  матрица proxy и browser cycle, evidence с фактическими размерами обоих запросов,
  неизменностью baseline и cleanup. Сроки отдельных шагов фиксировать как наблюдение,
  не как новый SLA. Ошибки fixture устранять в fixture, не ослаблением guards.
- [x] Проверить cleanup полного стенда также при искусственной ошибке после
  подготовки БД: собственные контейнеры/network/volume удалены, evidence сохранено.
  Перед любым рекурсивным удалением временного каталога проверить его абсолютный
  путь и принадлежность runner; не удалять рабочие каталоги и чужие Docker volumes.

## Задача 3. Инструкция, отчёт и итоговая проверка

**Файлы:** новые runbook/report, существующие индексы и записи INF-05.

- [x] Описать prerequisites: Docker Compose, Node, зависимости/browser из `infra/m4`;
  ручные команды proxy-only и full, evidence, cleanup и диагностику ошибок.
- [x] В runbook описать пересборку production frontend и правило внешнего HTTPS
  proxy: тот же Save path должен пропускать полное тело без конечной квоты,
  нарушающей гарантию; другие paths сохраняют собственные ограничения.
  Сохранить caveat INF-02 о restart frontend при смене IP API.
- [x] Сопоставить фактические результаты с дизайном. Указать отдельно proxy probe,
  browser/DB proof, размеры и число вершин, версии и предел внешнего TLS.
  Не заявлять поддержку бесконечного объёма или нагрузочную валидацию.
- [x] Выполнить `git diff --check`, проверить LF новых файлов и diff: продуктовая
  правка только в nginx, CI/workflow и существующие suites не изменены.
- [x] Провести review относительно дизайна и пяти пунктов фокуса; исправить
  обнаруженные ошибки и повторить только затронутые проверки. Отдельную память
  не создавать, если всё долговременное знание уже сохранено в runbook/дизайне.
- [x] Обновить статусы INF-05 только при подтверждённой приёмке. Оставить изменения
  unstaged; выдать пользователю ссылки на отчёт и ограничения проверки.

## Самопроверка плана

Покрыты выбранная граница location, сохранение proxy-контракта, локальный полный
Save/Revert, соседние paths, ошибки доступа, внешняя инфраструктура и cleanup.
Fixture и запуск не включены в CI. План выполнен с принятой поправкой приёмки; результаты в отчёте реализации и журнале исполнения.
