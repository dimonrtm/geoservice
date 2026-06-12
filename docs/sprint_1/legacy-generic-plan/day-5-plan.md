# День 5: frontend login flow и auth-state

## Цель дня

- Внедрить рабочий frontend login flow для `email + password`.
- Показывать login-экран, если у пользователя нет токена.
- Хранить токен и объект пользователя в auth-store в форме, согласованной с backend-контрактами Sprint 1.
- Удалить frontend dev-login path и перевести приложение на normal login как единственный пользовательский сценарий входа.
- Подготовить frontend к следующему этапу realtime, не меняя ещё WebSocket-логику.

## Результат дня

- Приложение не пускает пользователя сразу на карту без авторизации.
- Вместо dev-only сценария появляется обычный login screen с `email` и `password`.
- После успешного `POST /api/v1/auth/login` frontend сохраняет:
  - `access_token`
  - `user { id, email, role }`
- При перезагрузке приложения frontend умеет восстанавливать сессию через `GET /api/v1/auth/me`.
- Login screen полностью заменяет карту для неавторизованного пользователя.
- В основном UI есть явный `Logout`.
- Frontend больше не зависит от `dev-login`.

## Входная база Day 5

- Day 3 уже дал рабочие backend endpoint’ы:
  - `POST /api/v1/auth/login`
  - `GET /api/v1/auth/me`
- Day 4 уже сделал demo users и воспроизводимый backend login через Docker Compose.
- Во frontend уже есть:
  - [api/auth.ts](/C:/Repositories/geoservice/apps/frontend/src/api/auth.ts) с dev-only auth helper, который теперь можно убрать
  - [stores/auth.ts](/C:/Repositories/geoservice/apps/frontend/src/stores/auth.ts) с хранением токена, email и role
  - [App.vue](/C:/Repositories/geoservice/apps/frontend/src/App.vue), где карта сейчас рендерится как основной экран
  - [config/app.ts](/C:/Repositories/geoservice/apps/frontend/src/config/app.ts) с dev-auth флагом, который больше не нужен для Day 5 login flow
  - [api/http.ts](/C:/Repositories/geoservice/apps/frontend/src/api/http.ts) с Bearer interceptor и logout на `401`

## Ключевое решение

- Day 5 не переделывает весь frontend под новую архитектуру, а аккуратно внедряет login flow в текущую структуру приложения.
- Основа входа:
  - login form вызывает `POST /api/v1/auth/login`
  - auth-store хранит полный auth-state
  - приложение решает, что показывать, на основании auth-state
- Frontend dev-login path и dev-auth panel убираются, чтобы не поддерживать параллельно второй пользовательский сценарий входа.

## Задачи

1. Обновить frontend auth API под normal login:
   - добавить вызов `POST /api/v1/auth/login`
   - добавить вызов `GET /api/v1/auth/me`
   - удалить `devLogin(...)` и связанные frontend helper’ы
2. Нормализовать auth-store:
   - хранить `token`
   - хранить целиком `user`
   - иметь явные действия `setAuth(...)`, `setUser(...)`, `logout()`
3. Добавить признак готовности auth-state:
   - чтобы приложение понимало, когда завершена первичная попытка восстановления сессии
4. Реализовать frontend login screen:
   - поле `email`
   - поле `password`
   - кнопка входа
   - минимальное отображение ошибки `401`
5. Встроить guard на уровне root UI:
   - если auth ещё инициализируется, показывать промежуточное состояние
   - если токена нет или `/me` не прошёл, показывать login screen
   - если сессия валидна, показывать карту
6. Подключить восстановление сессии:
   - если токен есть в localStorage, при старте вызвать `GET /api/v1/auth/me`
   - если `/me` успешен, восстановить `user`
   - если `/me` вернул `401`, очистить auth-state
   - если `/me` упал по сети или `5xx`, показать временную ошибку и не стирать токен автоматически
7. Добавить явную кнопку `Logout` в авторизованный UI.
8. Удалить frontend dev-auth panel и связанный сценарий из root UI.
9. Обновить UI-связку с картой так, чтобы `MapPageView` показывался только после успешной авторизации.
10. Обновить docs/sprint-заметки, если понадобится уточнить frontend-последовательность login recovery.

## Решение по реализации

### API слой

- В [api/auth.ts](/C:/Repositories/geoservice/apps/frontend/src/api/auth.ts):
  - добавить `login(email, password)`
  - добавить `fetchMe()`
  - удалить `devLogin(...)` и фронтовые вызовы `POST /api/v1/auth/dev-login`
