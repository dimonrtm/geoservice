# Спринт 1, День 2: Роли И Доступ

Дата: 2026-06-13
Статус: подтвержден пользователем

## Назначение

Документ фиксирует целевую модель ролей, правила авторизации и demo users для
Спринта 1. Он уточняет документы Дня 1 в части удаления legacy-роли `Viewer`,
добавления роли `Reviewer` и различения ошибок роли и назначения.

Реализация reviewer queue, approve/reject и `post` не входит в День 2. День 2
создает устойчивый RBAC-контракт, на который эти операции будут опираться в
следующих спринтах.

## Принятое Решение

Выбрана строгая ролевая модель:

- `User.role` принимает только значения `editor` и `reviewer`;
- у пользователя ровно одна роль;
- роли `Editor` и `Reviewer` взаимоисключающие;
- permission-флаги и many-to-many-модель ролей не вводятся;
- legacy-роль `Viewer` удаляется из модели, API, frontend и demo seed.

Структурное ограничение одной роли на пользователя обеспечивает separation of
duties без дополнительных комбинаций разрешений.

## Матрица Доступа

| Возможность | `Editor` | `Reviewer` |
|---|---:|---:|
| Войти в систему | да | да |
| Читать разрешенные realtime-события | да | да |
| Видеть `My Work Orders` | только назначенные | нет |
| Открывать editor workspace | только назначенный | нет |
| Создавать или открывать `EditVersion` | только для назначенного `WorkOrder` | нет |
| Редактировать, валидировать, reconcile и submit | да, в своем workflow | нет |
| Видеть reviewer queue | нет | все версии в review |
| Approve/reject | нет | да |
| Выполнять `post` после approve | нет | да |

Reviewer queue является общей. Назначение версии конкретному `Reviewer` и
ограничение очереди по `AOI` или `Feeder` не входят в Release 1.

## Auth И Guards

Login возвращает пользователя с ролью:

```json
{
  "user": {
    "role": "editor"
  }
}
```

Допустимые значения поля `role`: `"editor"` и `"reviewer"`.

JWT сохраняет существующую форму:

- `sub`;
- `role`;
- `iat`;
- `exp`.

Каждый защищенный запрос повторно загружает активного пользователя из БД.
Payload JWT идентифицирует сессию, но не заменяет проверку актуальной роли и
активности пользователя в БД. Токен с удаленной ролью `viewer` отклоняется.

Backend использует централизованные зависимости:

- `get_current_user` проверяет token, пользователя и активность;
- `require_editor` разрешает только роль `editor`;
- `require_reviewer` разрешает только роль `reviewer`;
- assignment guard проверяет
  `WorkOrder.assignee_id == current_user.id`.

Скрытие элементов интерфейса не является механизмом безопасности: каждый
endpoint самостоятельно применяет role и assignment guards.

## Ошибки Авторизации

| HTTP | `code` | Условие |
|---|---|---|
| `401` | `AUTH_REQUIRED` | Token отсутствует, поврежден, истек или содержит неподдерживаемую роль. |
| `403` | `USER_INACTIVE` | Пользователь существует, но отключен. |
| `403` | `ROLE_NOT_ALLOWED` | Актуальная роль не допускает операцию. |
| `403` | `WORK_ORDER_NOT_ASSIGNED` | `Editor` обращается к существующему чужому `WorkOrder`. |
| `404` | `WORK_ORDER_NOT_FOUND` | `WorkOrder` не существует. |

Разделение `WORK_ORDER_NOT_ASSIGNED` и `WORK_ORDER_NOT_FOUND` является
осознанным уточнением API-контракта Дня 1. Оно предназначено для локального
demo и понятной диагностики доступа. Перед production-развертыванием риск
раскрытия существования чужого идентификатора должен быть пересмотрен.

## Demo Users

Идемпотентный seed создает или восстанавливает трех пользователей:

| Login | Email | Роль | Назначение |
|---|---|---|---|
| `alexey.editor` | `alexey.editor@example.local` | `Editor` | `WO-001`, основной editor flow |
| `bolat.editor` | `bolat.editor@example.local` | `Editor` | `WO-002`, параллельное изменение и conflict flow |
| `marina.reviewer` | `marina.reviewer@example.local` | `Reviewer` | Общая review queue, approve/reject и `post` |

Пароли фиксируются только для локального demo. В БД сохраняется только
`password_hash`. Повторный seed:

- не создает дубликаты;
- восстанавливает ожидаемую роль;
- восстанавливает ожидаемый password hash;
- сохраняет стабильные идентификаторы, необходимые связанным demo-данным.

UI управления пользователями, ролями и назначениями не входит в Спринт 1.

## Миграция Legacy Viewer

