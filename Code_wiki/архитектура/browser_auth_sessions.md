---
title: Сессия браузера и немедленный отзыв sid
type: service
status: active
created: 2026-10-28
updated: 2026-10-28
source: repository-change:2026-10-28
tags: [auth, browser-session, sid, concurrency]
---

# Сессия браузера и немедленный отзыв sid

## Серверная граница действительности

`user.browser_auth_sessions` — стабильный родитель одного входа конкретного
браузерного profile. `user.auth_sessions` содержит поколения одноразовых refresh
credentials, `user.websocket_tickets` — одноразовые tickets; обе таблицы связаны
с родителем composite FK `(browser_session_id, user_id)`. Access JWT содержит
обязательный `sid`. Это инфраструктурная auth-граница, не доменный lock WorkOrder.

`AuthSessionService` блокирует родителя до credential в общей транзакции.
Refresh сохраняет sid, меняет raw credential и продлевает активного родителя;
старый credential непригоден для replay. Состояние владельца/родителя и время
повторно проверяются после ожидания lock. Login заменяет только вход,
доказанный прежней cookie, и не отзывает все входы user id.

`AuthSessionAccessService.authenticate` проверяет JWT и свежие parent/user rows
без positive cache. Read transaction заканчивается до business service.
После commit logout новая проверка прежнего access JWT, refresh и ticket
отвергается; уже допущенная операция вправе завершиться.

`POST /api/v1/auth/session/status` принимает `{session_id}` и возвращает
`{session_id, state: active|ended}`. Доказательство относится именно к ожидаемому
sid: валидный JWT либо известный refresh hash, включая историю ротации.
Только status допускает истёкший `exp` в остальном валидного JWT. Status не
обновляет TTL, не выдаёт credential и не пишет cookie. DB failure не означает ended.

`POST /api/v1/auth/logout` принимает `{session_id}`, проверяет независимое OR
доказательство sid по неистёкшему JWT или известной cookie и идемпотентно
отзывает родителя. Ответ `{ok: true, session_id}` приходит после commit.
Logout **не пишет Set-Cookie**: недействительная cookie остаётся до login/expiry.
Истёкший JWT без matching cookie не даёт права logout.

Tickets привязаны к sid. Свежая проверка родителя нужна при выдаче,
handshake/admission и send. Manager группирует connections по sid и закрывает
их после logout в текущем процессе. Немедленный active close ограничен одним
worker; межпроцессный fanout не реализован.

## Координация вкладок

`browserSessionCoordinator` использует Web Lock `geoservice.auth.cookie.v1`.
Ожидание lock и auth HTTP ограничены отдельными 30000 ms; принудительный захват
lock запрещён. Web Locks обязателен для auth HTTP. Durable marker
`geoservice.auth.session.v1` содержит только version/revision/sessionId/state;
BroadcastChannel и storage events лишь сигнализируют перечитать marker.
Отсутствие BroadcastChannel допускается, отсутствие координации — явная ошибка.

`auth.ts` держит access/user/sid в памяти. Новый sid того же actor меняет epoch
и приостанавливает прежний workspace; refresh прежнего sid сохраняет его.
`restoreGeneration` ограждает поздние локальные continuations, revision/expected
sid — межвкладочное намерение. Полностью запретить поздний browser Set-Cookie
этими fences нельзя: потеря credential допускает повторный явный login.

`browserSessionMonitor` выполняет независимый status с timeout 1500 ms и паузой
1000 ms. Общий transport вкладки держит один HTTP и один заменяемый pending
context. Resume требует HTTP, начатый после события свежести; pre-resume active
из другого caller нельзя использовать для допуска защищённого действия.
Matching ended очищает UI до ожидания auth lock на marker publication.

`auth.logout(): Promise<boolean>` подтверждает именно исходный sid. До
подтверждения workspace сохраняется. Failure до вызова logout HTTP достоверно
недоставлен; после dispatch network/timeout требует status reconciliation, без
автоматического повторного logout. Поздний true старого sid не очищает новый.
Обычный рабочий 401 очищает локальный доступ и не публикует общий ended.

`prepareActorLogout` ожидает durable inserts/results и проверяет сохранность sent
identity без преждевременного suspension. Managed logout временно блокирует
новые локальные действия инициатора. External ended немедленно приостанавливает
workspace без dirty autosave; frozen payload/CommandId остаются в IndexedDB с
access barrier. Новый login не повторяет mutation автоматически.

## Выпуск и источники

Миграция `e9f1a2b3c4d5` завершает legacy credentials/tickets и создаёт отозванные
родительские rows для их истории. Старые JWT без sid не принимаются. Нужны
однократный повторный login и совместное обновление frontend/backend без mixed
rolling auth. Бизнес-данные и история команд сохраняются.

Проверяемые источники: `AuthSessionService`, `AuthSessionAccessService`,
`BrowserAuthSessionRepository`, `web_api/api/auth.py`, `web_api/api/ws_layers.py`,
`RealtimeConnectionManager`, frontend `src/auth/`, `src/stores/auth.ts`,
`src/api/auth.ts`, `src/stores/workOrders.ts`, `src/stores/workspaceRecovery.ts`.
Операционные команды и границы — [runbook AR-01](../../docs/sprint_2/2026-10-27-ar-01-browser-session-runbook.md).

## Конфликт с прежним описанием

На момент ingest прежние [[api_and_realtime]], [[backend]] и [[frontend]]
описывают logout без sid, удаление cookie и отсутствие межвкладочной
координации. Эти технические утверждения противоречат приведённым исходникам.
Нужна отдельная регистрация follow-up и post-ingest correction; доменную модель
и исторические решения по WorkOrder автоматически не менять.

После ingest зарегистрирован `FU-2026-10-28-001` в
[[Vision_wiki/decisions/followups/index]]. Отдельная post-ingest correction
2026-10-28 обновила только противоречащие auth-факты трёх технических нод.
Датированные записи реестра и доменная модель сохранены.

Связи: [[api_and_realtime]], [[backend]], [[frontend]], [[frontend_save_recovery]].
