# Спринт 1, День 1: Вертикальный Backlog

Дата: 2026-06-12
Статус: подтвержден пользователем

## Назначение

Backlog определяет порядок реализации Спринта 1 через вертикальные задачи.
Каждая задача включает необходимую часть данных, backend, frontend,
пользовательских русскоязычных сообщений и тестов. Почасовые оценки не
фиксируются.

Связанные артефакты:

- [Сценарий приемки](2026-06-12-sprint-1-day-1-acceptance-design.md)
- [Доменная модель](2026-06-12-sprint-1-day-1-domain-model-design.md)
- [API-контракт](2026-06-12-sprint-1-day-1-api-contract-design.md)

## Общий Definition Of Done

Задача считается завершенной, когда:

- реализован наблюдаемый вертикальный результат;
- authorization и защитные отказы покрыты тестами;
- пользовательские сообщения и application logs написаны на русском языке;
- API names, JSON keys, identifiers и error `code` не переведены;
- секреты и Bearer token не попадают в logs;
- документация соответствует фактическому контракту;
- существующие quality gates проходят.

## S1-01. Acceptance И Общий Словарь

Результат: команда использует единые AC-01..AC-07, термины и границы Спринта 1.

Зависимости: нет.

Приемка:

- четыре артефакта Дня 1 согласованы;
- editing, validation, reconcile, review и post явно исключены;
- `AOI`, `Feeder`, `Default`, `WorkOrder` и `EditVersion` определены
  однозначно.

## S1-02. Login, Roles И Demo Users

Результат: `Editor` и `Reviewer` входят в систему, а workflow endpoints
различают их роли.

Зависимости: S1-01.

Приемка:

- существуют воспроизводимые demo users;
- `Editor` получает доступ к editor workflow;
- `Reviewer` получает HTTP `403` при попытке открыть editor workspace;
- UI и ошибки русскоязычны;
- password и token отсутствуют в logs.

## S1-03. AOI И Feeder Dataset

Результат: backend хранит один валидный `AOI`, один `Feeder`, его features и
внутрефидерные associations.

Зависимости: S1-01.

Приемка:

- `AOI` является валидным `Polygon` или `MultiPolygon` в `SRID 4326`;
- каждый `NetworkFeature` принадлежит одному `Feeder`;
- оба конца association существуют и принадлежат тому же `Feeder`;
- данные доступны через service/repository boundary;
- базовые инварианты покрыты тестами.

## S1-04. Воспроизводимый Seed

Результат: `synthetic_utility_feeder_01` восстанавливается идемпотентно.

Зависимости: S1-02, S1-03.

Приемка:

- seed создает demo users, `AOI`, `Feeder`, network data, `Default` и
  назначенный `WO-001`;
- повторный запуск не создает дубли;
- integrity test подтверждает связи и стабильные codes.

## S1-05. Мои наряды API И Assignment Authorization

Результат: `Editor` получает только назначенные ему work orders.

Зависимости: S1-02, S1-04.

Приемка:

- реализован `GET /api/v1/work-orders/assigned-to-me`;
- чужие задачи отсутствуют в выдаче;
- роль и active user проверяются;
- DTO и ошибки соответствуют API-контракту;
- API tests покрывают AC-01, AC-05 и AC-06.

## S1-06. Create/Open EditVersion

Результат: первое открытие создает version, повторное возвращает ту же version.

Зависимости: S1-05.

Приемка:

- реализован `POST /api/v1/work-orders/{workOrderId}/edit-versions`;
- creation возвращает `201`, reopen возвращает `200`;
- `baseRevision` фиксируется атомарно;
- конкурентные запросы не создают две активные version;
- чужая задача возвращает тот же `404`, что и отсутствующая;
- tests покрывают AC-02, AC-03, AC-05 и AC-07.

## S1-07. Read-Only Workspace API

Результат: backend возвращает полный контекст workspace.

Зависимости: S1-03, S1-06.

Приемка:

- реализован `GET /api/v1/edit-versions/{editVersionId}/workspace`;
- features фильтруются одновременно по `Feeder` и пересечению с `AOI`;
- geometry не обрезается;
- возвращаются только associations с двумя присутствующими концами;
- чужая version не раскрывается;
- contract tests покрывают AC-04, AC-05, AC-06 и AC-07.

## S1-08. Frontend Мои наряды

Результат: после login `Editor` видит русскоязычный список назначенных задач.

Зависимости: S1-05.

Приемка:

- экран использует новый workflow API;
- показывает `code`, русские title/status и краткий контекст `AOI`/`Feeder`;
- loading, empty и error states написаны на русском;
- выбор задачи запускает create/open version;
- component/store tests покрывают AC-01 и защитные состояния.

## S1-09. Frontend Edit Workspace

Результат: выбор work order открывает read-only карту с контекстом version.

Зависимости: S1-06, S1-07, S1-08.

Приемка:

- карта позиционируется по extent `AOI`;
- видны граница `AOI`, network features и доступные associations;
- отображаются `WorkOrder`, `Feeder`, `EditVersion`, status и `baseRevision`;
- отсутствуют команды изменения сети;
- повторное открытие использует существующую version;
- frontend tests покрывают AC-03 и AC-04.

## S1-10. End-To-End Приемка И Документация

Результат: весь путь воспроизводится после чистого seed.

Зависимости: S1-04..S1-09.

Приемка:

- автоматизирован happy path AC-01..AC-04;
- автоматизированы защитные AC-05..AC-07;
- выполнен ручной demo в локальной Docker Compose среде;
- проверены русскоязычные UI, errors и application logs;
- зафиксированы известные ограничения Спринта 1;
- повторный прогон после восстановления seed дает тот же результат.

## Порядок И Контрольные Точки

- после S1-04 существует целостный backend dataset;
- после S1-06 устойчиво работает assignment-to-version flow;
- после S1-07 завершен backend vertical slice;
- после S1-09 доступен пользовательский vertical slice;
- S1-10 является единственным основанием считать Спринт 1 завершенным.