DB enum изменяется с `viewer | editor` на `editor | reviewer`.

Порядок миграции:

1. Найти пользователей с ролью `viewer`.
2. Удалить их как устаревшие demo-данные.
3. Очистить или удалить только связанные с ними legacy demo-записи согласно
   FK и заранее определенной политике удаления.
4. Убедиться, что на удаляемых users не ссылаются актуальные utility
   `WorkOrder`, `EditVersion` или audit records.
5. Заменить DB enum.
6. Запустить новый demo seed.

Миграция не преобразует `Viewer` в `Reviewer`: автоматическая выдача новых
review/post-полномочий запрещена. Если legacy `Viewer` связан с данными, которые
не классифицированы как удаляемые demo-данные, миграция завершается явной
ошибкой вместо каскадной потери данных.

## Backend И Frontend Контракты

Backend:

- `UserRole` содержит только `EDITOR` и `REVIEWER`;
- Pydantic-схемы и OpenAPI допускают только `"editor" | "reviewer"`;
- generic write endpoints используют `require_editor`;
- reviewer endpoints используют `require_reviewer`;
- WebSocket чтение разрешено обеим ролям;
- mutation остается в HTTP API и проверяется соответствующим guard.

Frontend:

- `AuthRole` содержит только `"editor" | "reviewer"`;
- роль отображается как `Редактор` или `Рецензент`;
- `Editor` получает editor navigation;
- `Reviewer` не получает editor workspace;
- reviewer navigation может быть заглушкой до реализации queue;
- прямой HTTP-вызов запрещенной операции остается заблокирован backend.

## Reviewer Workflow Boundary

Будущий reviewer workflow соблюдает следующие правила:

- `Reviewer` видит все версии в состоянии review;
- `Reviewer` принимает approve/reject decision;
- после approve тот же `Reviewer` выполняет отдельную операцию `post`;
- `Editor` не может approve или post собственную `EditVersion`;
- separation of duties определяется ролью, а не сравнением автора и reviewer;
- reviewer queue не требует отдельной сущности назначения.

В День 2 реализуются только роль, guard, demo user и контракт доступа. Queue,
approve/reject, `post` и их UI относятся к следующим спринтам.

## Проверка

Минимальный набор автоматических проверок:

- login успешен для каждого из трех demo users;
- API возвращает только `"editor" | "reviewer"`;
- token с ролью `viewer` отклоняется;
- `Editor` проходит `require_editor` и не проходит `require_reviewer`;
- `Reviewer` проходит `require_reviewer` и не проходит `require_editor`;
- `Editor` видит только назначенные ему work orders;
- обращение к существующему чужому `WorkOrder` возвращает
  `403 WORK_ORDER_NOT_ASSIGNED`;
- `Reviewer` получает `403 ROLE_NOT_ALLOWED` для editor workspace;
- WebSocket принимает обе активные роли;
- повторный seed не создает дубликаты и восстанавливает baseline;
- миграция удаляет legacy `Viewer`, но останавливается при неизвестных
  значимых FK-связях;
- после миграции в БД отсутствует значение роли `viewer`.
- все существующие jobs `.github/workflows/ci.yml` проходят без удаления или
  ослабления проверок;
- backend Docker targets `dev` и `prod`, frontend target `prod` собираются;
- Compose smoke `postgis + backend`, локальные profiles `dev` и `prod`, а
  также `infra/ci-up.cmd` и `infra/dev-up.cmd` сохраняют работоспособность;
- миграция и новый seed успешно поднимаются как на чистой БД, так и поверх
  legacy volume с текущими demo users.

Отдельного CD workflow в репозитории на момент design нет. Требование
совместимости относится к существующему CI, Docker image builds и локальному
Docker Compose deployment; оно не добавляет новый delivery pipeline в scope.

Acceptance smoke:

1. `alexey.editor` входит и видит только `WO-001`.
2. `bolat.editor` входит и видит только `WO-002`.
3. `marina.reviewer` входит, но не открывает editor workspace.
4. Повторный seed сохраняет трех пользователей и их назначения.

## Audit

Значимые операции доступа и будущего review workflow фиксируют:

- `actorId`;
- актуальную `role`;
- `action`;
- timestamp;
- target entity;
- `WorkOrder` или `EditVersion`;
- result и error `code`.

Пароли, password hash, JWT и authorization headers в audit и application logs
не записываются.

## Не Входит В Scope

- роль `Viewer`;
- совмещение `Editor` и `Reviewer`;
- permission-флаги;
- many-to-many roles;
- production user administration;
- назначение конкретного reviewer;
- ACL по объектам, полям, `AOI` или `Feeder`;
- refresh token и внешние identity providers;
- реализация reviewer queue, approve/reject и `post` в День 2.
