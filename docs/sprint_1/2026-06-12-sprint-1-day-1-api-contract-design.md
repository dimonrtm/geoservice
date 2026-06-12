# Спринт 1, День 1: API-Контракт

Дата: 2026-06-12
Статус: подтвержден пользователем

## Назначение

Документ определяет исполнимый HTTP-контракт первого участка Спринта 1:
endpoints, authorization, DTO, состояния и основные ошибки.

Связанные артефакты:

- [Сценарий приемки](2026-06-12-sprint-1-day-1-acceptance-design.md)
- [Доменная модель](2026-06-12-sprint-1-day-1-domain-model-design.md)
- [Вертикальный backlog](2026-06-12-sprint-1-day-1-vertical-backlog-design.md)

## Общие Правила

- base path: `/api/v1`;
- все workflow endpoints требуют Bearer token;
- API paths, JSON keys, enum values и error `code` пишутся на английском;
- пользовательское поле `message` пишется на русском языке;
- timestamps передаются в UTC в ISO 8601;
- идентификаторы сущностей являются UUID;
- `WorkOrder.code`, `Feeder.code` и asset codes являются стабильными
  человекочитаемыми идентификаторами demo dataset;
- каждый ответ с ошибкой содержит `correlationId`;
- password, Bearer token и секреты не попадают в responses и logs.

## ErrorResponse

```json
{
  "code": "WORK_ORDER_NOT_FOUND",
  "message": "Рабочая задача не найдена.",
  "correlationId": "6e2533cb-52a8-451d-b744-59e51aa62477",
  "details": {}
}
```

`details` является необязательным объектом и не должен раскрывать чужие
сущности, stack trace или секретные значения.

## POST /api/v1/auth/login

Аутентифицирует пользователя.

Request:

```json
{
  "email": "alexey.editor@example.local",
  "password": "string"
}
```

Success, HTTP `200`:

```json
{
  "access_token": "string",
  "token_type": "bearer",
  "user": {
    "id": "7ca660f0-3606-497b-b52d-9ac11f06178c",
    "email": "alexey.editor@example.local",
    "displayName": "Алексей Редактор",
    "role": "editor"
  }
}
```

Ошибки: `401 INVALID_CREDENTIALS`, `403 USER_INACTIVE`, `422 INVALID_REQUEST`.

## GET /api/v1/work-orders/assigned-to-me

Возвращает только work orders, назначенные текущему `Editor`.

Success, HTTP `200`:

```json
{
  "items": [
    {
      "id": "c80fd056-d80f-4bf4-8694-89fc1936ab99",
      "code": "WO-001",
      "title": "Проверка участка фидера",
      "description": "Открыть рабочий участок для последующего редактирования.",
      "status": "assigned",
      "aoi": {
        "id": "19e7cc20-9171-468a-a69c-914662c17f02",
        "name": "Рабочая область WO-001",
        "extent": [65.50, 44.80, 65.54, 44.84]
      },
      "feeder": {
        "id": "a5efc407-713b-49ea-b996-07465c02539c",
        "code": "synthetic_utility_feeder_01",
        "name": "Демонстрационный фидер 01"
      },
      "activeEditVersionId": null
    }
  ]
}
```

Для `Reviewer` endpoint возвращает `403 ROLE_NOT_ALLOWED`. Ошибки:
`401 AUTH_REQUIRED`, `403 ROLE_NOT_ALLOWED`.

## POST /api/v1/work-orders/{workOrderId}/edit-versions

Атомарно создает активную `EditVersion` или возвращает уже существующую.
Request body отсутствует.

Success при создании, HTTP `201`; success при повторном открытии, HTTP `200`:

```json
{
  "created": true,
  "editVersion": {
    "id": "a57ec6e1-7eaa-473e-a335-4d02a5e7678e",
    "workOrderId": "c80fd056-d80f-4bf4-8694-89fc1936ab99",
    "ownerId": "7ca660f0-3606-497b-b52d-9ac11f06178c",
    "status": "open",
    "baseRevision": 12,
    "createdAt": "2026-06-12T09:00:00Z",
    "lastOpenedAt": "2026-06-12T09:00:00Z"
  }
}
```