- Сигнатуры должны соответствовать backend-контракту Sprint 1:
  - login response:
    - `access_token`
    - `token_type`
    - `user { id, email, role }`
  - me response:
    - `user { id, email, role }`

### Auth store

- В [stores/auth.ts](/C:/Repositories/geoservice/apps/frontend/src/stores/auth.ts):
  - уйти от хранения только `email` и `role`
  - хранить полноценный `user` как единый объект
  - добавить `isReady` или эквивалентный флаг завершённой инициализации
  - добавить action для восстановления сессии при старте
- Local storage должен содержать:
  - `access_token`
  - сериализованный `user` или эквивалентный набор полей, но в store пользователь должен жить как единый объект

### Root UI

- В [App.vue](/C:/Repositories/geoservice/apps/frontend/src/App.vue):
  - перестать всегда показывать карту
  - переключать UI между:
    - loading state
    - login screen
    - map screen
  - добавить `Logout` в авторизованный сценарий
- Login screen должен полностью заменять карту для неавторизованного пользователя.

### Login screen

- Создать отдельный компонент логина, а не встраивать форму прямо в `App.vue`.
- Форма должна быть минимальной, но рабочей:
  - `email`
  - `password`
  - submit
  - error message
- Day 5 не требует сложного дизайна, recovery flow, registration, password reset или расширенного UX.

## Ограничения дня

- Без realtime и WebSocket.
- Без frontend-реакции на realtime-события.
- Без create-flow новой feature.
- Без расширения frontend editing на все geometry types.
- Без полного frontend-рефактора под `features/shared/map/api/auth`.
- Без refresh token, cookies и SSO.
- Без сохранения frontend dev-login как альтернативного пользовательского сценария.

## Проверки

### Login flow checks

- Пользователь без токена видит login screen, а не карту.
- `POST /api/v1/auth/login` успешен для demo credentials.
- После успешного login карта становится доступной без ручного refresh.
- Ошибка `401 Invalid email or password` отображается пользователю в понятной форме.

### Session recovery checks

- Если в localStorage лежит валидный токен, приложение при старте вызывает `/api/v1/auth/me`.
- При успешном `/me` пользователь сразу попадает на карту.
- При `401` на `/me` auth-state очищается и показывается login screen.
- При сетевой ошибке или `5xx` на `/me` приложение показывает временную ошибку и не стирает токен автоматически.

### Auth UI checks

- Frontend dev-auth panel больше не отображается как часть основного сценария.
- Frontend не зависит от `POST /api/v1/auth/dev-login`.
- В авторизованном интерфейсе есть рабочий `Logout`.

### UI checks

- `MapPageView` не рендерится как основной экран для неавторизованного пользователя.
- После logout приложение возвращается на login screen.
- Existing Axios interceptor на `401` остаётся совместим с новым auth-store.

## Demo-сценарий дня

1. Запустить frontend и backend в dev-режиме.
2. Открыть приложение без токена в localStorage.
3. Убедиться, что вместо карты показывается login screen.
4. Ввести `editor@example.com / editor-password`.
5. Получить успешный login и переход к карте.
6. Перезагрузить страницу.
7. Убедиться, что сессия восстанавливается через `GET /api/v1/auth/me`.
8. Выполнить logout.
9. Убедиться, что приложение снова показывает login screen.

## Definition of Done для Дня 5

- Frontend умеет входить через `POST /api/v1/auth/login`.
- Frontend умеет восстанавливать сессию через `GET /api/v1/auth/me`.
- Карта недоступна как основной экран до успешной авторизации.
- Auth-store хранит token и нормализованный объект `user` как единое значение.
- В UI есть явный `Logout`.
- Frontend dev-login path удалён и не подменяет собой normal login flow.
- Сетевые ошибки `/me` не разлогинивают пользователя автоматически.
- Day 5 не добавляет realtime-логику и не захватывает задачи следующих дней.

## Assumptions

- План дня 5 должен продолжать стиль `day-1-plan.md` ... `day-4-plan.md`.
- Для Sprint 1 достаточно одного простого login screen без регистрации и восстановления пароля.
- Auth-state можно продолжать хранить в localStorage, так как это уже используется текущим frontend.
- Day 5 должен опираться на текущую frontend-структуру, а не требовать отдельного архитектурного рефактора перед началом реализации.
- Backend `POST /api/v1/auth/dev-login` может временно оставаться в API, но Day 5 не должен использовать его на frontend.
