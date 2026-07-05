# Ограничение Legacy GIS API

Дата: 2026-07-05
Статус: утвержден пользователем

## Назначение

Нужно ограничить legacy endpoints `/api/v1/layers*` и `/api/v1/ws/layers*`, чтобы они не обходили текущую модель Utility Workflow: `Editor` работает только через назначенные `WorkOrder` и workspace, а `Reviewer` не получает глобальный read-channel по слоям и realtime.

Решение вводит compatibility flag. Legacy GIS API остается технически доступным для dev/demo совместимости, но выключен по умолчанию и не является частью основного Utility Workflow.

## Выбранный Подход

Вводится backend setting:

```text
LEGACY_GIS_API_ENABLED=false
```

Поведение:

- если `LEGACY_GIS_API_ENABLED=false`, legacy REST endpoints и выдача websocket ticket возвращают `403 LEGACY_GIS_API_DISABLED`;
- если `LEGACY_GIS_API_ENABLED=true`, legacy REST endpoints и выдача websocket ticket доступны только активному `Editor`;
- `Reviewer` получает `403 ROLE_NOT_ALLOWED` даже при включенном flag;
- websocket handshake остается ticket-only: роль и flag проверяются на этапе выдачи ticket, а не в query string, JWT или cookie на самом websocket.

## Backend Architecture

`utility_service.utils.settings.Settings` получает поле `legacy_gis_api_enabled` с alias `LEGACY_GIS_API_ENABLED` и значением `False` по умолчанию.

В `utility_service.web_api.api.auth` добавляется единый guard `require_legacy_gis_editor`. Guard сначала проверяет feature flag, затем применяет editor role guard к актуальному пользователю из БД. Это сохраняет существующий принцип: JWT не является source of truth для роли или активности пользователя.

Guard применяется ко всей legacy GIS surface:

- `GET /api/v1/layers`;
- `GET /api/v1/layers/{layer_id}/features`;
- `GET /api/v1/layers/{layer_id}/features/{feature_id}`;
- `POST /api/v1/layers/{layer_id}/features`;
- `PATCH /api/v1/layers/{layer_id}/features/{feature_id}`;
- `DELETE /api/v1/layers/{layer_id}/features/{feature_id}`;
- `POST /api/v1/ws/layers/{layer_id}/ticket`.

`WebSocketTicketService` больше не закрепляет доступ `Reviewer` к layer realtime. Роль проверяется новым guard до вызова `issue_ticket`; дополнительная проверка внутри service остается defense-in-depth и разрешает только `editor`.

## Data Flow

REST flow:

```text
HTTP request -> get_current_user -> require_legacy_gis_editor -> legacy handler
```

Ticket issue flow:

```text
POST /api/v1/ws/layers/{layer_id}/ticket
-> get_current_user
-> require_legacy_gis_editor
-> WebSocketTicketService.issue_ticket
-> ticket
```

WebSocket flow:

```text
WS /api/v1/ws/layers/{layer_id}?ticket=...
-> consume_ticket
-> layer existence check
-> connection_manager.connect
```

Прямой websocket endpoint не принимает JWT, long-lived access token, session cookie или role параметр. Если ticket не выдан, подключение невозможно.

## Error Handling

Для выключенного flag используется structured error:

```json
{
  "code": "LEGACY_GIS_API_DISABLED",
  "message": "Legacy GIS API отключен."
}
```

Текст `message` должен быть человекочитаемым, а `code` должен быть стабильным для тестов и клиентской диагностики.

Для роли `reviewer` используется существующий `403 ROLE_NOT_ALLOWED`. Для отсутствующей или невалидной сессии сохраняется `401 AUTH_REQUIRED`.

Для websocket handshake ошибки consume ticket остаются policy violation `1008`; новые role/flag ошибки должны возникать раньше, на HTTP ticket endpoint.

## Testing

Backend regression tests должны закрепить следующие случаи:

- при `LEGACY_GIS_API_ENABLED=false` authenticated `editor` и `reviewer` получают `403 LEGACY_GIS_API_DISABLED` на legacy REST endpoints и ticket issue;
- при `LEGACY_GIS_API_ENABLED=true` `editor` проходит legacy REST guard и может получить websocket ticket;
- при `LEGACY_GIS_API_ENABLED=true` `reviewer` получает `403 ROLE_NOT_ALLOWED` на legacy REST endpoints и ticket issue;
- существующий websocket subscription по валидному editor ticket остается рабочим;
- тесты, которые параметризуют layer realtime access по `editor` и `reviewer`, сужаются до `editor`;
- settings tests проверяют default `legacy_gis_api_enabled is False` и чтение `LEGACY_GIS_API_ENABLED=true`.

## Documentation

После реализации нужно обновить технические knowledge nodes, где сейчас зафиксировано, что `editor` и `reviewer` могут читать layers/features и подписываться на realtime. В частности, актуализации потребуют `Code_wiki/архитектура/api_and_realtime.md` и `Code_wiki/архитектура/backend.md`.

Repository-change ingest нужен только после завершенной реализации, потому что изменение исправит durable technical knowledge о security boundary legacy GIS API.

## Scope

Входит в scope:

- feature flag для legacy GIS API;
- единый guard для legacy REST и ticket issue;
- запрет `Reviewer` на legacy layers/realtime;
- regression tests для flag и role behavior;
- последующее обновление Code_wiki после реализации.

Не входит в scope:

- object-level ACL по `AOI`, `Feeder`, `Layer`, `Feature` или `WorkOrder`;
- `scope` claims в JWT;
- permission flags, many-to-many RBAC или новая модель ролей;
- новый workspace-specific layer API;
- workspace realtime;
- изменение frontend workspace flow.

## Rollout

Default должен быть secure: `LEGACY_GIS_API_ENABLED=false`. Если legacy editor map нужен для dev/demo совместимости, flag включается явно в соответствующем окружении. Production-like окружение не должно получать legacy layer read/realtime без явного решения.