При HTTP `200` поле `created` равно `false`, а `lastOpenedAt` может быть
обновлено.

Ошибки:

- `401 AUTH_REQUIRED`;
- `403 ROLE_NOT_ALLOWED`;
- `404 WORK_ORDER_NOT_FOUND` для отсутствующей или чужой задачи;
- `409 WORK_ORDER_STATE_CONFLICT`;
- `422 WORK_ORDER_CONTEXT_INVALID`.

Backend обязан защищать уникальность активной version на уровне транзакции и
storage constraint, а не только предварительной проверки.

## GET /api/v1/edit-versions/{editVersionId}/workspace

Возвращает read-only контекст workspace.

Success, HTTP `200`:

```json
{
  "workOrder": {
    "id": "c80fd056-d80f-4bf4-8694-89fc1936ab99",
    "code": "WO-001",
    "title": "Проверка участка фидера",
    "description": "Открыть рабочий участок для последующего редактирования.",
    "status": "in_progress"
  },
  "editVersion": {
    "id": "a57ec6e1-7eaa-473e-a335-4d02a5e7678e",
    "status": "open",
    "baseRevision": 12
  },
  "aoi": {
    "id": "19e7cc20-9171-468a-a69c-914662c17f02",
    "name": "Рабочая область WO-001",
    "geometry": {
      "type": "Polygon",
      "coordinates": []
    },
    "extent": [65.50, 44.80, 65.54, 44.84]
  },
  "feeder": {
    "id": "a5efc407-713b-49ea-b996-07465c02539c",
    "code": "synthetic_utility_feeder_01",
    "name": "Демонстрационный фидер 01"
  },
  "features": {
    "type": "FeatureCollection",
    "features": []
  },
  "associations": [
    {
      "id": "5469236b-af26-41d0-8eee-c7ac3f38b047",
      "fromFeatureId": "dbad40d0-2544-466a-92cc-fe09190a54b9",
      "toFeatureId": "f916f93d-38fb-4de0-8cb2-993856a945cd",
      "associationType": "connectivity",
      "revision": 3
    }
  ]
}
```

`features` содержит только объекты выбранного `Feeder`, пересекающие `AOI`.
Полная geometry пересекающего объекта возвращается без clipping. Association
включается, только если оба ее конца присутствуют в `features`.

Ошибки:

- `401 AUTH_REQUIRED`;
- `403 ROLE_NOT_ALLOWED`;
- `404 EDIT_VERSION_NOT_FOUND` для отсутствующей или чужой version;
- `409 EDIT_VERSION_STATE_CONFLICT`;
- `422 WORKSPACE_CONTEXT_INVALID`.

## HTTP И Error Codes

| HTTP | `code` | Русское значение |
|---|---|---|
| `401` | `AUTH_REQUIRED` | Требуется вход в систему. |
| `401` | `INVALID_CREDENTIALS` | Неверный логин или пароль. |
| `403` | `ROLE_NOT_ALLOWED` | Роль пользователя не допускает операцию. |
| `403` | `USER_INACTIVE` | Учетная запись отключена. |
| `404` | `WORK_ORDER_NOT_FOUND` | Рабочая задача не найдена. |
| `404` | `EDIT_VERSION_NOT_FOUND` | Рабочая версия не найдена. |
| `409` | `WORK_ORDER_STATE_CONFLICT` | Состояние задачи не допускает операцию. |
| `409` | `EDIT_VERSION_STATE_CONFLICT` | Состояние version не допускает операцию. |
| `422` | `INVALID_REQUEST` | Запрос содержит некорректные данные. |
| `422` | `WORK_ORDER_CONTEXT_INVALID` | Контекст задачи поврежден или неполон. |
| `422` | `WORKSPACE_CONTEXT_INVALID` | Workspace невозможно сформировать из текущих данных. |

## Журналирование

Application logs пишутся на русском языке и используют структурированные
поля:

- `correlationId`;
- `actorId`, если пользователь определен;
- `operation`;
- безопасные entity ids;
- `result`;
- error `code`.

Пример сообщения: `Открытие WorkOrder отклонено: задача не назначена текущему пользователю`.
Raw password, token, authorization header, stack trace в пользовательском
ответе и полные request bodies не журналируются.
